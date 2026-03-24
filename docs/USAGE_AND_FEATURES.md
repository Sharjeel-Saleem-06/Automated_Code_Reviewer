# Usage and Features

Complete guide for running the Multi-Agent Code Reviewer locally, including every CLI mode, expected behavior, troubleshooting, and a concise interview demo script.

---

## Prerequisites

- **Python 3.10+** recommended (project tested with 3.13 in development).
- **Anthropic account** and API key ([Anthropic Console](https://console.anthropic.com)).
- **Internet access** for `pip install` and API calls.
- **GitHub Personal Access Token** (optional): required only for `pr` mode and for real tool execution against GitHub; see `src/tools/github_tools.py` and `.env.example`.

---

## Setup

### 1. Clone or open the project

```bash
cd "/path/to/Multi_Agent_Code_Reviewer"
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Core packages include `anthropic`, `python-dotenv`, `langgraph`, `langchain-core`, `PyGithub`, and `requests` (see `requirements.txt`).

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | **Yes** | Authenticates Claude via `src/config.py` |
| `GITHUB_TOKEN` | No* | Real PR fetch and comment posting; without it, GitHub tools use demo data |
| `PINECONE_*`, `LANGSMITH_*` | No | Reserved for future RAG / tracing (see `.env.example`) |

**Never commit `.env`.** Keys are read in `src/config.py` with `python-dotenv`.

### 5. Run from repository root

All commands use the package layout under `src/`:

```bash
python -m src.main <command> [options]
```

---

## CLI commands (7 modes)

The entry point is `src/main.py`. Subcommands are registered in `main()`; missing subcommand opens the **interactive** menu.

### 1. Interactive (default)

**Command:**

```bash
python -m src.main
```

**What happens:** Banner and menu with options `[1]` full review, `[2]` single agent, `[3]` tools demo, `[4]` eval, `[5]` quick, `[6]` real PR (prompts for URL/token), `[q]` quit.

**Expected output:** Prompts for input; then the same downstream output as the corresponding non-interactive command.

---

### 2. `quick` — fast, low-cost demo

**Command:**

```bash
python -m src.main quick
```

**What happens:** Runs **SecurityAgent** only on a **small inline diff** (hardcoded in `cmd_quick_demo` in `src/main.py`): SQLi-style query, hardcoded secret, MD5 password hashing.

**Expected output:**

- Header `QUICK DEMO — Security Agent`
- Model name (`claude-haiku-4-5-20251001` from `src/config.py`)
- Summary line and per-finding severity / type / truncated description
- Stats table: one row for `security` (tokens, latency, estimated USD)

**Use when:** You want a **cheap** live API call during a screen share.

---

### 3. `review` — full multi-agent pipeline

**Command (demo diff):**

```bash
python -m src.main review
```

**Command (file):**

```bash
python -m src.main review --file /path/to/changes.diff
# short form:
python -m src.main review -f /path/to/changes.diff
```

**What happens:** `run_review(diff)` executes Logic → Security → Performance → Supervisor (`src/graph/workflow.py`). Progress lines `[1/4]` … `[4/4]` print to stdout.

**Expected output:**

- `MULTI-AGENT CODE REVIEW` header, input description
- `FINAL REVIEW REPORT`: markdown from supervisor
- `Agent Performance Metrics` table: four rows (logic, security, performance, supervisor) + TOTAL
- `INDIVIDUAL AGENT FINDINGS (RAW JSON)`: condensed list per agent
- Total pipeline wall time in seconds

---

### 4. `single` — one specialist agent

**Command:**

```bash
python -m src.main single logic
python -m src.main single security
python -m src.main single performance
python -m src.main single security -f ./my.patch
```

**What happens:** Instantiates one `*Agent` from `src/agents/`, runs `agent.run(diff)` (`src/agents/base_agent.py`). Default diff is demo via `load_diff()`; `-f` loads a file.

**Expected output:**

- Header naming the agent
- Pretty-printed **JSON** result (`json.dumps(..., indent=2)`)
- Single-row stats table

**Errors:** Unknown agent name prints allowed choices: `logic`, `security`, `performance`.

---

### 5. `tools` — tool-calling demo loop

**Command:**

```bash
python -m src.main tools
```

**What happens:** `run_tool_agent_demo()` in `src/graph/tool_agent_workflow.py` asks Claude to review a **demo** PR (`acme/webapp#42`) using `get_pr_diff`, then `post_review_comment`, etc., with logged tool names/args.

**Expected output:**

- `TOOL-USE AGENT DEMO` header
- Step lines: `Claude calls tool 'get_pr_diff'` …
- Final step `Agent finished (end_turn)` when the model stops
- Summary: count of tool calls, iterations, total tokens

**Note:** Without a real `GITHUB_TOKEN`, tools still run but return **demo** diff and `[DEMO]` comment message (`src/tools/github_tools.py`).

---

### 6. `eval` — evaluation suite

**Command:**

```bash
python -m src.main eval
```

**What happens:** For each `TestCase` in `TEST_SUITE` (`src/evaluation/evaluator.py`), runs **full** `run_review(tc.diff)`, then `evaluate_agent_output` per agent review. Pass/fail icon uses recall ≥ 0.8.

**Expected output:**

- Per test: name, separator, lines like `[  ]` or `[XX]` per agent with found counts and expected types
- `EVALUATION SUMMARY`: tests run, passing count, average recall and precision

---

### 7. `pr` — real GitHub Pull Request by URL

**Command:**

```bash
python -m src.main pr "https://github.com/owner/repo/pull/123"
python -m src.main pr "https://github.com/owner/repo/pull/123" --token ghp_xxxx
```

**What happens:** `parse_pr_url` extracts owner/repo/number; `get_pr_diff` uses PyGithub when token is valid (`src/main.py`, `src/tools/github_tools.py`). Then same `run_review` as `review`.

**Expected output:**

- `LIVE GITHUB PR REVIEW` with repo and PR number
- Line count of fetched diff (or error / “No changes found”)
- Supervisor markdown report + stats table + link to PR

**Failure cases:** Invalid URL format; missing/placeholder token (message explains `.env` or `--token`); API errors surfaced as `Error fetching PR: ...`.

---

## Feature list

| Feature | Description |
|---------|-------------|
| **Multi-agent pipeline** | Three specialists plus supervisor on a shared diff (`src/graph/workflow.py`). |
| **LangGraph orchestration** | Typed state, reducers for append-only lists, linear `StateGraph`. |
| **Prompt engineering** | Role, CoT, few-shot, XML sections, JSON-only specialist outputs (`src/prompts/system_prompts.py`). |
| **Tool calling** | Anthropic tools + JSON schemas + Python executors (`src/tools/github_tools.py`, `base_agent.py`, `tool_agent_workflow.py`). |
| **Evaluation** | Labeled diffs, precision/recall by agent (`src/evaluation/evaluator.py`). |
| **Cost tracking** | Per-agent token counts and USD estimate (Haiku pricing assumptions in `base_agent.py` / `supervisor.py`). |
| **Real PR review** | Fetch unified diff from GitHub and run full pipeline (`src/main.py` `pr`, `get_pr_diff`). |
| **Demo-safe defaults** | Works without GitHub token using `_get_demo_diff()` and simulated tool results. |

---

## Troubleshooting

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| `401` / authentication errors from API | Bad or missing `ANTHROPIC_API_KEY` | Set key in `.env`, restart shell, confirm `load_dotenv()` runs (`src/config.py`). |
| `Invalid PR URL` | URL does not match `github.com/owner/repo/pull/N` | Fix format; include `https://`. |
| `GitHub token required` on `pr` | `GITHUB_TOKEN` unset or still placeholder | Set real PAT in `.env` or pass `--token`. |
| `Error fetching PR: ...` | Permissions, private repo, or network | Token needs `repo` scope for private repos; verify repo access. |
| Empty or stub diff | PR has no patchable files or API returned no `patch` | Try another PR; some file types lack patch text. |
| JSON parse fallback (`Failed to parse structured output`) | Model returned prose or malformed JSON | Retry; tighten temperature if you add API params; check prompt in `system_prompts.py`. |
| High latency / cost | Large diff + four model calls | Use `quick` or `single`; trim diff size; consider smaller model only if you change `MODEL_NAME`. |
| `ModuleNotFoundError: src` | Wrong working directory | Run from project root with `python -m src.main`. |
| LangGraph / import errors | Stale venv | Recreate venv, `pip install -r requirements.txt`. |

---

## Recommended demo flow (interviews)

1. **Show architecture in one sentence:** “Three specialist Claude agents over LangGraph, then a supervisor merges into one PR-style markdown report.”
2. **Run `quick`** (~seconds, low cost) to prove API wiring and security reasoning.
3. **Run `review`** on the built-in demo diff to show the full graph, stdout progress `[1/4]`…`[4/4]`, final markdown, and the **token/cost table**.
4. **Run `tools`** to narrate the **agentic loop**: model chooses `get_pr_diff`, you execute, model continues until `end_turn`.
5. **Mention `eval`** (run if time permits) to connect outputs to **precision/recall** on known vulnerabilities.
6. **Optional:** `pr` with a **public** small PR if token is available — demonstrates real-world integration.

This sequence moves from **cheap proof** → **full system** → **agentic tools** → **quality metrics** → **production-shaped input**, which mirrors how hiring panels often probe depth.
