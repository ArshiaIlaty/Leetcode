"""
react_agent.py — A complete ReAct (Reason + Act) agent from scratch.

Implements the full Reason → Act → Observe loop using the Anthropic API.
Includes: tool schema definition, dispatch, loop detection, memory, and error handling.

Usage:
    python react_agent.py
    # Or import and use directly:
    #   from react_agent import Agent, run_demo
"""

import json
import math
import random
import datetime
from dataclasses import dataclass, field
from typing import Any, Callable
import anthropic

# ─────────────────────────────────────────────────────────────────────────────
# 1. TOOL DEFINITIONS
#    Each tool has: a JSON schema (what the LLM sees) and a Python function
#    (what actually runs). Keep them together for clarity.
# ─────────────────────────────────────────────────────────────────────────────

def calculator(expression: str) -> str:
    """
    Safely evaluate a math expression.
    Supports: +, -, *, /, **, sqrt(), sin(), cos(), log(), pi, e
    """
    allowed_names = {
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
        "log": math.log, "abs": abs, "round": round,
        "pi": math.pi, "e": math.e,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(round(result, 6))
    except Exception as ex:
        return f"Error evaluating '{expression}': {ex}"


def get_weather(city: str) -> str:
    """Simulated weather API — returns realistic-looking fake data."""
    conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "windy"]
    temp_c = random.randint(5, 35)
    condition = random.choice(conditions)
    humidity = random.randint(30, 90)
    return json.dumps({
        "city": city,
        "temperature_c": temp_c,
        "temperature_f": round(temp_c * 9/5 + 32, 1),
        "condition": condition,
        "humidity_pct": humidity,
        "source": "WeatherAPI (simulated)"
    })


def search_web(query: str, max_results: int = 3) -> str:
    """
    Simulated web search — in production, swap this for a real search API
    (Brave, Serper, Tavily, etc.).
    """
    fake_results = [
        {
            "title": f"Result {i+1}: {query} — Overview",
            "url": f"https://example.com/{query.replace(' ', '-')}-{i+1}",
            "snippet": (
                f"Comprehensive information about {query}. "
                f"This result covers the key aspects of {query} including background, "
                f"current developments, and expert analysis (result {i+1} of {max_results})."
            ),
        }
        for i in range(max_results)
    ]
    return json.dumps(fake_results, indent=2)


def get_current_time(timezone: str = "UTC") -> str:
    """Returns the current time. Timezone param is accepted but not used in this demo."""
    now = datetime.datetime.utcnow()
    return json.dumps({
        "utc_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone_requested": timezone,
        "note": "UTC returned (demo mode)"
    })


def read_file(filename: str) -> str:
    """Simulated file reader — returns fake content for demo purposes."""
    if "." not in filename:
        return f"Error: '{filename}' has no extension. Provide a full filename."
    fake_content = {
        "report.txt": "Q3 Revenue: $4.2M\nGrowth: +18% YoY\nTop Market: APAC",
        "data.csv": "name,score\nAlice,92\nBob,87\nCarol,95",
        "notes.md": "## Meeting Notes\n- Discussed agent architecture\n- Next steps: implement memory layer",
    }
    return fake_content.get(filename, f"File '{filename}' not found in the simulated filesystem.")


# Map tool names → Python functions (used in dispatch)
TOOL_REGISTRY: dict[str, Callable] = {
    "calculator":     calculator,
    "get_weather":    get_weather,
    "search_web":     search_web,
    "get_current_time": get_current_time,
    "read_file":      read_file,
}

