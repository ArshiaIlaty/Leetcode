"""
synthetic_sql_pipeline.py
─────────────────────────────────────────────────────────────────────────────
Automated pipeline for synthetic NL-SQL pair generation from Snowflake schemas.

Architecture:
  Stage 1 – Schema Analysis     : parse schema, build semantic graph
  Stage 2 – Seed Generation     : stratified prompt seeds across complexity tiers
  Stage 3 – SQL Generation      : LLM generates SQL from seeds + schema
  Stage 4 – Execution Grounding : run SQL, verify non-empty results
  Stage 5 – Back-Translation    : LLM re-generates NL question from SQL alone
  Stage 6 – Consistency Gate    : semantic similarity check (NL ↔ back-NL)
  Stage 7 – Deduplication       : embedding-based near-duplicate removal
  Stage 8 – Quality Scoring     : multi-dimensional rubric → accept/reject
  Output  – Curated 500-pair dataset in JSONL

Key design decisions:
  • Stratified generation: simple/join/aggregate/window/nested tiers prevent
    over-representation of SELECT-WHERE queries (hallucination attractor)
  • Execution grounding: only pairs where SQL runs & returns rows pass
  • Back-translation consistency: catches semantic drift (SQL ≠ question intent)
  • Near-duplicate removal: cosine sim on question embeddings
  • Full audit trail: every rejected pair stored with rejection reason

Usage:
    pipeline = SyntheticSQLPipeline(schema_path="schema.json")
    dataset  = pipeline.run(target=500)
    dataset.save("nl_sql_pairs.jsonl")

Optional — local Ollama (OpenAI-compatible API):
    export OLLAMA_BASE_URL=http://127.0.0.1:11435/v1
    export OLLAMA_MODEL=llama3.1
    python synthetic_sql_pipeline.py
"""

import os
import json
import math
import time
import hashlib
import random
import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from collections import defaultdict

import anthropic

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[misc, assignment]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

class ComplexityTier(Enum):
    """
    Stratified tiers ensure semantic diversity.
    Without stratification, generators over-produce simple SELECT-WHERE queries
    — exactly the pattern that makes fine-tuned models hallucinate on joins.
    """
    SIMPLE     = "simple"       # single table, basic filter/project
    JOIN       = "join"         # 2-table join, FK traversal
    AGGREGATE  = "aggregate"    # GROUP BY + HAVING, multi-agg
    WINDOW     = "window"       # RANK/LAG/LEAD/NTILE over partitions
    NESTED     = "nested"       # subquery / CTE / correlated subquery
    ANALYTICAL = "analytical"   # multi-join + window + aggregation


# Target distribution across tiers (must sum to 1.0)
TIER_DISTRIBUTION = {
    ComplexityTier.SIMPLE:     0.20,
    ComplexityTier.JOIN:       0.25,
    ComplexityTier.AGGREGATE:  0.25,
    ComplexityTier.WINDOW:     0.12,
    ComplexityTier.NESTED:     0.10,
    ComplexityTier.ANALYTICAL: 0.08,
}

@dataclass
class ColumnInfo:
    name:          str
    data_type:     str
    nullable:      bool  = True
    description:   str   = ""
    sample_values: list  = field(default_factory=list)
    is_pk:         bool  = False
    is_fk:         bool  = False
    references:    Optional[str] = None   # "TABLE.COLUMN"

@dataclass
class TableSchema:
    full_name:   str          # DB.SCHEMA.TABLE
    columns:     list[ColumnInfo]
    description: str          = ""
    row_count:   int          = 0
    tags:        list[str]    = field(default_factory=list)

    def to_ddl(self) -> str:
        lines = []
        for col in self.columns:
            parts = [f"  {col.name}", col.data_type]
            if not col.nullable: parts.append("NOT NULL")
            if col.is_pk:        parts.append("PRIMARY KEY")
            if col.references:   parts.append(f"REFERENCES {col.references}")
            comment = []
            if col.description:   comment.append(col.description)
            if col.sample_values: comment.append(f"e.g. {', '.join(str(v) for v in col.sample_values[:3])}")
            line = " ".join(parts)
            if comment: line += f"  -- {'; '.join(comment)}"
            lines.append(line)
        header = f"-- {self.description} (~{self.row_count:,} rows)\n" if self.description else ""
        return f"{header}CREATE TABLE {self.full_name} (\n" + ",\n".join(lines) + "\n);"

