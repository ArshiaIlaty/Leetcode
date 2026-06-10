"""
snowflake_sql_agent.py — Production Text-to-SQL Agent for Snowflake

Architecture:
  1. SchemaRegistry    — loads & caches table schemas, injects relevant ones into prompts
  2. SQLValidator      — pre-flight checks before any query hits Snowflake
  3. SnowflakeExecutor — runs queries, returns structured results
  4. TextToSQLAgent    — orchestrates the ReAct loop with retry logic

Usage:
    agent = TextToSQLAgent(connection_params)
    result = agent.query("What were the top 5 products by revenue last month?")
    print(result.answer)
    print(result.sql)

Optional — local Ollama (OpenAI-compatible API; include /v1 in the URL):
    export OLLAMA_BASE_URL=http://127.0.0.1:11435/v1
    export OLLAMA_MODEL=llama3.1
    python sql_agent.py
"""

import os
import re
import json
import time
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

import anthropic

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[misc, assignment]

# Optional: uncomment when connecting to real Snowflake
# import snowflake.connector

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

class QueryStatus(Enum):
    SUCCESS   = "success"
    ERROR     = "error"
    TIMEOUT   = "timeout"
    FORBIDDEN = "forbidden"    # blocked by safety validator


@dataclass
class ColumnInfo:
    name:        str
    data_type:   str
    nullable:    bool  = True
    description: str   = ""
    sample_values: list = field(default_factory=list)


@dataclass
class TableSchema:
    database:    str
    schema:      str
    table:       str
    columns:     list[ColumnInfo]
    description: str       = ""
    row_count:   int       = 0
    tags:        list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.database}.{self.schema}.{self.table}"

    def to_ddl(self) -> str:
        """Render as CREATE TABLE DDL — the clearest format for LLMs."""
        col_lines = []
        for col in self.columns:
            nullable = "" if col.nullable else " NOT NULL"
            comment  = f"  -- {col.description}" if col.description else ""
            samples  = f" (e.g. {', '.join(str(v) for v in col.sample_values[:3])})" if col.sample_values else ""
            col_lines.append(f"    {col.name} {col.data_type}{nullable}{comment}{samples}")

        header = f"-- {self.description} | ~{self.row_count:,} rows\n" if self.description else ""
        return (
            f"{header}"
            f"CREATE TABLE {self.full_name} (\n"
            + ",\n".join(col_lines)
            + "\n);"
        )


@dataclass
class QueryResult:
    status:    QueryStatus
    sql:       str
    answer:    str
    rows:      list[dict]     = field(default_factory=list)
    row_count: int            = 0
    error:     Optional[str]  = None
    attempts:  int            = 1
    latency_ms: float         = 0.0
    tokens_used: int          = 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. SCHEMA REGISTRY
#    Loads schemas and selects relevant tables for each query.
#    In production: pull from INFORMATION_SCHEMA or a metadata DB.
# ─────────────────────────────────────────────────────────────────────────────

