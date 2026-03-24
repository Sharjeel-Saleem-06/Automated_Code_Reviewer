# How It Works — Internal Workflow

This document walks through the Multi-Agent Code Reviewer from input to final report, aligned with the actual implementation under `src/`.

---

## High-level flow (ASCII)

```
                         ┌──────────────────────────────────────┐
                         │  INPUT: unified diff (file / demo  │
                         │  / GitHub PR via PyGithub)         │
                         └──────────────────┬───────────────────┘
                                            │
                         ┌──────────────────▼───────────────────┐
                         │  LangGraph StateGraph (ReviewState)   │
                         │  START → logic → security → perf →   │
                         │          supervisor → END             │
                         └──────────────────┬───────────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────────┐
              ▼                             ▼                             ▼
       ┌─────────────┐               ┌─────────────┐               ┌─────────────┐
       │ LogicAgent  │               │SecurityAgent│               │Performance  │
       │ JSON review │               │ JSON review │               │Agent JSON   │
       └──────┬──────┘               └──────┬──────┘               └──────┬──────┘
              │                             │                             │
              └─────────────────────────────┼─────────────────────────────┘
                                            ▼
                              ┌─────────────────────────┐
                              │   SupervisorAgent       │
                              │   merge_reports() →     │
                              │   markdown PR comment   │
                              └────────────┬────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │ OUTPUT: final_report +    │
                              │ agent_stats (tokens $)   │
                              └─────────────────────────┘

  OPTIONAL (separate demo path):
  Tool-use loop: Messages API + TOOL_DEFINITIONS → execute →
                 append tool_result → repeat (base_agent: max 5)
```

---

## Step 1: Input — loading the diff

The pipeline always starts with a **single string** containing a unified diff (added lines with `+`, context, hunks).

| Source | Mechanism | Code |
|--------|-----------|------|
| Built-in demo | `_get_demo_diff()` returns a vulnerable Flask-style sample | `src/tools/github_tools.py` |
| File | `load_diff(file_path)` reads a `.diff` or patch file | `src/main.py` |
| GitHub PR | `get_pr_diff(owner, repo, pr_number, github_token=...)` aggregates file patches | `src/tools/github_tools.py`, invoked from `cmd_pr` in `src/main.py` |

The PR URL is parsed by `parse_pr_url` in `src/main.py` (expects `https://github.com/{owner}/{repo}/pull/{n}`). If `GITHUB_TOKEN` is missing or placeholder, real PR fetch is skipped and demo behavior applies inside `get_pr_diff`.

---

## Step 2: LangGraph `StateGraph` initialization

`run_review(diff)` in `src/graph/workflow.py` compiles a graph once per invocation and invokes it with initial state:

```python
{
    "diff": diff,
    "reviews": [],
    "final_report": "",
    "agent_stats": [],
}
```

### `ReviewState`

`ReviewState` is a `TypedDict` declaring what flows through the graph:

- **`diff` (`str`)**: Immutable input; every specialist node reads `state["diff"]`.
- **`reviews` (`Annotated[list, operator.add]`)**: Each agent node **returns** `{"reviews": [single_result]}`; LangGraph **concatenates** lists from successive nodes so the supervisor sees all three JSON reports.
- **`final_report` (`str`)**: The supervisor node **overwrites** this with merged markdown (last write wins).
- **`agent_stats` (`Annotated[list, operator.add]`)**: Same reduction pattern as `reviews` — each node appends one stats dict; the CLI prints the full table.

### Why `Annotated[list, operator.add]`?

In LangGraph, plain `list` fields default to **replace** semantics when a node returns a partial update. Annotating with `operator.add` registers a **reducer**: returned one-element lists are **appended** to the existing list. That is how three separate nodes each contribute one review and one stats row without manual merge code in Python.

The graph topology is strictly linear:

`logic_agent` → `security_agent` → `performance_agent` → `supervisor` → `END` (`src/graph/workflow.py`).

---

## Step 3: Logic Agent

**Role:** Find **correctness and logic** defects on **added lines** only.

**Checks (from prompt):** off-by-one errors, missing null checks, bad boolean logic, race conditions, infinite loops, wrong/missing returns, type issues, unhandled edge cases (`src/prompts/system_prompts.py`, `LOGIC_AGENT_PROMPT`).

**Prompt techniques:**

- **Role prompting:** Principal engineer persona.
- **Chain-of-thought:** “Think step by step… trace through the code mentally.”
- **Few-shot:** `<example>` with `get_average` and division-by-zero JSON.
- **Structured output:** Strict JSON with `agent`, `summary`, `findings[]` (`bug_type`, `trigger_scenario`, `suggested_fix`, severities).
- **XML-style sections:** `<role>`, `<task>`, `<rules>`, `<output_format>`, `<example>`.

**Execution:** `LogicAgent` subclasses `BaseAgent` with `use_tools=False` (`src/agents/logic_agent.py`). The user message wraps the diff in `<diff>...</diff>` (`src/agents/base_agent.py`, `_run_direct`).

**Output:** Parsed JSON via `_parse_json`; appended to `reviews` in `logic_node` (`src/graph/workflow.py`).

---

## Step 4: Security Agent

**Role:** OWASP-oriented **vulnerability** review on added lines.