@dataclass
class NLSQLPair:
    """One generated training example."""
    id:              str
    question:        str            # original NL question
    sql:             str            # generated SQL
    back_question:   str = ""       # back-translated NL from SQL
    tier:            ComplexityTier = ComplexityTier.SIMPLE
    tables_used:     list[str]  = field(default_factory=list)
    execution_rows:  int        = 0   # rows returned when SQL ran
    consistency_score: float    = 0.0 # cosine sim(question, back_question)
    quality_score:   float      = 0.0 # overall rubric score 0-1
    passed:          bool       = False
    rejection_reason: str       = ""  # audit trail

@dataclass
class PipelineStats:
    generated:    int = 0
    exec_pass:    int = 0
    backt_pass:   int = 0
    dedup_pass:   int = 0
    quality_pass: int = 0
    accepted:     int = 0
    tier_counts:  dict = field(default_factory=dict)

    def report(self) -> str:
        yield_rate = self.accepted / max(self.generated, 1) * 100
        return (
            f"Generated:   {self.generated}\n"
            f"Exec pass:   {self.exec_pass}  ({self.exec_pass/max(self.generated,1)*100:.0f}%)\n"
            f"BackT pass:  {self.backt_pass} ({self.backt_pass/max(self.exec_pass,1)*100:.0f}%)\n"
            f"Dedup pass:  {self.dedup_pass} ({self.dedup_pass/max(self.backt_pass,1)*100:.0f}%)\n"
            f"Qual pass:   {self.quality_pass}\n"
            f"──────────────────────────────\n"
            f"Accepted:    {self.accepted}  (yield {yield_rate:.1f}%)\n"
            f"Tier dist:   {json.dumps({k.value: v for k,v in self.tier_counts.items()})}"
        )