class SchemaRegistry:
    """
    Manages table schemas and selects which ones to inject into each prompt.

    Key insight: injecting ALL schemas every call wastes tokens and confuses
    the LLM. Instead we embed schema names and select top-K by relevance
    to the user's question (keyword match here; use embeddings in production).
    """

    def __init__(self, max_tables_per_prompt: int = 8):
        self.max_tables_per_prompt = max_tables_per_prompt
        self._schemas: dict[str, TableSchema] = {}
        self._load_demo_schemas()

    def _load_demo_schemas(self):
        """Demo schemas — replace with INFORMATION_SCHEMA query in production."""
        schemas = [
            TableSchema(
                database="PROD_DW", schema="SALES", table="ORDERS",
                description="Customer orders, one row per order",
                row_count=4_200_000,
                tags=["orders", "revenue", "sales", "transactions"],
                columns=[
                    ColumnInfo("ORDER_ID",      "VARCHAR(36)",    False, "UUID primary key"),
                    ColumnInfo("CUSTOMER_ID",   "VARCHAR(36)",    False, "FK to CUSTOMERS"),
                    ColumnInfo("ORDER_DATE",    "DATE",           False, "Date order was placed",
                               ["2024-01-15", "2024-03-22"]),
                    ColumnInfo("TOTAL_AMOUNT",  "NUMBER(12,2)",   False, "Order total in USD",
                               [149.99, 2340.00, 89.50]),
                    ColumnInfo("STATUS",        "VARCHAR(20)",    False, "Order lifecycle status",
                               ["completed", "pending", "cancelled", "refunded"]),
                    ColumnInfo("PRODUCT_ID",    "VARCHAR(36)",    False, "FK to PRODUCTS"),
                    ColumnInfo("QUANTITY",      "INTEGER",        False, "Units ordered",
                               [1, 2, 5]),
                    ColumnInfo("REGION",        "VARCHAR(50)",    True,  "Geo region",
                               ["North America", "EMEA", "APAC"]),
                    ColumnInfo("DISCOUNT_PCT",  "NUMBER(5,2)",    True,  "Discount applied 0-100"),
                    ColumnInfo("CREATED_AT",    "TIMESTAMP_NTZ",  False, "Row insert time"),
                ]
            ),
            TableSchema(
                database="PROD_DW", schema="SALES", table="CUSTOMERS",
                description="Customer master table",
                row_count=380_000,
                tags=["customers", "users", "accounts", "clients"],
                columns=[
                    ColumnInfo("CUSTOMER_ID",   "VARCHAR(36)",    False, "UUID primary key"),
                    ColumnInfo("EMAIL",         "VARCHAR(255)",   False, "Unique email address"),
                    ColumnInfo("FIRST_NAME",    "VARCHAR(100)",   True),
                    ColumnInfo("LAST_NAME",     "VARCHAR(100)",   True),
                    ColumnInfo("SEGMENT",       "VARCHAR(50)",    True,  "Customer tier",
                               ["enterprise", "mid-market", "smb", "consumer"]),
                    ColumnInfo("COUNTRY",       "VARCHAR(100)",   True,  "", ["USA", "Germany", "Japan"]),
                    ColumnInfo("SIGNUP_DATE",   "DATE",           True),
                    ColumnInfo("LTV",           "NUMBER(12,2)",   True,  "Lifetime value in USD"),
                    ColumnInfo("IS_ACTIVE",     "BOOLEAN",        False, "", [True, False]),
                    ColumnInfo("CREATED_AT",    "TIMESTAMP_NTZ",  False),
                ]
            ),
            TableSchema(
                database="PROD_DW", schema="CATALOG", table="PRODUCTS",
                description="Product catalog with pricing",
                row_count=12_000,
                tags=["products", "catalog", "items", "sku", "inventory"],
                columns=[
                    ColumnInfo("PRODUCT_ID",    "VARCHAR(36)",    False, "UUID primary key"),
                    ColumnInfo("SKU",           "VARCHAR(50)",    False, "Human-readable SKU"),
                    ColumnInfo("NAME",          "VARCHAR(255)",   False, "Product display name"),
                    ColumnInfo("CATEGORY",      "VARCHAR(100)",   True,  "",
                               ["Electronics", "Apparel", "Home", "Software"]),
                    ColumnInfo("PRICE",         "NUMBER(10,2)",   False, "Current list price"),
                    ColumnInfo("COST",          "NUMBER(10,2)",   True,  "COGS"),
                    ColumnInfo("IS_ACTIVE",     "BOOLEAN",        False),
                    ColumnInfo("CREATED_AT",    "TIMESTAMP_NTZ",  False),
                ]
            ),
            TableSchema(
                database="PROD_DW", schema="ANALYTICS", table="DAILY_REVENUE",
                description="Pre-aggregated daily revenue by region — use for fast revenue queries",
                row_count=2_500,
                tags=["revenue", "daily", "aggregated", "finance", "kpi"],
                columns=[
                    ColumnInfo("DATE",          "DATE",           False),
                    ColumnInfo("REGION",        "VARCHAR(50)",    False, "", ["North America", "EMEA", "APAC"]),
                    ColumnInfo("GROSS_REVENUE", "NUMBER(15,2)",   False),
                    ColumnInfo("NET_REVENUE",   "NUMBER(15,2)",   False, "After discounts/refunds"),
                    ColumnInfo("ORDER_COUNT",   "INTEGER",        False),
                    ColumnInfo("CUSTOMER_COUNT","INTEGER",        False, "Distinct buyers"),
                    ColumnInfo("UPDATED_AT",    "TIMESTAMP_NTZ",  False),
                ]
            ),
            TableSchema(
                database="PROD_DW", schema="ANALYTICS", table="USER_EVENTS",
                description="Raw clickstream / product events",
                row_count=900_000_000,
                tags=["events", "clickstream", "behavior", "funnel", "pageview"],
                columns=[
                    ColumnInfo("EVENT_ID",      "VARCHAR(36)",    False),
                    ColumnInfo("USER_ID",       "VARCHAR(36)",    True,  "NULL for anonymous"),
                    ColumnInfo("SESSION_ID",    "VARCHAR(36)",    True),
                    ColumnInfo("EVENT_TYPE",    "VARCHAR(100)",   False, "",
                               ["page_view", "add_to_cart", "checkout", "purchase"]),
                    ColumnInfo("PAGE",          "VARCHAR(500)",   True),
                    ColumnInfo("PROPERTIES",    "VARIANT",        True,  "JSON blob"),
                    ColumnInfo("OCCURRED_AT",   "TIMESTAMP_NTZ",  False),
                ]
            ),
        ]
        for s in schemas:
            self._schemas[s.full_name] = s

    def select_relevant_schemas(self, question: str) -> list[TableSchema]:
        """
        Select the most relevant schemas for a given question.

        Production: replace keyword match with embedding similarity search
        (e.g., cosine similarity over OpenAI/Snowflake embeddings of schema descriptions).
        """
        question_lower = question.lower()
        scored: list[tuple[float, TableSchema]] = []

        for schema in self._schemas.values():
            score = 0.0
            # Tag match (high signal)
            for tag in schema.tags:
                if tag in question_lower:
                    score += 2.0
            # Description match
            for word in schema.description.lower().split():
                if len(word) > 3 and word in question_lower:
                    score += 0.5
            # Table name match
            if schema.table.lower() in question_lower:
                score += 3.0
            # Column name match
            for col in schema.columns:
                if col.name.lower().replace("_", " ") in question_lower:
                    score += 1.0

            if score > 0:
                scored.append((score, schema))

        # Sort by score descending, return top K
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = [s for _, s in scored[:self.max_tables_per_prompt]]

        # Always return at least 2 tables (for join discovery)
        if len(selected) < 2:
            all_schemas = list(self._schemas.values())
            for s in all_schemas:
                if s not in selected:
                    selected.append(s)
                if len(selected) >= 2:
                    break

        return selected

    def build_schema_prompt(self, question: str) -> str:
        """Build the schema section to inject into the system prompt."""
        schemas = self.select_relevant_schemas(question)
        ddls = "\n\n".join(s.to_ddl() for s in schemas)
        table_list = ", ".join(s.full_name for s in schemas)
        return (
            f"## Available Tables\n"
            f"Selected {len(schemas)} tables most relevant to this question.\n"
            f"Tables: {table_list}\n\n"
            f"### Schemas (DDL)\n"
            f"```sql\n{ddls}\n```"
        )

    def get_schema(self, full_name: str) -> Optional[TableSchema]:
        return self._schemas.get(full_name)

    def list_all_tables(self) -> list[str]:
        return list(self._schemas.keys())


