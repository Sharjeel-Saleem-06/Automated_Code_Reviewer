# Interview Guide — Defend the Build

Use this guide to sound like you **designed and shipped** the Multi-Agent Code Reviewer, not merely ran a demo. Pair it with live terminal output from `python -m src.main`.

---

## 30-second elevator pitch

“I built a multi-agent code review pipeline on **LangGraph**: three **Claude Haiku** specialists—logic, security, and performance—each read the same PR diff and return **strict JSON**. A **supervisor** agent merges and deduplicates into one **markdown** review with severity ordering. I used **Anthropic tool calling** with GitHub-shaped functions so the model can fetch diffs and post comments in a loop, and I added an **evaluation suite** with precision and recall on labeled vulnerable diffs. The CLI covers quick demos, full review, single agents, tool demos, eval, and **live PR review** via URL.”

---

## Live demo script

| Step | Command / action | What to say (talking points) |
|------|------------------|------------------------------|
| 1 | `cd` to repo, `source venv/bin/activate` | “I run this as a module so imports resolve under `src/`.” |
| 2 | Show `.env` exists, **not** contents | “Keys load through `python-dotenv` in `config.py`; never commit secrets.” |
| 3 | `python -m src.main quick` | “This hits **one** agent on a tiny diff to prove the stack and keep cost low—good for screen-share warm-up.” |
| 4 | `python -m src.main review` | “Here’s the full **StateGraph**: logic, security, performance, then supervisor. Watch the `[1/4]` progress and the **token/cost** table—four API calls plus merge.” |
| 5 | Scroll **final_report** | “Supervisor output is **markdown** for GitHub; specialists were **JSON** for parsing and eval.” |
| 6 | `python -m src.main tools` | “Separate path: **tool_use** stop reason → execute `get_pr_diff` / `post_review_comment` → feed `tool_result` back until **end_turn**.” |
| 7 | Optional: `python -m src.main eval` | “I measure **recall** against expected vulnerability types on curated diffs; pass threshold is recall ≥ 0.8 per agent row.” |
| 8 | Optional: `python -m src.main pr "<url>"` | “With a PAT, `PyGithub` pulls real patches; same `run_review` as local file mode.” |

**If something fails:** Say “Production hardening would add retries, structured logging, and caching; the research prototype prioritizes clarity of the agent graph and eval hooks.”

---

## Q&A — confident answer, then depth

### Why multi-agent instead of one big prompt?

**Answer:** Specialization reduces **cross-objective confusion** and makes outputs **auditable**—security findings don’t get diluted by performance prose in the same JSON blob.

**Depth:** Each agent has a **narrow rubric** and **different JSON schema** (`bug_type` vs `vulnerability_type` vs `issue_type`), which improves parsing and lets us **evaluate** agents independently (`src/evaluation/evaluator.py`). The supervisor handles **deduplication and severity narrative** once, instead of asking one model to self-edit a monolithic list.

### Why LangGraph specifically?

**Answer:** I needed **explicit orchestration** over shared state with **append semantics** for per-agent results, not an ad-hoc script of function calls.

**Depth:** `ReviewState` uses `Annotated[list, operator.add]` so each node returns `{"reviews": [one]}` and LangGraph **concatenates** (`src/graph/workflow.py`). That’s clearer than manually threading a list through four calls. Compared to **raw loops**, LangGraph gives a **compile-time graph** we can extend later with branches, human-in-the-loop, or checkpointing. Compared to **CrewAI/AutoGen**, LangGraph stays close to **LangChain-core** types and stays thin—good when you already standardize on Anthropic Messages API.

### How does tool calling work here?

**Answer:** Claude returns **`stop_reason: tool_use`** with `tool_use` blocks; we execute Python functions, append **`tool_result`** messages, and call the API again until **`end_turn`** or a max iteration cap.

**Depth:** Tool schemas are **`TOOL_DEFINITIONS`** with **`input_schema`** (`src/tools/github_tools.py`). **`TOOL_EXECUTOR`** dispatches by name. In **`BaseAgent._run_with_tools`**, we loop up to **5** times (`src/agents/base_agent.py`). The **`tools`** subcommand uses **`run_tool_agent_demo`** (`src/graph/tool_agent_workflow.py`) with the same branching on **`stop_reason`**, capped at **6** iterations for the demo.

### Walk through the agentic loop step by step.

**Answer:** User message → **create message** with tools → if **tool_use**, run each tool, push assistant content + user `tool_result` list → repeat → if **end_turn**, extract text and parse JSON (or finish).