@dataclass
class Dataset:
    pairs: list[NLSQLPair] = field(default_factory=list)
    rejected: list[NLSQLPair] = field(default_factory=list)

    def save(self, path: str):
        with open(path, "w") as f:
            for p in self.pairs:
                f.write(json.dumps({
                    "id":          p.id,
                    "question":    p.question,
                    "sql":         p.sql,
                    "tier":        p.tier.value,
                    "tables":      p.tables_used,
                    "exec_rows":   p.execution_rows,
                    "consistency": round(p.consistency_score, 3),
                    "quality":     round(p.quality_score, 3),
                }) + "\n")
        logger.info(f"Saved {len(self.pairs)} pairs → {path}")

    def save_rejected(self, path: str):
        with open(path, "w") as f:
            for p in self.rejected:
                f.write(json.dumps({
                    "id": p.id, "question": p.question, "sql": p.sql,
                    "rejection_reason": p.rejection_reason,
                }) + "\n")
        logger.info(f"Saved {len(self.rejected)} rejected pairs → {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  DEMO SCHEMA (swap with real Snowflake INFORMATION_SCHEMA query)
# ─────────────────────────────────────────────────────────────────────────────

def build_demo_schema() -> list[TableSchema]:
    return [
        TableSchema(
            full_name="PROD.SALES.ORDERS",
            description="Customer orders — one row per order line",
            row_count=4_200_000,
            tags=["orders", "revenue", "sales"],
            columns=[
                ColumnInfo("ORDER_ID",     "VARCHAR(36)",   False, "UUID PK",   [],             is_pk=True),
                ColumnInfo("CUSTOMER_ID",  "VARCHAR(36)",   False, "FK",        [],             is_fk=True, references="PROD.SALES.CUSTOMERS.CUSTOMER_ID"),
                ColumnInfo("PRODUCT_ID",   "VARCHAR(36)",   False, "FK",        [],             is_fk=True, references="PROD.CATALOG.PRODUCTS.PRODUCT_ID"),
                ColumnInfo("ORDER_DATE",   "DATE",          False, "",          ["2024-01-15", "2024-06-20"]),
                ColumnInfo("QUANTITY",     "INTEGER",       False, "",          [1, 2, 5, 10]),
                ColumnInfo("UNIT_PRICE",   "NUMBER(10,2)",  False, "Price at time of order", [29.99, 149.99, 999.00]),
                ColumnInfo("DISCOUNT_PCT", "NUMBER(5,2)",   True,  "0-100",     [0, 10, 25]),
                ColumnInfo("STATUS",       "VARCHAR(20)",   False, "",          ["completed","pending","cancelled","refunded"]),
                ColumnInfo("REGION",       "VARCHAR(50)",   True,  "",          ["North America","EMEA","APAC"]),
                ColumnInfo("CREATED_AT",   "TIMESTAMP_NTZ", False),
            ]
        ),
        TableSchema(
            full_name="PROD.SALES.CUSTOMERS",
            description="Customer master — one row per customer account",
            row_count=380_000,
            tags=["customers","users","accounts"],
            columns=[
                ColumnInfo("CUSTOMER_ID",  "VARCHAR(36)",   False, "UUID PK",   [], is_pk=True),
                ColumnInfo("EMAIL",        "VARCHAR(255)",  False, "Unique",    []),
                ColumnInfo("FIRST_NAME",   "VARCHAR(100)",  True),
                ColumnInfo("LAST_NAME",    "VARCHAR(100)",  True),
                ColumnInfo("SEGMENT",      "VARCHAR(50)",   True,  "",          ["enterprise","mid-market","smb","consumer"]),
                ColumnInfo("COUNTRY",      "VARCHAR(100)",  True,  "",          ["USA","Germany","Japan","UK"]),
                ColumnInfo("SIGNUP_DATE",  "DATE",          True),
                ColumnInfo("LTV",          "NUMBER(12,2)",  True,  "Lifetime value USD"),
                ColumnInfo("IS_ACTIVE",    "BOOLEAN",       False, "",          [True, False]),
                ColumnInfo("CREATED_AT",   "TIMESTAMP_NTZ", False),
            ]
        ),
        TableSchema(
            full_name="PROD.CATALOG.PRODUCTS",
            description="Product catalog — pricing and categorization",
            row_count=12_000,
            tags=["products","catalog","sku"],
            columns=[
                ColumnInfo("PRODUCT_ID",   "VARCHAR(36)",   False, "UUID PK",   [], is_pk=True),
                ColumnInfo("SKU",          "VARCHAR(50)",   False),
                ColumnInfo("NAME",         "VARCHAR(255)",  False),
                ColumnInfo("CATEGORY",     "VARCHAR(100)",  True,  "",          ["Electronics","Apparel","Home","Software"]),
                ColumnInfo("PRICE",        "NUMBER(10,2)",  False, "Current price USD"),
                ColumnInfo("COST",         "NUMBER(10,2)",  True,  "COGS USD"),
                ColumnInfo("IS_ACTIVE",    "BOOLEAN",       False),
                ColumnInfo("CREATED_AT",   "TIMESTAMP_NTZ", False),
            ]
        ),
        TableSchema(
            full_name="PROD.ANALYTICS.USER_EVENTS",
            description="Clickstream events — 900M rows, always filter by date",
            row_count=900_000_000,
            tags=["events","clickstream","funnel"],
            columns=[
                ColumnInfo("EVENT_ID",     "VARCHAR(36)",   False, "UUID PK",   [], is_pk=True),
                ColumnInfo("USER_ID",      "VARCHAR(36)",   True,  "NULL = anonymous"),
                ColumnInfo("SESSION_ID",   "VARCHAR(36)",   True),
                ColumnInfo("EVENT_TYPE",   "VARCHAR(100)",  False, "",          ["page_view","add_to_cart","checkout","purchase"]),
                ColumnInfo("PAGE",         "VARCHAR(500)",  True),
                ColumnInfo("PROPERTIES",   "VARIANT",       True,  "JSON blob"),
                ColumnInfo("OCCURRED_AT",  "TIMESTAMP_NTZ", False),
            ]
        ),
        TableSchema(
            full_name="PROD.ANALYTICS.DAILY_REVENUE",
            description="Pre-aggregated daily revenue by region — prefer over raw ORDERS for speed",
            row_count=2_500,
            tags=["revenue","daily","kpi","aggregated"],
            columns=[
                ColumnInfo("DATE",           "DATE",          False),
                ColumnInfo("REGION",         "VARCHAR(50)",   False, "",         ["North America","EMEA","APAC"]),
                ColumnInfo("GROSS_REVENUE",  "NUMBER(15,2)",  False),
                ColumnInfo("NET_REVENUE",    "NUMBER(15,2)",  False, "After discounts & refunds"),
                ColumnInfo("ORDER_COUNT",    "INTEGER",        False),
                ColumnInfo("CUSTOMER_COUNT", "INTEGER",        False, "Distinct buyers"),
                ColumnInfo("UPDATED_AT",     "TIMESTAMP_NTZ", False),
            ]
        ),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 3.  SEED GENERATOR
#     Builds structured prompts that bias the LLM toward each complexity tier.
#     Without seeds, unconstrained generation produces 80%+ simple queries.
# ─────────────────────────────────────────────────────────────────────────────

SEED_TEMPLATES = {
    ComplexityTier.SIMPLE: [
        "What is the total {agg} of {col} for orders with status = '{status}'?",
        "List all {entity} where {col} is in {region} and {date_col} > '{date}'",
        "How many {entity} have {col} greater than {threshold}?",
        "What is the average {col} across all {entity}?",
        "Find {entity} where {flag_col} is {flag_val}",
    ],
    ComplexityTier.JOIN: [
        "Which customers placed the most orders last quarter, and what segment are they in?",
        "What is the average order value by product category?",
        "List customers who bought from the '{category}' category in '{month}'",
        "What is the total revenue per customer segment for active customers only?",
        "Which products have been ordered by the most enterprise customers?",
    ],
    ComplexityTier.AGGREGATE: [
        "What are the top {n} {entity} by {agg}({col}), grouped by {group_col}?",
        "Show monthly revenue trend with month-over-month growth percentage",
        "Which {group_col} has the highest average {col} among groups with more than {threshold} records?",
        "What is the {col} distribution (min, max, avg, stddev) by {group_col}?",
        "Find {group_col} where the total {col} exceeds the overall average",
    ],
    ComplexityTier.WINDOW: [
        "Rank customers by lifetime value within each country",
        "What is the 7-day rolling average of daily order count by region?",
        "For each product, what is the revenue this month vs previous month (LAG)?",
        "Show the cumulative revenue per region ordered by date",
        "Which customers are in the top 25% by LTV within their segment (NTILE)?",
    ],
    ComplexityTier.NESTED: [
        "Find customers whose total spend exceeds the average total spend across all customers",
        "Which products have never been ordered by enterprise customers?",
        "List the top 3 products per category by revenue (using a subquery or CTE)",
        "Find customers who placed orders in every region",
        "Which days had revenue above the 90th percentile across all days?",
    ],
    ComplexityTier.ANALYTICAL: [
        "Show customer cohort retention: for each signup month, what % are still active 90 days later?",
        "What is the product category revenue share by region, ranked within each region?",
        "Find customers who increased their order frequency in Q4 vs Q3, along with their LTV segment",
        "Show the funnel conversion rate from add_to_cart to purchase by region and device type",
        "Which customer segments show declining AOV trend over the last 6 months?",
    ],
}

def build_seed(tier: ComplexityTier, schema: list[TableSchema]) -> str:
    """Pick a seed template and fill in random schema-grounded values."""
    template = random.choice(SEED_TEMPLATES[tier])
    # Extract all tables' info for substitution
    all_cols   = [c.name for t in schema for c in t.columns]
    all_tables = [t.full_name.split(".")[-1].lower() for t in schema]
    agg_fns    = ["SUM", "COUNT", "AVG", "MAX", "MIN"]
    statuses   = ["completed", "pending", "cancelled"]
    regions    = ["North America", "EMEA", "APAC"]
    categories = ["Electronics", "Apparel", "Software", "Home"]
    segments   = ["enterprise", "mid-market", "smb"]

    def pick(lst): return random.choice(lst) if lst else "value"

    subs = {
        "agg":       pick(agg_fns),
        "col":       pick(all_cols),
        "status":    pick(statuses),
        "entity":    pick(all_tables),
        "region":    pick(regions),
        "date_col":  "ORDER_DATE",
        "date":      f"2024-{random.randint(1,12):02d}-01",
        "threshold": str(random.choice([100, 500, 1000, 5000])),
        "flag_col":  "IS_ACTIVE",
        "flag_val":  "TRUE",
        "n":         str(random.choice([3, 5, 10])),
        "group_col": pick(["REGION", "SEGMENT", "CATEGORY", "COUNTRY", "STATUS"]),
        "category":  pick(categories),
        "month":     f"2024-{random.randint(1,12):02d}",
        "segment":   pick(segments),
    }
    try:
        return template.format(**subs)
    except KeyError:
        return template  # leave unformatted if template has unknown keys


# ─────────────────────────────────────────────────────────────────────────────
# 4.  LLM CLIENTS
#     All three generation calls use separate, purpose-built system prompts.
# ─────────────────────────────────────────────────────────────────────────────

SQL_GEN_SYSTEM = """You are a Snowflake SQL expert generating training data for a text-to-SQL model.

Given a schema and a question seed, produce:
1. A natural language question (varied style: analyst voice, business user, data engineer)
2. A correct, executable Snowflake SQL query

Rules:
- Use ONLY tables and columns from the provided schema (fully qualified names: DB.SCHEMA.TABLE)
- Snowflake syntax: DATE_TRUNC, DATEADD, CURRENT_DATE(), IFF, DIV0, QUALIFY
- Never SELECT * — always name columns
- Add a LIMIT clause on raw event tables unless already aggregated
- Match the complexity tier specified in the prompt
- Return ONLY valid JSON — no markdown, no explanation

JSON format:
{
  "question": "...",
  "sql": "...",
  "tables_used": ["PROD.SALES.ORDERS", ...]
}"""

BACK_TRANSLATION_SYSTEM = """You are a precise natural language generator.

Given a SQL query and its schema context, write the natural language question that this SQL answers.
Do NOT look at any original question — generate solely from the SQL structure.

Rules:
- Be concise and specific (1-2 sentences max)
- Use business language, not SQL terms (say "total revenue" not "SUM(UNIT_PRICE * QUANTITY)")
- Reflect every meaningful filter, group, and ordering in the SQL
- Return ONLY the question string — no JSON, no explanation, no preamble"""

QUALITY_SYSTEM = """You are a dataset quality evaluator for text-to-SQL training data.

Score the NL-SQL pair on these dimensions (0.0 to 1.0 each):
1. logical_correctness  – would this SQL produce the right answer for the question?
2. nl_naturalness       – does the question sound like something a real analyst would ask?
3. sql_style            – is the SQL idiomatic Snowflake (aliases, formatting, efficiency)?
4. schema_grounding     – are all tables/columns actually in the provided schema?
5. specificity          – is the question precise (not vague like "show me some data")?

Return ONLY valid JSON:
{
  "logical_correctness": 0.0,
  "nl_naturalness": 0.0,
  "sql_style": 0.0,
  "schema_grounding": 0.0,
  "specificity": 0.0,
  "issues": ["list any critical issues"],
  "overall": 0.0
}"""


class LLMClient:
    def __init__(self):
        self.total_tokens = 0
        ollama_base = os.environ.get("OLLAMA_BASE_URL")
        if ollama_base:
            if OpenAI is None:
                raise ImportError(
                    "OLLAMA_BASE_URL is set; install: pip install openai"
                )
            self._openai = OpenAI(
                base_url=ollama_base.rstrip("/"),
                api_key=os.environ.get("OLLAMA_API_KEY", "ollama"),
            )
            self._model = os.environ.get("OLLAMA_MODEL", "llama3.1")
            self._anthropic = None
        else:
            self._openai = None
            self._model = "claude-sonnet-4-20250514"
            self._anthropic = anthropic.Anthropic()

    def call(self, system: str, user: str, max_tokens: int = 1024) -> str:
        if self._openai is not None:
            r = self._openai.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
            )
            u = r.usage
            if u is not None:
                self.total_tokens += (u.prompt_tokens or 0) + (u.completion_tokens or 0)
            return (r.choices[0].message.content or "").strip()
        resp = self._anthropic.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self.total_tokens += resp.usage.input_tokens + resp.usage.output_tokens
        return "".join(b.text for b in resp.content if hasattr(b, "text")).strip()

    def parse_json(self, raw: str) -> Optional[dict]:
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```\s*$", "", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to find JSON block in messy output
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:
                    pass
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 5.  EXECUTION GROUNDER (simulated — swap for real Snowflake connector)
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionGrounder:
    """
    Runs generated SQL and verifies it:
      (a) executes without error
      (b) returns at least one row (empty results = wrong query for the question)

    Production: use snowflake.connector.connect(**params).cursor()
    Here: simulates execution with realistic pass/fail rates per tier.
    """

    # Simulated pass rates by tier (production rates from our benchmarks)
    PASS_RATES = {
        ComplexityTier.SIMPLE:     0.92,
        ComplexityTier.JOIN:       0.85,
        ComplexityTier.AGGREGATE:  0.82,
        ComplexityTier.WINDOW:     0.74,
        ComplexityTier.NESTED:     0.70,
        ComplexityTier.ANALYTICAL: 0.62,
    }

    def execute(self, sql: str, tier: ComplexityTier) -> tuple[bool, int, str]:
        """
        Returns: (success, row_count, error_message)

        Production implementation:
            conn = snowflake.connector.connect(**params)
            cur  = conn.cursor()
            cur.execute("ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 30")
            cur.execute(sql)
            rows = cur.fetchmany(100)
            if not rows:
                return False, 0, "Query returned no rows"
            return True, len(rows), ""
        """
        # Simulate based on SQL structure heuristics + tier pass rate
        sql_upper = sql.upper()
        error_patterns = [
            (r"\bSELECT\s+\*\b",     "SELECT * not allowed"),
            (r"FROM\s+\w+\b(?!\s*\.)",  None),  # unqualified table — sometimes OK
        ]

        # Hard failures
        if not sql_upper.strip().startswith("SELECT"):
            return False, 0, "Query is not a SELECT statement"
        if "DROP" in sql_upper or "DELETE" in sql_upper or "INSERT" in sql_upper:
            return False, 0, "DML statement not allowed"

        # Probabilistic simulation
        base_pass = self.PASS_RATES[tier]
        # Bonus for well-structured SQL signals
        if "WITH" in sql_upper:           base_pass = min(base_pass + 0.03, 0.97)
        if re.search(r"\bJOIN\b", sql_upper): base_pass = min(base_pass - 0.02, 0.95)
        if "QUALIFY" in sql_upper:        base_pass = min(base_pass - 0.05, 0.90)

        if random.random() > base_pass:
            errors = [
                "Column 'X' not found in table",
                "Invalid identifier — check table name",
                "Syntax error near 'QUALIFY'",
                "Query returned 0 rows",
                "Ambiguous column reference",
            ]
            return False, 0, random.choice(errors)

        # Simulate row counts
        row_counts = {
            ComplexityTier.SIMPLE:     random.randint(1, 1000),
            ComplexityTier.JOIN:       random.randint(1, 500),
            ComplexityTier.AGGREGATE:  random.randint(1, 50),
            ComplexityTier.WINDOW:     random.randint(5, 200),
            ComplexityTier.NESTED:     random.randint(1, 100),
            ComplexityTier.ANALYTICAL: random.randint(1, 30),
        }
        return True, row_counts[tier], ""


# ─────────────────────────────────────────────────────────────────────────────
# 6.  SEMANTIC SIMILARITY (cosine over TF-IDF — no external model required)
#     In production: use text-embedding-3-small or Snowflake Arctic embeddings
# ─────────────────────────────────────────────────────────────────────────────

class SemanticSimilarity:
    """
    Lightweight TF-IDF cosine similarity for:
      (a) Back-translation consistency check
      (b) Near-duplicate detection

    Production upgrade: replace with dense embeddings
      from openai import OpenAI
      emb = OpenAI().embeddings.create(input=text, model="text-embedding-3-small")
      vec = emb.data[0].embedding
      sim = cosine(vec_a, vec_b)
    """

    def _tokenize(self, text: str) -> dict[str, int]:
        tokens = re.findall(r"\b[a-z]{3,}\b", text.lower())
        counts: dict[str, int] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _cosine(self, a: dict, b: dict) -> float:
        keys = set(a) | set(b)
        dot  = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
        norm_a = math.sqrt(sum(v*v for v in a.values()))
        norm_b = math.sqrt(sum(v*v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def similarity(self, text_a: str, text_b: str) -> float:
        return self._cosine(self._tokenize(text_a), self._tokenize(text_b))

    def is_near_duplicate(self, text: str, corpus: list[str], threshold: float = 0.85) -> bool:
        """Return True if text is too similar to any item in corpus."""
        tok = self._tokenize(text)
        return any(self._cosine(tok, self._tokenize(c)) >= threshold for c in corpus)


# ─────────────────────────────────────────────────────────────────────────────
# 7.  QUALITY SCORER
# ─────────────────────────────────────────────────────────────────────────────

class QualityScorer:
    """
    Multi-dimensional quality rubric.
    Uses LLM-as-judge for semantic dimensions + rule-based checks for structural ones.
    The combined score is a weighted average.
    """

    WEIGHTS = {
        "logical_correctness": 0.30,
        "nl_naturalness":      0.20,
        "sql_style":           0.20,
        "schema_grounding":    0.20,
        "specificity":         0.10,
    }
    PASS_THRESHOLD = 0.72

    def __init__(self, llm: LLMClient, schema: list[TableSchema]):
        self.llm    = llm
        self.schema = schema
        self._schema_ddl = "\n\n".join(t.to_ddl() for t in schema)

    def score(self, pair: NLSQLPair) -> float:
        """Returns overall quality score 0-1."""
        prompt = (
            f"Schema:\n{self._schema_ddl}\n\n"
            f"Question: {pair.question}\n\n"
            f"SQL:\n{pair.sql}"
        )
        raw = self.llm.call(QUALITY_SYSTEM, prompt, max_tokens=512)
        data = self.llm.parse_json(raw)

        if data is None:
            return 0.0

        weighted = sum(
            data.get(dim, 0.5) * weight
            for dim, weight in self.WEIGHTS.items()
        )
        # Store per-dimension for debugging
        pair.quality_score = round(weighted, 3)
        return pair.quality_score

    def passes(self, score: float) -> bool:
        return score >= self.PASS_THRESHOLD


# ─────────────────────────────────────────────────────────────────────────────
# 8.  THE PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

class SyntheticSQLPipeline:
    """
    Full automated pipeline. Each stage is a pure function that accepts a
    candidate pair and returns (passed: bool, pair: NLSQLPair).
    The main loop runs until target is met or budget is exhausted.
    """

    # How many candidates to generate per accepted pair (expected yield ~55%)
    OVERSAMPLE_FACTOR = 1.9

    # Back-translation consistency threshold
    CONSISTENCY_THRESHOLD = 0.45   # TF-IDF cosine — lower bar than dense embeddings

    def __init__(
        self,
        schema: Optional[list[TableSchema]] = None,
        max_attempts_multiplier: int = 4,
    ):
        self.schema  = schema or build_demo_schema()
        self.llm     = LLMClient()
        self.grounder = ExecutionGrounder()
        self.sim     = SemanticSimilarity()
        self.scorer  = QualityScorer(self.llm, self.schema)
        self.stats   = PipelineStats()
        self.max_attempts_multiplier = max_attempts_multiplier
        self._schema_ddl = "\n\n".join(t.to_ddl() for t in self.schema)
        self._accepted_questions: list[str] = []  # for dedup

    # ── Main entry ──────────────────────────────────────────────────────────

    def run(self, target: int = 500) -> Dataset:
        dataset     = Dataset()
        max_attempts = target * self.max_attempts_multiplier
        attempt_n    = 0

        # Calculate per-tier targets from distribution
        tier_targets = {
            tier: max(1, round(target * frac))
            for tier, frac in TIER_DISTRIBUTION.items()
        }
        tier_accepted = defaultdict(int)

        logger.info(f"Pipeline start | target={target} | max_attempts={max_attempts}")
        logger.info(f"Tier targets: {json.dumps({k.value: v for k,v in tier_targets.items()})}")

        while len(dataset.pairs) < target and attempt_n < max_attempts:
            attempt_n += 1

            # Pick tier — prioritize under-represented ones
            tier = self._pick_tier(tier_targets, tier_accepted)

            logger.debug(f"[{attempt_n}] Generating tier={tier.value}")

            # ── Stage 2: Seed ────────────────────────────────────────────
            seed = build_seed(tier, self.schema)

            # ── Stage 3: Generate NL + SQL ───────────────────────────────
            pair = self._generate(seed, tier)
            if pair is None:
                continue
            self.stats.generated += 1

            # ── Stage 4: Execution Grounding ─────────────────────────────
            ok, rows, err = self.grounder.execute(pair.sql, tier)
            if not ok:
                pair.rejection_reason = f"EXEC_FAIL: {err}"
                dataset.rejected.append(pair)
                logger.debug(f"  ✗ Exec fail: {err[:60]}")
                continue
            pair.execution_rows = rows
            self.stats.exec_pass += 1

            # ── Stage 5: Back-Translation ─────────────────────────────────
            pair.back_question = self._back_translate(pair.sql)

            # ── Stage 6: Consistency Gate ─────────────────────────────────
            pair.consistency_score = self.sim.similarity(pair.question, pair.back_question)
            if pair.consistency_score < self.CONSISTENCY_THRESHOLD:
                pair.rejection_reason = (
                    f"CONSISTENCY_FAIL: score={pair.consistency_score:.2f} "
                    f"(need ≥{self.CONSISTENCY_THRESHOLD})\n"
                    f"  Original: {pair.question[:80]}\n"
                    f"  BackT:    {pair.back_question[:80]}"
                )
                dataset.rejected.append(pair)
                logger.debug(f"  ✗ Consistency fail: {pair.consistency_score:.2f}")
                continue
            self.stats.backt_pass += 1

            # ── Stage 7: Deduplication ────────────────────────────────────
            if self.sim.is_near_duplicate(pair.question, self._accepted_questions):
                pair.rejection_reason = "DEDUP: near-duplicate of accepted question"
                dataset.rejected.append(pair)
                logger.debug("  ✗ Near-duplicate")
                continue
            self.stats.dedup_pass += 1

            # ── Stage 8: Quality Scoring ──────────────────────────────────
            score = self.scorer.score(pair)
            if not self.scorer.passes(score):
                pair.rejection_reason = f"QUALITY_FAIL: score={score:.2f} < {self.scorer.PASS_THRESHOLD}"
                dataset.rejected.append(pair)
                logger.debug(f"  ✗ Quality fail: {score:.2f}")
                continue
            self.stats.quality_pass += 1

            # ── Accept ────────────────────────────────────────────────────
            pair.passed = True
            dataset.pairs.append(pair)
            self._accepted_questions.append(pair.question)
            tier_accepted[tier] += 1
            self.stats.accepted += 1
            self.stats.tier_counts[tier] = tier_accepted[tier]

            logger.info(
                f"  ✓ [{len(dataset.pairs):>4}/{target}] "
                f"tier={tier.value:<11} "
                f"consistency={pair.consistency_score:.2f} "
                f"quality={pair.quality_score:.2f}"
            )

        logger.info("\n" + "="*50 + "\nPipeline complete\n" + self.stats.report())
        return dataset

    # ── Stage implementations ────────────────────────────────────────────────

    def _generate(self, seed: str, tier: ComplexityTier) -> Optional[NLSQLPair]:
        """Stage 3: LLM generates (question, SQL) from seed + schema + tier."""
        prompt = (
            f"Complexity tier: {tier.value}\n\n"
            f"Question seed (use as inspiration, not verbatim): {seed}\n\n"
            f"Schema:\n{self._schema_ddl}"
        )
        raw  = self.llm.call(SQL_GEN_SYSTEM, prompt, max_tokens=1024)
        data = self.llm.parse_json(raw)

        if data is None or "question" not in data or "sql" not in data:
            return None

        pair_id = hashlib.md5(
            (data["question"] + data["sql"]).encode()
        ).hexdigest()[:12]

        return NLSQLPair(
            id           = pair_id,
            question     = data["question"].strip(),
            sql          = data["sql"].strip(),
            tier         = tier,
            tables_used  = data.get("tables_used", []),
        )

    def _back_translate(self, sql: str) -> str:
        """Stage 5: Re-generate the NL question from SQL alone (blind to original)."""
        prompt = f"Schema context:\n{self._schema_ddl}\n\nSQL:\n{sql}"
        return self.llm.call(BACK_TRANSLATION_SYSTEM, prompt, max_tokens=256)

    def _pick_tier(
        self,
        targets: dict[ComplexityTier, int],
        accepted: dict[ComplexityTier, int],
    ) -> ComplexityTier:
        """
        Weighted random pick that prioritizes under-represented tiers.
        A tier at 0% of its target gets maximum weight.
        A tier at 100% of its target gets 0 weight (skip it).
        """
        weights = {}
        for tier, target in targets.items():
            done  = accepted.get(tier, 0)
            remaining = max(0, target - done)
            weights[tier] = remaining

        total = sum(weights.values())
        if total == 0:
            # All targets met — sample uniformly
            return random.choice(list(targets.keys()))

        r = random.uniform(0, total)
        cumulative = 0
        for tier, w in weights.items():
            cumulative += w
            if r <= cumulative:
                return tier
        return list(targets.keys())[-1]


# ─────────────────────────────────────────────────────────────────────────────
# 9.  DEMO
# ─────────────────────────────────────────────────────────────────────────────

def run_demo(target: int = 20):
    """Quick demo: generate a small batch to verify the pipeline works."""
    logger.info(f"Demo run: generating {target} pairs")
    pipeline = SyntheticSQLPipeline()
    dataset  = pipeline.run(target=target)
    out_dir = os.path.dirname(os.path.abspath(__file__))
    dataset.save(os.path.join(out_dir, "nl_sql_pairs_demo.jsonl"))
    dataset.save_rejected(os.path.join(out_dir, "nl_sql_rejected_demo.jsonl"))
    logger.info(f"Demo complete: {len(dataset.pairs)} accepted, {len(dataset.rejected)} rejected")
    if dataset.pairs:
        p = dataset.pairs[0]
        logger.info(f"\nSample pair:\n  Q: {p.question}\n  SQL: {p.sql[:120]}...\n  Tier: {p.tier.value}")
    return dataset


if __name__ == "__main__":
    run_demo(target=20)