# ─────────────────────────────────────────────────────────────────────────────
# 3. SQL VALIDATOR
#    Pre-flight checks before any query hits the database.
#    Catches the most common LLM SQL mistakes early.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    is_valid: bool
    errors:   list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = []
        if self.errors:
            parts.append("Errors:\n" + "\n".join(f"  - {e}" for e in self.errors))
        if self.warnings:
            parts.append("Warnings:\n" + "\n".join(f"  - {w}" for w in self.warnings))
        return "\n".join(parts) if parts else "Valid"


class SQLValidator:
    """
    Rule-based SQL validator. Catches common LLM mistakes before execution.

    Does NOT replace DB-level parsing — think of this as a fast pre-filter.
    """

    # Statements we never allow (data-modifying or DDL)
    FORBIDDEN_PATTERNS = [
        (r"\bDROP\s+TABLE\b",     "DROP TABLE is not allowed"),
        (r"\bDROP\s+DATABASE\b",  "DROP DATABASE is not allowed"),
        (r"\bTRUNCATE\b",         "TRUNCATE is not allowed"),
        (r"\bDELETE\s+FROM\b",    "DELETE is not allowed (read-only agent)"),
        (r"\bUPDATE\s+\w+\s+SET\b","UPDATE is not allowed (read-only agent)"),
        (r"\bINSERT\s+INTO\b",    "INSERT is not allowed (read-only agent)"),
        (r"\bCREATE\s+TABLE\b",   "CREATE TABLE is not allowed"),
        (r"\bALTER\s+TABLE\b",    "ALTER TABLE is not allowed"),
        (r"\bEXEC(UTE)?\b",       "EXECUTE is not allowed"),
        (r";\s*\w",               "Multiple statements (semicolon-separated) not allowed"),
    ]

    # Large table patterns that need a WHERE clause or LIMIT
    LARGE_TABLE_PATTERNS = [
        r"FROM\s+PROD_DW\.ANALYTICS\.USER_EVENTS",
    ]

    def validate(self, sql: str, schema_registry: SchemaRegistry) -> ValidationResult:
        errors:   list[str] = []
        warnings: list[str] = []

        sql_upper = sql.upper().strip()

        # ── Must be a SELECT ───────────────────────────────────────────────
        if not sql_upper.lstrip().startswith("SELECT"):
            errors.append("Query must start with SELECT (read-only agent).")

        # ── Forbidden patterns ─────────────────────────────────────────────
        for pattern, message in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                errors.append(message)

        # ── Missing LIMIT on potentially large scans ───────────────────────
        for pattern in self.LARGE_TABLE_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                has_limit = bool(re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE))
                has_where = bool(re.search(r"\bWHERE\b", sql, re.IGNORECASE))
                has_group = bool(re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE))
                if not (has_limit or has_where or has_group):
                    errors.append(
                        "Query on USER_EVENTS (900M rows) must include a WHERE clause, "
                        "GROUP BY, or LIMIT to avoid a full table scan."
                    )

        # ── SELECT * warning (expensive) ──────────────────────────────────
        if re.search(r"SELECT\s+\*", sql, re.IGNORECASE):
            warnings.append(
                "SELECT * fetches all columns. Consider selecting only the columns you need."
            )

        # ── Hallucinated table names ───────────────────────────────────────
        # Extract "FROM table" and "JOIN table" references and validate them
        known_tables = {t.lower() for t in schema_registry.list_all_tables()}
        table_refs = re.findall(
            r"(?:FROM|JOIN)\s+([\w.]+)",
            sql, re.IGNORECASE
        )
        for ref in table_refs:
            if "." in ref and ref.lower() not in known_tables:
                # Allow subquery aliases and CTEs (they won't have dots)
                warnings.append(
                    f"Table '{ref}' not found in schema registry. "
                    f"Verify the table name is correct."
                )

        # ── No ORDER BY on aggregated queries without GROUP BY ─────────────
        has_agg = bool(re.search(r"\b(SUM|AVG|COUNT|MIN|MAX)\s*\(", sql, re.IGNORECASE))
        has_group = bool(re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE))
        has_order = bool(re.search(r"\bORDER\s+BY\b", sql, re.IGNORECASE))
        if has_agg and not has_group and has_order:
            warnings.append(
                "Aggregate function without GROUP BY — ORDER BY may behave unexpectedly."
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 4. SNOWFLAKE EXECUTOR
#    Runs validated SQL and returns structured results.
#    Includes row limit, timeout, and result caching.
# ─────────────────────────────────────────────────────────────────────────────

class SnowflakeExecutor:
    """
    Executes SQL against Snowflake with safety guardrails.

    In this demo, returns simulated results.
    In production: use snowflake.connector or SQLAlchemy + Snowflake dialect.
    """

    MAX_ROWS    = 1000    # Hard cap on returned rows
    TIMEOUT_SEC = 30      # Query timeout

    def __init__(self, connection_params: Optional[dict] = None):
        self.connection_params = connection_params
        self._result_cache: dict[str, tuple[float, list[dict]]] = {}
        self.CACHE_TTL_SEC = 300  # 5 minutes

    def _cache_key(self, sql: str) -> str:
        return hashlib.md5(sql.strip().lower().encode()).hexdigest()

    def _get_cached(self, sql: str) -> Optional[list[dict]]:
        key = self._cache_key(sql)
        if key in self._result_cache:
            ts, rows = self._result_cache[key]
            if time.time() - ts < self.CACHE_TTL_SEC:
                return rows
        return None

    def _set_cache(self, sql: str, rows: list[dict]):
        self._result_cache[self._cache_key(sql)] = (time.time(), rows)

    def execute(self, sql: str) -> tuple[QueryStatus, list[dict], Optional[str]]:
        """
        Execute SQL. Returns (status, rows, error_message).

        Production implementation:
            conn = snowflake.connector.connect(**self.connection_params)
            cursor = conn.cursor(DictCursor)
            cursor.execute(f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {self.TIMEOUT_SEC}")
            cursor.execute(sql)
            rows = cursor.fetchmany(self.MAX_ROWS)
            return QueryStatus.SUCCESS, [dict(r) for r in rows], None
        """
        # Check cache
        cached = self._get_cached(sql)
        if cached is not None:
            return QueryStatus.SUCCESS, cached, None

        # ── DEMO: Simulate results based on SQL content ────────────────────
        rows = self._simulate_results(sql)
        self._set_cache(sql, rows)
        return QueryStatus.SUCCESS, rows, None

    def _simulate_results(self, sql: str) -> list[dict]:
        """Realistic fake results for demo purposes."""
        sql_lower = sql.lower()

        if "revenue" in sql_lower or "total_amount" in sql_lower:
            return [
                {"PRODUCT_NAME": "Pro Plan Annual",   "TOTAL_REVENUE": 1_240_500.00, "ORDER_COUNT": 830},
                {"PRODUCT_NAME": "Enterprise Bundle",  "TOTAL_REVENUE":   980_200.00, "ORDER_COUNT": 245},
                {"PRODUCT_NAME": "Starter Monthly",    "TOTAL_REVENUE":   750_100.00, "ORDER_COUNT": 5001},
                {"PRODUCT_NAME": "Add-on Storage 1TB", "TOTAL_REVENUE":   310_800.00, "ORDER_COUNT": 2060},
                {"PRODUCT_NAME": "Support Premium",    "TOTAL_REVENUE":   208_400.00, "ORDER_COUNT": 417},
            ]
        elif "customer" in sql_lower:
            return [
                {"SEGMENT": "enterprise",  "CUSTOMER_COUNT": 1240,  "AVG_LTV": 42000.00},
                {"SEGMENT": "mid-market",  "CUSTOMER_COUNT": 8900,  "AVG_LTV":  8500.00},
                {"SEGMENT": "smb",         "CUSTOMER_COUNT": 42000, "AVG_LTV":  1200.00},
                {"SEGMENT": "consumer",    "CUSTOMER_COUNT": 328000,"AVG_LTV":   180.00},
            ]
        elif "event" in sql_lower:
            return [
                {"EVENT_TYPE": "page_view",    "EVENT_COUNT": 4_200_000},
                {"EVENT_TYPE": "add_to_cart",  "EVENT_COUNT":   420_000},
                {"EVENT_TYPE": "checkout",     "EVENT_COUNT":   126_000},
                {"EVENT_TYPE": "purchase",     "EVENT_COUNT":    84_000},
            ]
        else:
            return [
                {"RESULT": "Query executed successfully", "ROW_COUNT": 1}
            ]


# ─────────────────────────────────────────────────────────────────────────────
# 5. PROMPT TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

SQL_SYSTEM_PROMPT = """You are a Snowflake SQL expert. Your job is to translate natural language questions into correct, efficient Snowflake SQL queries.

## Rules
1. Generate ONLY valid Snowflake SQL (not MySQL, Postgres, or generic SQL).
2. Always use fully-qualified table names: DATABASE.SCHEMA.TABLE
3. Never use SELECT * — always list the columns you need.
4. For date filtering: use DATE_TRUNC, DATEADD, and CURRENT_DATE() (Snowflake syntax).
5. For string operations: use ILIKE for case-insensitive matching.
6. Prefer aggregated tables (e.g., DAILY_REVENUE) over raw tables for performance.
7. Add a LIMIT clause on raw event tables unless the query is already aggregated.
8. Return ONLY the SQL — no explanation, no markdown fences, no preamble.

## Snowflake-specific syntax reminders
- Date arithmetic:  DATEADD(month, -1, CURRENT_DATE())
- Date truncation:  DATE_TRUNC('month', order_date)
- Conditional agg:  COUNT_IF(condition), SUM(IFF(cond, val, 0))
- Safe division:    DIV0(numerator, denominator)
- String concat:    CONCAT(a, b) or a || b
- JSON extraction:  properties:event_name::STRING

{schema_section}
"""

INTERPRETATION_PROMPT = """You are a data analyst interpreting SQL query results for a business user.

Given the question, SQL query, and results, provide a clear, concise natural language answer.
Focus on the business insight, not the technical details.
If results are empty, explain what that likely means.
Format numbers with commas and currency symbols where appropriate.
Keep your answer to 3-5 sentences maximum."""


# ─────────────────────────────────────────────────────────────────────────────
# 6. TEXT-TO-SQL AGENT — The main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class TextToSQLAgent:
    """
    Production Text-to-SQL agent with:
      - Dynamic schema injection (only relevant tables)
      - Pre-execution SQL validation
      - Retry loop with error feedback to the LLM
      - Result interpretation (NL answer from rows)
      - Query result caching
      - Full observability logging
    """

    MAX_SQL_ATTEMPTS = 3   # Max times to retry a failing SQL

    def __init__(self, connection_params: Optional[dict] = None):
        ollama_base = os.environ.get("OLLAMA_BASE_URL")
        if ollama_base:
            if OpenAI is None:
                raise ImportError(
                    "OLLAMA_BASE_URL is set; install the OpenAI SDK for Ollama's "
                    "compatible API: pip install openai"
                )
            # e.g. http://127.0.0.1:11435/v1
            self._openai_client = OpenAI(
                base_url=ollama_base.rstrip("/"),
                api_key=os.environ.get("OLLAMA_API_KEY", "ollama"),
            )
            self._ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.1")
            self.client = None
        else:
            self._openai_client = None
            self._ollama_model = ""
            self.client = anthropic.Anthropic()
        self.registry  = SchemaRegistry()
        self.validator = SQLValidator()
        self.executor  = SnowflakeExecutor(connection_params)

    def _llm_complete(
        self,
        system:   str,
        messages: list[dict],
        max_tokens: int,
    ) -> str:
        """Anthropic Messages API or Ollama via OpenAI-compatible HTTP."""
        if self._openai_client is not None:
            o_msgs = [{"role": "system", "content": system}, *messages]
            r = self._openai_client.chat.completions.create(
                model=self._ollama_model,
                messages=o_msgs,
                max_tokens=max_tokens,
            )
            return (r.choices[0].message.content or "").strip()
        resp = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return "".join(
            block.text for block in resp.content if hasattr(block, "text")
        ).strip()

    # ── Public interface ───────────────────────────────────────────────────

    def query(self, question: str, verbose: bool = True) -> QueryResult:
        """
        Main entry point. Translates a natural language question to SQL,
        executes it, and returns a structured result with a natural language answer.
        """
        start = time.time()

        if verbose:
            print(f"\n{'═'*65}")
            print(f"  QUESTION: {question}")
            print(f"{'═'*65}")

        # Build schema-injected system prompt (fresh per query)
        schema_section = self.registry.build_schema_prompt(question)
        system_prompt  = SQL_SYSTEM_PROMPT.format(schema_section=schema_section)

        # ── SQL generation + retry loop ────────────────────────────────────
        sql, attempts, error_history = self._generate_sql_with_retry(
            question, system_prompt, verbose
        )

        if sql is None:
            return QueryResult(
                status=QueryStatus.ERROR,
                sql="",
                answer="Failed to generate valid SQL after multiple attempts.",
                error="\n".join(error_history),
                attempts=attempts,
                latency_ms=(time.time() - start) * 1000,
            )

        # ── Execute validated SQL ──────────────────────────────────────────
        if verbose:
            print(f"\n▶ Executing SQL:\n{sql}\n")

        status, rows, exec_error = self.executor.execute(sql)

        if status != QueryStatus.SUCCESS:
            return QueryResult(
                status=status, sql=sql, answer="Query execution failed.",
                error=exec_error, attempts=attempts,
                latency_ms=(time.time() - start) * 1000,
            )

        # ── Interpret results in natural language ──────────────────────────
        answer = self._interpret_results(question, sql, rows, verbose)

        result = QueryResult(
            status=QueryStatus.SUCCESS,
            sql=sql,
            answer=answer,
            rows=rows,
            row_count=len(rows),
            attempts=attempts,
            latency_ms=(time.time() - start) * 1000,
        )

        if verbose:
            print(f"\n✅ ANSWER:\n   {answer}")
            print(f"\n📊 {attempts} attempt(s) | {result.row_count} rows | {result.latency_ms:.0f}ms")

        return result

    # ── Internal methods ───────────────────────────────────────────────────

    def _generate_sql_with_retry(
        self,
        question:      str,
        system_prompt: str,
        verbose:       bool,
    ) -> tuple[Optional[str], int, list[str]]:
        """
        The retry loop. Asks the LLM to generate SQL, validates it,
        and if invalid feeds the validation errors back as context
        so the LLM can correct its mistake.

        Returns: (sql | None, attempt_count, error_history)
        """
        messages      = [{"role": "user", "content": question}]
        error_history = []

        for attempt in range(1, self.MAX_SQL_ATTEMPTS + 1):
            if verbose:
                print(f"\n{'─'*40}")
                print(f"  SQL generation attempt {attempt}/{self.MAX_SQL_ATTEMPTS}")

            # ── Ask the LLM ────────────────────────────────────────────────
            raw_sql = self._extract_sql(
                self._llm_complete(system_prompt, messages, max_tokens=1024)
            )

            if verbose:
                print(f"  Generated:\n  {raw_sql[:200]}{'...' if len(raw_sql) > 200 else ''}")

            # ── Validate ───────────────────────────────────────────────────
            validation = self.validator.validate(raw_sql, self.registry)

            if validation.warnings and verbose:
                for w in validation.warnings:
                    print(f"  ⚠️  Warning: {w}")

            if validation.is_valid:
                if verbose:
                    print(f"  ✅ Validation passed")
                return raw_sql, attempt, error_history

            # ── Validation failed — build error feedback ───────────────────
            error_msg = str(validation)
            error_history.append(f"Attempt {attempt}: {error_msg}")

            if verbose:
                print(f"  ❌ Validation failed:\n  {error_msg}")

            # If we have retries left, append error as feedback to the LLM
            if attempt < self.MAX_SQL_ATTEMPTS:
                messages.append({
                    "role": "assistant",
                    "content": raw_sql,
                })
                messages.append({
                    "role": "user",
                    "content": (
                        f"That SQL has the following issues. Please fix them and return "
                        f"corrected SQL only:\n\n{error_msg}"
                    )
                })

        return None, self.MAX_SQL_ATTEMPTS, error_history

    def _extract_sql(self, raw: str) -> str:
        """Strip markdown fences from model output (SQL only)."""
        raw = raw.strip()
        raw = re.sub(r"^```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```\s*$", "", raw)
        return raw.strip()

    def _interpret_results(
        self,
        question: str,
        sql:      str,
        rows:     list[dict],
        verbose:  bool,
    ) -> str:
        """Call the LLM a second time to turn rows into a human-readable answer."""
        if not rows:
            return "The query returned no results."

        # Truncate to avoid token overflow on large result sets
        rows_preview = rows[:20]
        rows_text    = json.dumps(rows_preview, indent=2, default=str)
        if len(rows) > 20:
            rows_text += f"\n... ({len(rows) - 20} more rows)"

        prompt = (
            f"Question: {question}\n\n"
            f"SQL executed:\n{sql}\n\n"
            f"Results ({len(rows)} rows):\n{rows_text}"
        )

        return self._llm_complete(
            INTERPRETATION_PROMPT,
            [{"role": "user", "content": prompt}],
            max_tokens=512,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7. DEMO
# ─────────────────────────────────────────────────────────────────────────────

def run_demo():
    agent = TextToSQLAgent()

    queries = [
        # Basic aggregation
        "What were the top 5 products by total revenue last month?",

        # Join query
        "Show me the number of customers per segment and their average lifetime value.",

        # Time-series
        "What is the daily revenue trend for the past 30 days in North America?",

        # This should trigger the large-table safety validator
        "Show me all events from USER_EVENTS without any filters.",

        # Ambiguous — tests schema selection
        "Which region has the highest conversion rate?",
    ]

    for q in queries:
        result = agent.query(q, verbose=True)
        print()


if __name__ == "__main__":
    run_demo()