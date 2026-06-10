"""
multi_agent_orchestrator.py — Production Multi-Agent Orchestrator Pattern

Architecture:
  Orchestrator  — decomposes tasks, routes to sub-agents, synthesizes results
  Sub-Agents    — specialized workers with their own tools and system prompts
    ├── ResearchAgent   — web search, fact finding, current events
    ├── AnalystAgent    — data analysis, calculations, comparisons
    ├── WriterAgent     — drafting, summarizing, formatting output
    └── CriticAgent     — quality review, error catching, refinement

Communication pattern:
  Orchestrator → Plan (list of subtasks with agent assignments)
  Sub-Agents   → Results (structured outputs back to orchestrator)
  Orchestrator → Synthesis (final answer from all results)

Usage:
    orchestrator = Orchestrator()
    result = orchestrator.run("Write a competitive analysis of Snowflake vs Databricks")
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import anthropic

# ─────────────────────────────────────────────────────────────────────────────
# 1. SHARED DATA MODELS
# ─────────────────────────────────────────────────────────────────────────────

class AgentType(Enum):
    RESEARCH = "research"
    ANALYST  = "analyst"
    WRITER   = "writer"
    CRITIC   = "critic"


class SubtaskStatus(Enum):
    PENDING    = "pending"
    RUNNING    = "running"
    DONE       = "done"
    FAILED     = "failed"


@dataclass
class Subtask:
    """A unit of work the orchestrator assigns to a sub-agent."""
    id:           str
    agent_type:   AgentType
    instruction:  str                          # What the sub-agent should do
    depends_on:   list[str] = field(default_factory=list)  # IDs of subtasks that must finish first
    status:       SubtaskStatus = SubtaskStatus.PENDING
    result:       Optional[str] = None
    error:        Optional[str] = None
    duration_ms:  float = 0.0


@dataclass
class Plan:
    """The orchestrator's decomposition of the user's goal into subtasks."""
    goal:     str
    subtasks: list[Subtask]
    reasoning: str = ""       # Why the orchestrator chose this decomposition


@dataclass
class OrchestratorResult:
    """Final output returned to the caller."""
    goal:          str
    final_answer:  str
    plan:          Plan
    subtask_count: int
    total_duration_ms: float
    tokens_used:   int = 0

    def summary(self) -> str:
        done   = sum(1 for t in self.plan.subtasks if t.status == SubtaskStatus.DONE)
        failed = sum(1 for t in self.plan.subtasks if t.status == SubtaskStatus.FAILED)
        return (
            f"Goal: {self.goal[:60]}...\n"
            f"Subtasks: {done} done, {failed} failed / {self.subtask_count} total\n"
            f"Duration: {self.total_duration_ms:.0f}ms"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. SHARED STATE
#    Passed by reference to all agents — the "bulletin board" pattern.
#    Agents write results here; later agents can read prior results.
# ─────────────────────────────────────────────────────────────────────────────

class SharedState:
    """
    Thread-safe (enough for sequential execution) shared memory.
    Each subtask's result is stored by subtask ID.
    Agents reference earlier results to build on each other's work.
    """
    def __init__(self, goal: str):
        self.goal    = goal
        self._store: dict[str, str] = {}
        self._log:   list[str]      = []

    def write(self, subtask_id: str, value: str):
        self._store[subtask_id] = value
        self._log.append(f"[WRITE] {subtask_id}: {value[:60]}...")

    def read(self, subtask_id: str) -> Optional[str]:
        return self._store.get(subtask_id)

    def read_all(self) -> dict[str, str]:
        return dict(self._store)

    def context_for_agent(self, depends_on: list[str]) -> str:
        """Build a context string from the results of dependency subtasks."""
        if not depends_on:
            return ""
        parts = []
        for dep_id in depends_on:
            result = self.read(dep_id)
            if result:
                parts.append(f"[Result from {dep_id}]\n{result}")
        return "\n\n".join(parts) if parts else ""


# ─────────────────────────────────────────────────────────────────────────────
# 3. BASE AGENT
# ─────────────────────────────────────────────────────────────────────────────

class BaseAgent:
    """
    Every sub-agent extends this. Provides:
    - The ReAct tool-use loop (same pattern from react_agent.py)
    - Configurable system prompt and tool set
    - Token tracking
    """

    MAX_STEPS = 8

    def __init__(self, name: str, system_prompt: str, tools: list[dict], tool_registry: dict[str, Callable]):
        self.name          = name
        self.system_prompt = system_prompt
        self.tools         = tools
        self.tool_registry = tool_registry
        self.client        = anthropic.Anthropic()
        self.tokens_used   = 0

    def run(self, task: str, context: str = "") -> str:
        """
        Execute a task, optionally with context from prior agents.
        Returns the final answer as a string.
        """
        user_message = task
        if context:
            user_message = f"Context from previous steps:\n{context}\n\n---\n\nYour task: {task}"

        messages = [{"role": "user", "content": user_message}]

        for step in range(self.MAX_STEPS):
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=self.system_prompt,
                tools=self.tools if self.tools else anthropic.NOT_GIVEN,
                messages=messages,
            )
            self.tokens_used += response.usage.input_tokens + response.usage.output_tokens

            # Done — extract final text
            if response.stop_reason == "end_turn":
                return self._extract_text(response.content)

            # Tool use
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    result = self._dispatch(block.name, block.input)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result,
                    })
                messages.append({"role": "user", "content": tool_results})
            else:
                break  # Unexpected stop reason

        return self._extract_text(response.content) if response else "No result produced."

    def _dispatch(self, name: str, args: dict) -> str:
        if name not in self.tool_registry:
            return f"Error: unknown tool '{name}'"
        try:
            return str(self.tool_registry[name](**args))
        except Exception as e:
            return f"Error running {name}: {e}"

    @staticmethod
    def _extract_text(content: list) -> str:
        return "".join(b.text for b in content if hasattr(b, "text")).strip()


# ─────────────────────────────────────────────────────────────────────────────
# 4. SPECIALIZED SUB-AGENTS
#    Each has its own system prompt, tools, and expertise.
# ─────────────────────────────────────────────────────────────────────────────

# ── Tool implementations ───────────────────────────────────────────────────

def web_search(query: str, max_results: int = 5) -> str:
    """Simulated web search."""
    return json.dumps([
        {
            "title":   f"Result {i+1}: {query}",
            "url":     f"https://source{i+1}.com/{query.replace(' ','-')}",
            "snippet": f"Detailed information about {query} — result {i+1}. This covers key aspects, recent developments, and expert perspectives on the topic.",
        }
        for i in range(max_results)
    ])

def fetch_url(url: str) -> str:
    """Simulated URL fetch."""
    return f"[Content from {url}]\nDetailed article content about the topic. Includes statistics, expert quotes, and analysis. For demo purposes this returns placeholder text."

def run_calculation(expression: str) -> str:
    """Safe math evaluator."""
    import math
    try:
        result = eval(expression, {"__builtins__": {}},
                      {"sqrt": math.sqrt, "log": math.log, "pi": math.pi, "e": math.e})
        return str(round(float(result), 6))
    except Exception as ex:
        return f"Error: {ex}"

def compare_values(items: list, metric: str) -> str:
    """Format a comparison table."""
    rows = [f"| {item.get('name','?'):20s} | {item.get(metric, 'N/A'):>12s} |" for item in items]
    return "| Item                 | {:>12s} |\n".format(metric) + "|" + "-"*22 + "|" + "-"*14 + "|\n" + "\n".join(rows)

def check_facts(claims: list[str]) -> str:
    """Simulated fact-check."""
    results = []
    for claim in claims:
        results.append({"claim": claim, "verdict": "plausible", "confidence": "medium",
                        "note": "Requires primary source verification."})
    return json.dumps(results, indent=2)

def score_quality(text: str, criteria: list[str]) -> str:
    """Simulated quality scoring."""
    scores = {c: round(3.5 + hash(c + text[:20]) % 15 / 10, 1) for c in criteria}
    overall = round(sum(scores.values()) / len(scores), 1)
    return json.dumps({"scores": scores, "overall": overall, "max": 5.0})


# ── ResearchAgent ──────────────────────────────────────────────────────────

RESEARCH_SYSTEM = """You are a research specialist. Your job is to find accurate, current information on any topic.