# JSON schemas for the LLM (sent in every API call)
TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": (
            "Evaluate a mathematical expression. Use for any arithmetic, algebra, "
            "or numeric computation. Supports: +, -, *, /, **, sqrt(), sin(), cos(), "
            "log(), abs(), round(), pi, e."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A valid Python math expression, e.g. '2 ** 10' or 'sqrt(144) / 3'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'San Francisco'"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for information about a topic. Use for factual lookups, news, or anything not in your training data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Number of results (1–5)", "default": 3}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_current_time",
        "description": "Get the current date and time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "description": "Timezone name, e.g. 'America/New_York'", "default": "UTC"}
            },
            "required": []
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file from the filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename with extension, e.g. 'report.txt'"}
            },
            "required": ["filename"]
        }
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 2. AGENT STATE
#    Tracks messages, tool call history (for loop detection), and metadata.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentState:
    messages: list[dict] = field(default_factory=list)
    tool_calls_log: list[dict] = field(default_factory=list)   # full history
    step: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def log_tool_call(self, name: str, args: dict, result: str):
        self.tool_calls_log.append({"name": name, "args": args, "result": result})

    def detect_loop(self) -> bool:
        """
        Simple loop detection: if the last 2 tool calls are identical
        (same name + same args), we're stuck in a loop.
        """
        if len(self.tool_calls_log) < 4:
            return False
        last_four = self.tool_calls_log[-4:]
        return last_four[0:2] == last_four[2:4]

    def summary(self) -> str:
        return (
            f"Steps: {self.step} | "
            f"Tool calls: {len(self.tool_calls_log)} | "
            f"Tokens in/out: {self.total_input_tokens}/{self.total_output_tokens}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. TOOL DISPATCH
#    Calls the right Python function and returns the result as a string.
#    All errors are caught and returned as strings — the LLM sees them
#    as observations and can adapt (retry, try different approach, etc.)
# ─────────────────────────────────────────────────────────────────────────────

def dispatch_tool(name: str, args: dict) -> str:
    if name not in TOOL_REGISTRY:
        known = ", ".join(TOOL_REGISTRY.keys())
        return f"Error: Unknown tool '{name}'. Available tools: {known}"
    try:
        fn = TOOL_REGISTRY[name]
        result = fn(**args)
        return str(result)
    except TypeError as e:
        return f"Error: Wrong arguments for '{name}': {e}"
    except Exception as e:
        return f"Error running '{name}': {type(e).__name__}: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. THE REACT LOOP
#    The core of the agent. Runs until:
#      (a) LLM returns a final answer (stop_reason == "end_turn")
#      (b) Max steps reached (safety exit)
#      (c) Loop detected (identical tool calls repeating)
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.

When answering questions:
1. Think about what information or computation you need.
2. Use tools to gather that information — don't guess or make up facts.
3. After receiving a tool result, reason about whether you have enough to answer.
4. If a tool returns an error, try a different approach or tool.
5. When you have enough information, give a clear, concise final answer.

Be efficient — don't call tools you don't need."""


def run_agent(
    user_query: str,
    max_steps: int = 10,
    verbose: bool = True,
) -> tuple[str, AgentState]:
    """
    Run the ReAct agent on a user query.

    Returns:
        (final_answer: str, state: AgentState)
    """
    client = anthropic.Anthropic()
    state = AgentState()

    # Initialize with the user's question
    state.messages = [{"role": "user", "content": user_query}]

    if verbose:
        print(f"\n{'═'*60}")
        print(f"  USER: {user_query}")
        print(f"{'═'*60}")

    for step in range(max_steps):
        state.step = step + 1

        # ── REASON: Ask the LLM what to do next ──────────────────────────────
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=state.messages,
        )

        state.total_input_tokens  += response.usage.input_tokens
        state.total_output_tokens += response.usage.output_tokens

        # ── DONE: LLM has produced a final answer ─────────────────────────────
        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            if verbose:
                print(f"\n✅ FINAL ANSWER (after {state.step} steps):")
                print(f"   {final_text}")
                print(f"\n📊 {state.summary()}")

            return final_text, state

        # ── ACT: LLM wants to call one or more tools ──────────────────────────
        if response.stop_reason == "tool_use":
            # Append the assistant's full response to history
            state.messages.append({
                "role": "assistant",
                "content": response.content   # may contain text + tool_use blocks
            })

            # Log any reasoning text the LLM produced before the tool call
            for block in response.content:
                if hasattr(block, "text") and block.text.strip():
                    if verbose:
                        print(f"\n💭 Step {state.step} — Thinking:")
                        print(f"   {block.text.strip()}")

            # Process ALL tool calls in this step (LLM can call multiple at once)
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_args = block.input
                tool_id   = block.id

                if verbose:
                    print(f"\n🔧 Step {state.step} — Tool call: {tool_name}({json.dumps(tool_args)})")

                # ── OBSERVE: Execute the tool ─────────────────────────────────
                result = dispatch_tool(tool_name, tool_args)
                state.log_tool_call(tool_name, tool_args, result)

                if verbose:
                    # Truncate long results for readability
                    display = result if len(result) < 300 else result[:300] + "..."
                    print(f"   → {display}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result,
                })

            # Feed all observations back into the conversation
            state.messages.append({"role": "user", "content": tool_results})

            # ── Loop detection ────────────────────────────────────────────────
            if state.detect_loop():
                msg = "Stopped: detected repeating tool calls (possible loop)."
                if verbose:
                    print(f"\n⚠️  {msg}")
                return msg, state

        else:
            # Unexpected stop reason — bail out
            msg = f"Unexpected stop_reason: '{response.stop_reason}'"
            if verbose:
                print(f"\n⚠️  {msg}")
            return msg, state

    # ── Max steps reached ─────────────────────────────────────────────────────
    msg = f"Reached max_steps={max_steps} without a final answer."
    if verbose:
        print(f"\n⚠️  {msg}\n📊 {state.summary()}")
    return msg, state


# ─────────────────────────────────────────────────────────────────────────────
# 5. DEMO — run a set of example queries
# ─────────────────────────────────────────────────────────────────────────────

def run_demo():
    """Run a handful of example queries to show the agent in action."""
    demo_queries = [
        # Simple tool use
        "What is the square root of 1764, divided by 3?",

        # Multi-step: needs weather + math
        "What's the weather in Tokyo right now? And convert that temperature to Kelvin.",

        # Multi-tool: needs search + time
        "What time is it right now, and search for 'Snowflake Cortex AI' for me.",

        # File + reasoning
        "Read the file 'data.csv' and tell me who has the highest score.",

        # Error recovery: LLM should adapt when tool fails
        "Read the file 'doesnotexist' and summarize its contents.",
    ]

    for query in demo_queries:
        answer, state = run_agent(query, verbose=True)
        print()


if __name__ == "__main__":
    run_demo()