**Checks:** SQL injection, XSS, hardcoded secrets, weak crypto, command injection, path traversal, unsafe deserialization, missing auth, SSRF, sensitive data exposure (`SECURITY_AGENT_PROMPT` in `src/prompts/system_prompts.py`).

**OWASP / CWE / attacks:** The prompt requires citing **OWASP Top 10** categories (e.g. `A03:2021 Injection`) and describing **concrete attack scenarios** (e.g. `"' OR '1'='1"` for SQLi). CWE is referenced at the persona level (“CWE weaknesses”).

**Output JSON:** Fields include `vulnerability_type`, `owasp_category`, `attack_scenario`, `suggested_fix`.

**Code path:** `SecurityAgent` → `BaseAgent._run_direct` (`src/agents/security_agent.py`).

---

## Step 5: Performance Agent

**Role:** Scalability and **complexity** regressions.

**Checks:** N+1 queries, missing indexes, nested loops, missing caching, blocking I/O, unbounded memory growth, string concat in loops, repeated regex compile, pooling gaps, unbounded structures (`PERFORMANCE_AGENT_PROMPT`).

**Scale framing:** Rules require estimating **big-O** style impact (“what happens when input grows 100x”) and fields like `current_complexity` and `impact_at_scale` in JSON.

**Code path:** `PerformanceAgent` (`src/agents/performance_agent.py`).

---

## Step 6: Supervisor — merge, de-duplicate, severity ranking

**Role:** Lead reviewer producing **one markdown** comment suitable for GitHub.

**Inputs:** `json.dumps(agent_reports)` of all entries in `state["reviews"]`, wrapped in `<agent_reports>` (`src/agents/supervisor.py`).

**Prompt rules (`SUPERVISOR_PROMPT`):** Group by severity (Critical → Low), de-duplicate cross-agent duplicates, attribute findings to agents, verdict **CHANGES REQUESTED** vs **APPROVED**, summary table by agent, “LGTM ✅” if empty (`src/prompts/system_prompts.py`).

**Output:** Free-form **markdown** text (not JSON) — `response.content[0].text`.

**Graph update:** `supervisor_node` sets `final_report` and appends supervisor `agent_stats` (`src/graph/workflow.py`).

---

## Step 7: Output and metrics

`run_review` returns the final state dict. `src/main.py` (`cmd_review`, `cmd_pr`):

- Prints **`final_report`** (supervisor markdown).
- Prints **`print_stats_table(agent_stats)`**: per-agent `total_tokens`, `latency_ms`, `estimated_cost_usd`, plus totals and `MODEL_NAME`.
- Optionally dumps **raw JSON** per agent for transparency (`INDIVIDUAL AGENT FINDINGS` section).

---

## Tool-use agentic loop (`base_agent.py`)

Specialist reviewers use **direct** completion (`_run_direct`). The **tool loop** lives in `BaseAgent._run_with_tools` for agents constructed with `use_tools=True` (pattern available for GitHub-augmented agents).

**Algorithm (max 5 iterations):**

1. Initialize `messages` with the user turn.
2. Call `client.messages.create` with `tools=TOOL_DEFINITIONS` from `src/tools/github_tools.py`.
3. Accumulate `input_tokens` / `output_tokens` from `response.usage`.
4. If **`stop_reason == "tool_use"`**: For each `tool_use` block, look up `TOOL_EXECUTOR[block.name]`, run with `block.input`, append assistant `content` and a user message containing `tool_result` payloads (with `tool_use_id`). Go to step 2.
5. If **`stop_reason == "end_turn"`**: Extract text blocks, `_parse_json` on text, return dict.
6. If the loop exhausts **5** iterations without structured JSON, return a safe empty fallback with `summary` explaining incomplete output (`src/agents/base_agent.py`).

**Related demo:** `run_tool_agent_demo` in `src/graph/tool_agent_workflow.py` implements the same pattern with a **6-iteration** ceiling and prints each tool step for CLI visibility — useful for interviews when distinguishing “production cap” (5) from “demo harness” (6).

---

## JD alignment (representative mapping)

| Job-description theme | Where it shows up in code |
|------------------------|---------------------------|
| Multi-step agent workflows / reasoning chains | Sequential LangGraph nodes + CoT instructions in `src/prompts/system_prompts.py` |
| Orchestration frameworks (LangGraph / LangChain ecosystem) | `StateGraph`, `ReviewState`, `build_review_graph` in `src/graph/workflow.py` |
| Tool calling and function execution | `TOOL_DEFINITIONS`, `TOOL_EXECUTOR`, `_run_with_tools`, `tool_agent_workflow.py` |
| Testing / evaluation / hallucination awareness | `TEST_SUITE`, precision/recall in `src/evaluation/evaluator.py`, `cmd_eval` in `src/main.py` |
| Monitoring cost / performance | Token usage + `_estimate_cost` in `src/agents/base_agent.py`, `src/agents/supervisor.py`, CLI stats in `src/main.py` |
| Real-world integration (GitHub) | `get_pr_diff`, PyGithub paths in `src/tools/github_tools.py`, `pr` subcommand in `src/main.py` |

Use this table to narrate **why** each file exists when discussing ownership of the system end-to-end.