Guidelines:
- Always search before stating facts — don't rely on memory for specific data
- Fetch URLs to get full article content when snippets aren't enough
- Cite your sources (URL) for every key claim
- Focus on facts, data points, and direct quotes
- Return a well-structured research summary with sources at the end
- Be thorough but concise — aim for signal over volume"""

RESEARCH_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for information. Use specific queries for best results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string", "description": "Search query (3-8 words)"},
                "max_results": {"type": "integer", "description": "Number of results (1-5)", "default": 3}
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_url",
        "description": "Fetch and read the full content of a web page.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Full URL to fetch"}},
            "required": ["url"]
        }
    },
]

RESEARCH_REGISTRY = {"web_search": web_search, "fetch_url": fetch_url}


# ── AnalystAgent ───────────────────────────────────────────────────────────

ANALYST_SYSTEM = """You are a data analyst. Your job is to analyze information, run calculations, and draw data-driven conclusions.

Guidelines:
- Always show your calculations explicitly
- Compare options on clear, measurable dimensions
- Flag assumptions you're making
- Quantify claims when possible (percentages, ratios, ranges)
- Use comparison tables for multi-option analysis
- End with a clear, ranked recommendation with justification"""

ANALYST_TOOLS = [
    {
        "name": "run_calculation",
        "description": "Evaluate a math expression. Supports: +,-,*,/,**,sqrt,log,pi",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Python math expression"}},
            "required": ["expression"]
        }
    },
    {
        "name": "compare_values",
        "description": "Format a structured comparison table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items":  {"type": "array",  "items": {"type": "object"}, "description": "List of {name, metric_value} dicts"},
                "metric": {"type": "string", "description": "Metric name for the column header"}
            },
            "required": ["items", "metric"]
        }
    },
]

ANALYST_REGISTRY = {"run_calculation": run_calculation, "compare_values": compare_values}


# ── WriterAgent ────────────────────────────────────────────────────────────

WRITER_SYSTEM = """You are a professional writer and editor. Your job is to transform research and analysis into clear, compelling content.