**Depth:** We accumulate **`usage.input_tokens` / `output_tokens`** every hop for cost visibility. If the model never returns parseable JSON, **`_parse_json`** falls back to extracting the first `{...}` region or returns an empty structured error (`src/agents/base_agent.py`).

### Which prompt techniques did you use, and why do they help?

**Answer:** **Role prompting** steers expertise; **chain-of-thought** reduces shallow flags; **few-shot** locks JSON shape; **XML sections** separate concerns for Claude; **structured output** enables automation.

**Depth:** Implemented in **`src/prompts/system_prompts.py`**: `<role>` sets bias (security engineer vs performance engineer); “Think step by step” forces **trace-before-claim**; `<example>` pairs a tiny diff with golden JSON so the model **imitates keys and severity enums**; `<output_format>` says “ONLY valid JSON” to protect **`json.loads`** downstream.

### How do you handle hallucinations?

**Answer:** **Constrain** output format, **evaluate** against known bugs, and **supervise** to collapse duplicate noise—hallucination becomes measurable, not just anecdotal.

**Depth:** Specialists must cite **trigger/attack** scenarios and fixes; eval checks **expected types** vs **found types** with recall/precision (`src/evaluation/evaluator.py`). The supervisor is instructed to **dedupe** (`SUPERVISOR_PROMPT`). For false positives on clean code, the suite includes a **clean diff** test case.

### What is your cost optimization strategy?

**Answer:** **Haiku** model id, **`quick`** mode for one agent, smaller demo diffs, and **token accounting** per node so I can see which stage dominates.

**Depth:** `MODEL_NAME` is **`claude-haiku-4-5-20251001`** (`src/config.py`). **`_estimate_cost`** uses $1/M input and $5/M output assumptions (`src/agents/base_agent.py`). Production next steps: **cache** embeddings/summaries of unchanged files, **batch** hunks, or route trivial PRs to a single **security-only** path.

### How would you scale this?

**Answer:** **Parallelize** independent hunks or repos, **batch** API calls, add **caching** for file contents, and move from linear graph to **map-reduce** over files.

**Depth:** Today the graph is **sequential** (`src/graph/workflow.py`). For scale, fan out **per-file** reviewer nodes with a **reduce** supervisor; use **idempotent** tool results and **rate limiting** for GitHub; store **checkpoints** in LangGraph for long PRs. For org-wide rollout, queue PR webhooks and process asynchronously.

### How is this different from a thin GPT wrapper?

**Answer:** A wrapper sends one prompt; this is a **stateful workflow** with **typed multi-agent outputs**, **quantitative eval**, and **tool execution** against GitHub.

**Depth:** The wrapper pattern skips **orchestration**, **per-agent metrics**, and **merge logic**. Here, **`run_review`** is an explicit graph; **`cmd_eval`** proves behavior on **labeled** diffs; **`github_tools`** shows **closed-loop** tool use, not static text completion.

### How does the evaluation suite work?

**Answer:** For each curated diff, I run the **full pipeline**, then for each agent JSON I compare **expected issue types** to **found types** using substring overlap and compute **precision/recall**.

**Depth:** `TestCase` holds `expected_security`, `expected_logic`, `expected_performance` (`src/evaluation/evaluator.py`). `evaluate_agent_output` normalizes to lowercase and checks whether each expected string appears in any finding type. CLI marks **PASS** if **recall ≥ 0.8** (`src/main.py`).

### What is the supervisor pattern?

**Answer:** A **meta-agent** that doesn’t re-scan the diff but **merges** specialist JSON into **one** user-facing markdown report with **severity ordering** and **deduplication**.

**Depth:** `SupervisorAgent.merge_reports` dumps reports into `<agent_reports>` and uses **`SUPERVISOR_PROMPT`** (`src/agents/supervisor.py`, `src/prompts/system_prompts.py`). It outputs **markdown**, not JSON, because the consumer is a **human PR comment**.

### How do you handle JSON parsing failures?

**Answer:** Strip markdown fences, **`json.loads`**, then try **substring extraction** between first `{` and last `}`; if still failing, return a **structured empty result** with a truncated `_raw_response` for debugging.

**Depth:** Implemented in **`BaseAgent._parse_json`** (`src/agents/base_agent.py`). This keeps the **graph from crashing** and preserves partial telemetry.

### How does shared state work in LangGraph?

**Answer:** Each node receives the **current** `ReviewState` dict and returns **partial updates**; the framework merges according to field annotations—**replace** for strings, **add** for annotated lists.