Guidelines:
- Write for a professional business audience unless told otherwise
- Structure content with clear headers and logical flow
- Translate data into plain language insights
- Lead with the most important finding (inverted pyramid)
- Use active voice, concrete examples, and specific numbers
- Match tone to the request (formal report vs casual summary vs executive brief)
- No filler phrases like "In conclusion" or "It is important to note that"
- Do NOT use tools — just write based on the context provided"""

# Writer has no tools — pure generation from context
WRITER_TOOLS    = []
WRITER_REGISTRY = {}


# ── CriticAgent ────────────────────────────────────────────────────────────

CRITIC_SYSTEM = """You are a quality assurance specialist and editor. Your job is to review content and improve it.

Guidelines:
- Fact-check specific claims against provided research
- Flag unsupported assertions, logical gaps, or vague language
- Check for completeness — does the output actually answer the original goal?
- Suggest specific improvements (not just "needs more detail")
- If the content is strong, say so and explain why
- Return: VERDICT (PASS/NEEDS_REVISION), ISSUES (list), IMPROVED_VERSION (full rewrite or original if passing)"""

CRITIC_TOOLS = [
    {
        "name": "check_facts",
        "description": "Fact-check a list of specific claims.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claims": {"type": "array", "items": {"type": "string"}, "description": "List of specific factual claims to verify"}
            },
            "required": ["claims"]
        }
    },
    {
        "name": "score_quality",
        "description": "Score content quality on given criteria (scale 1-5).",
        "input_schema": {
            "type": "object",
            "properties": {
                "text":     {"type": "string", "description": "Content to score"},
                "criteria": {"type": "array",  "items": {"type": "string"}, "description": "Criteria to score on"}
            },
            "required": ["text", "criteria"]
        }
    },
]

CRITIC_REGISTRY = {"check_facts": check_facts, "score_quality": score_quality}


def build_agent(agent_type: AgentType) -> BaseAgent:
    """Factory — returns a configured agent for the given type."""
    configs = {
        AgentType.RESEARCH: ("ResearchAgent", RESEARCH_SYSTEM, RESEARCH_TOOLS, RESEARCH_REGISTRY),
        AgentType.ANALYST:  ("AnalystAgent",  ANALYST_SYSTEM,  ANALYST_TOOLS,  ANALYST_REGISTRY),
        AgentType.WRITER:   ("WriterAgent",   WRITER_SYSTEM,   WRITER_TOOLS,   WRITER_REGISTRY),
        AgentType.CRITIC:   ("CriticAgent",   CRITIC_SYSTEM,   CRITIC_TOOLS,   CRITIC_REGISTRY),
    }
    name, prompt, tools, registry = configs[agent_type]
    return BaseAgent(name, prompt, tools, registry)


# ─────────────────────────────────────────────────────────────────────────────
# 5. ORCHESTRATOR
#    The "manager" LLM that plans, routes, and synthesizes.
# ─────────────────────────────────────────────────────────────────────────────

ORCHESTRATOR_SYSTEM = """You are an orchestrator that decomposes complex tasks into subtasks for specialized agents.