**Depth:** `diff` is read by every specialist but not mutated; `reviews` and `agent_stats` **grow** via **`operator.add`** (`src/graph/workflow.py`). `final_report` is **overwritten** by the supervisor.

### What is `Annotated[list, operator.add]`?

**Answer:** It tells LangGraph to **concatenate** list updates from each node instead of replacing the entire list.

**Depth:** Without it, returning `{"reviews": [new]}` would **wipe** prior agents’ results. The annotation registers the **reducer** so three nodes each append exactly one review object.

### How does real PR review integrate with GitHub?

**Answer:** `cmd_pr` parses the URL, calls **`get_pr_diff`** with **`PyGithub`**, concatenates per-file **`patch`** strings, then invokes **`run_review`**.

**Depth:** `get_pr_diff` in **`src/tools/github_tools.py`** iterates `pr.get_files()` and joins patches. Comments use **`create_issue_comment`** in **`post_review_comment`** (demo mode logs `[DEMO]` without a token). The **`pr`** CLI requires **`GITHUB_TOKEN`** in `.env` or **`--token`** (`src/main.py`).

### What would you change for production?

**Answer:** Add **retries**, **observability** (OpenTelemetry / LangSmith), **secrets rotation**, **PR size limits**, **async workers**, **idempotent** posting, and **human approval** before comments.

**Depth:** Harden **`_parse_json`** with schema validation (**Pydantic**), version prompts, store **raw model outputs** for audit, use **GitHub Checks** or review API instead of only issue comments, and add **rate limiting** around **`messages.create`**.

### What security considerations did you account for?

**Answer:** **Tokens** live only in env vars; GitHub PAT never logs; API keys aren’t embedded in prompts; tool execution is **server-side** and **allow-listed** by name.

**Depth:** `.env` is gitignored (see `.env.example`). `post_review_comment` only runs with a real token; otherwise it **simulates** (`src/tools/github_tools.py`). Production needs **least-scope PATs**, **org-wide secret scanning**, and **backoff** on 403/429 from GitHub or Anthropic.

### Agents vs agentic AI — how do you draw the line?

**Answer:** A **single-shot** specialist is an “agent” in the loose sense; **agentic** means **multi-turn** planning with **tools** until the task completes.

**Depth:** Logic/security/performance nodes are **LLM agents** with **structured outputs** but **no tools** (`use_tools=False` in `src/agents/logic_agent.py` etc.). **`_run_with_tools`** and **`run_tool_agent_demo`** are **agentic** loops: the model **decides** when to fetch data or post comments based on intermediate observations.

---

## Quick command reference

| Command | Purpose |
|---------|---------|
| `python -m src.main` | Interactive menu |
| `python -m src.main quick` | One agent, small diff, low cost |
| `python -m src.main review` | Full graph, demo diff |
| `python -m src.main review -f FILE` | Full graph, file diff |
| `python -m src.main single {logic\|security\|performance}` | One specialist |
| `python -m src.main single AGENT -f FILE` | One specialist, file diff |
| `python -m src.main tools` | Tool-use loop demo |
| `python -m src.main eval` | Precision/recall suite |
| `python -m src.main pr URL` | Live GitHub PR (`--token` optional) |

---

## JD checklist mapping (example themes)

Use checkboxes in interviews verbally (“I can point to the file for each”).

| Theme | Evidence in repo |
|-------|------------------|
| Multi-step agent workflows | `src/graph/workflow.py`, `src/graph/tool_agent_workflow.py` |
| Reasoning / planning | CoT instructions in `src/prompts/system_prompts.py` |
| Orchestration framework | LangGraph `StateGraph`, `ReviewState` |
| Tool calling / function execution | `TOOL_DEFINITIONS`, `TOOL_EXECUTOR`, `_run_with_tools` |
| Structured output / parsing | JSON prompts, `_parse_json` in `src/agents/base_agent.py` |
| Evaluation / quality metrics | `src/evaluation/evaluator.py`, `cmd_eval` |
| Cost / performance awareness | Token usage + `_estimate_cost`, CLI stats table |
| External integration | `src/tools/github_tools.py`, `cmd_pr` |
| Production-minded discussion | Retries, validation, observability, scaling (verbal follow-ups) |

---

## Closing tip

When interviewers probe a weakness, **name the tradeoff you chose**: e.g. sequential graph for **clarity** over parallel for **latency**. That signals senior judgment and matches how this repository is intentionally **readable** first.