Available agents:
- research  : finds facts, searches web, fetches URLs, cites sources
- analyst   : runs calculations, compares data, draws conclusions, makes recommendations
- writer    : drafts and structures final content from provided research/analysis
- critic    : reviews output for quality, fact-checks, suggests improvements

Your job: given a user's goal, produce a JSON plan.

Rules:
1. Use the minimum number of subtasks needed (aim for 2-5)
2. Subtasks run in dependency order — use depends_on to chain them
3. Each subtask has one agent type
4. Research before analysis; analyze before writing; write before critiquing
5. The final subtask should produce the user-facing output

Return ONLY valid JSON matching this schema:
{
  "reasoning": "Why you chose this decomposition",
  "subtasks": [
    {
      "id": "t1",
      "agent": "research|analyst|writer|critic",
      "instruction": "Detailed instruction for this agent",
      "depends_on": []
    }
  ]
}"""

SYNTHESIS_SYSTEM = """You are a synthesis expert. Given a user's original goal and the results from multiple specialized agents,
produce a single, polished final answer.

- Integrate all results coherently — don't just concatenate them
- The Critic's improved version (if present) should be your primary source
- Ensure the answer directly addresses the original goal
- Remove any internal workflow artifacts (task IDs, agent names, etc.)
- Format for the end user, not for internal review"""


class Orchestrator:
    """
    Multi-agent orchestrator. Decomposes goals, runs sub-agents in
    dependency order, and synthesizes a final answer.
    """

    def __init__(self):
        self.client      = anthropic.Anthropic()
        self.tokens_used = 0

    def run(self, goal: str, verbose: bool = True) -> OrchestratorResult:
        start = time.time()

        if verbose:
            print(f"\n{'═'*65}")
            print(f"  GOAL: {goal}")
            print(f"{'═'*65}")

        # ── Step 1: Plan ───────────────────────────────────────────────────
        plan = self._plan(goal, verbose)

        # ── Step 2: Execute subtasks in dependency order ───────────────────
        state = SharedState(goal)
        self._execute_plan(plan, state, verbose)

        # ── Step 3: Synthesize ─────────────────────────────────────────────
        final_answer = self._synthesize(goal, plan, state, verbose)

        elapsed_ms = (time.time() - start) * 1000

        result = OrchestratorResult(
            goal=goal,
            final_answer=final_answer,
            plan=plan,
            subtask_count=len(plan.subtasks),
            total_duration_ms=elapsed_ms,
            tokens_used=self.tokens_used,
        )

        if verbose:
            print(f"\n{'═'*65}")
            print(f"✅ FINAL ANSWER:\n{final_answer}")
            print(f"\n📊 {result.summary()}")

        return result

    # ── Planning ───────────────────────────────────────────────────────────

    def _plan(self, goal: str, verbose: bool) -> Plan:
        """Ask the orchestrator LLM to decompose the goal into subtasks."""
        if verbose:
            print(f"\n📋 Planning...")

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=ORCHESTRATOR_SYSTEM,
            messages=[{"role": "user", "content": f"Goal: {goal}"}],
        )
        self.tokens_used += response.usage.input_tokens + response.usage.output_tokens

        raw = "".join(b.text for b in response.content if hasattr(b, "text"))

        # Strip markdown fences if present
        import re
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```\s*$", "", raw)

        plan_data = json.loads(raw)

        subtasks = []
        for item in plan_data.get("subtasks", []):
            agent_str = item.get("agent", "writer").lower()
            # Map string to enum safely
            agent_type_map = {
                "research": AgentType.RESEARCH,
                "analyst":  AgentType.ANALYST,
                "writer":   AgentType.WRITER,
                "critic":   AgentType.CRITIC,
            }
            agent_type = agent_type_map.get(agent_str, AgentType.WRITER)
            subtasks.append(Subtask(
                id          = item["id"],
                agent_type  = agent_type,
                instruction = item["instruction"],
                depends_on  = item.get("depends_on", []),
            ))

        plan = Plan(goal=goal, subtasks=subtasks, reasoning=plan_data.get("reasoning", ""))

        if verbose:
            print(f"   Reasoning: {plan.reasoning}")
            for t in plan.subtasks:
                deps = f" (after {t.depends_on})" if t.depends_on else ""
                print(f"   {t.id}: [{t.agent_type.value.upper():8s}] {t.instruction[:60]}...{deps}")

        return plan

    # ── Execution ──────────────────────────────────────────────────────────

    def _execute_plan(self, plan: Plan, state: SharedState, verbose: bool):
        """
        Execute subtasks in topological order (dependencies first).
        Simple sequential execution — see production notes for async version.
        """
        executed = set()

        # Keep looping until all tasks are done or stuck
        max_rounds = len(plan.subtasks) * 2
        for _ in range(max_rounds):
            made_progress = False

            for subtask in plan.subtasks:
                if subtask.status != SubtaskStatus.PENDING:
                    continue

                # Check all dependencies are satisfied
                deps_done = all(
                    any(t.id == dep_id and t.status == SubtaskStatus.DONE
                        for t in plan.subtasks)
                    for dep_id in subtask.depends_on
                ) if subtask.depends_on else True

                if not deps_done:
                    continue

                # Execute this subtask
                self._run_subtask(subtask, state, verbose)
                executed.add(subtask.id)
                made_progress = True

            if not made_progress:
                break  # No progress = stuck (circular dep or all done)

            if all(t.status in (SubtaskStatus.DONE, SubtaskStatus.FAILED)
                   for t in plan.subtasks):
                break

    def _run_subtask(self, subtask: Subtask, state: SharedState, verbose: bool):
        """Run a single subtask using the appropriate agent."""
        subtask.status = SubtaskStatus.RUNNING
        start = time.time()

        if verbose:
            deps = f" | context from: {subtask.depends_on}" if subtask.depends_on else ""
            print(f"\n🔧 [{subtask.id}] {subtask.agent_type.value.upper()}{deps}")
            print(f"   → {subtask.instruction[:80]}...")

        try:
            agent   = build_agent(subtask.agent_type)
            context = state.context_for_agent(subtask.depends_on)
            result  = agent.run(subtask.instruction, context)

            self.tokens_used += agent.tokens_used
            state.write(subtask.id, result)

            subtask.result     = result
            subtask.status     = SubtaskStatus.DONE
            subtask.duration_ms = (time.time() - start) * 1000

            if verbose:
                preview = result[:120].replace("\n", " ")
                print(f"   ✅ Done ({subtask.duration_ms:.0f}ms): {preview}...")

        except Exception as e:
            subtask.status = SubtaskStatus.FAILED
            subtask.error  = str(e)
            if verbose:
                print(f"   ❌ Failed: {e}")

    # ── Synthesis ──────────────────────────────────────────────────────────

    def _synthesize(self, goal: str, plan: Plan, state: SharedState, verbose: bool) -> str:
        """Final LLM call to integrate all sub-agent results into one answer."""
        if verbose:
            print(f"\n🔗 Synthesizing...")

        all_results = state.read_all()
        results_text = "\n\n".join(
            f"=== {tid} ({next((t.agent_type.value for t in plan.subtasks if t.id == tid), '?')}) ===\n{result}"
            for tid, result in all_results.items()
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=SYNTHESIS_SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"Original goal: {goal}\n\n"
                    f"Sub-agent results:\n{results_text}\n\n"
                    f"Produce the final integrated answer."
                )
            }],
        )
        self.tokens_used += response.usage.input_tokens + response.usage.output_tokens
        return "".join(b.text for b in response.content if hasattr(b, "text")).strip()


# ─────────────────────────────────────────────────────────────────────────────
# 6. DEMO
# ─────────────────────────────────────────────────────────────────────────────

def run_demo():
    orchestrator = Orchestrator()

    goals = [
        # Triggers: research → analyst → writer → critic
        "Write a competitive analysis comparing Snowflake vs Databricks for an enterprise data team.",

        # Triggers: research → writer (simpler task)
        "Summarize the key trends in AI agents for 2025.",

        # Triggers: research → analyst → writer (data-heavy)
        "Analyze the ROI of migrating from on-premise data warehouses to Snowflake.",
    ]

    for goal in goals:
        result = orchestrator.run(goal, verbose=True)
        print("\n" + "="*65 + "\n")


if __name__ == "__main__":
    run_demo()