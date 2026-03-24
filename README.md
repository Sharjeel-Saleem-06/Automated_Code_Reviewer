# Multi-Agent Code Reviewer

A production-grade **multi-agent AI system** that reviews Pull Request code changes using three specialized Claude-powered agents, orchestrated through a **LangGraph state machine** with a supervisor agent that merges all findings into a unified report.

## Architecture

```
                         ┌─────────────────┐
                         │   Code Diff      │
                         │   (PR Changes)   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
             ┌───────────┐ ┌───────────┐ ┌───────────┐
             │  Agent 1  │ │  Agent 2  │ │  Agent 3  │
             │   LOGIC   │ │ SECURITY  │ │   PERF    │
             │   BUGS    │ │   VULNS   │ │  ISSUES   │
             └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                   │             │             │
                   └─────────────┼─────────────┘
                                 ▼
                      ┌────────────────────┐
                      │    SUPERVISOR      │
                      │  (Merge & Rank)    │
                      └────────┬───────────┘
                               ▼
                      ┌────────────────────┐
                      │   Final Review     │
                      │   (Markdown PR     │
                      │    Comment)        │
                      └────────────────────┘
```

**Each agent** is a specialized AI persona powered by Claude, with expert-level system prompts using role prompting, few-shot examples, chain-of-thought reasoning, and strict JSON output schemas. The **Supervisor** agent reads all three reports and produces a unified, severity-ranked markdown review.

## Features

| Feature | Description |
|---------|-------------|
| **3 Specialist Agents** | Logic bugs, security vulnerabilities, performance issues |
| **LangGraph Orchestration** | State machine workflow with shared memory |
| **Tool Calling** | Claude autonomously calls GitHub API tools |
| **Structured Output** | Every agent returns strict JSON schemas |
| **Supervisor Agent** | Merges and de-duplicates findings across agents |
| **Evaluation Framework** | Test suite with precision/recall metrics |
| **Cost Tracking** | Per-agent token usage and USD cost estimation |
| **Demo + Production Modes** | Works with sample diffs or real GitHub PRs |

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/AISharjeel/Multi_Agent_Code_Reviewer.git
cd Multi_Agent_Code_Reviewer
python -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 3. Run

```bash
python -m src.main          # Interactive menu
python -m src.main quick    # Fast single-agent demo (~$0.004)
python -m src.main review   # Full 3-agent pipeline (~$0.04)
```

## Usage Modes

### Interactive Menu

```bash
python -m src.main
```

Presents a menu with all demo options. Best for live demonstrations.

### Full Multi-Agent Review

```bash
python -m src.main review                         # Uses built-in vulnerable demo code
python -m src.main review --file path/to/file.diff # Review a custom diff file
```

Runs all 3 agents sequentially through the LangGraph pipeline, then the Supervisor merges their reports into a final markdown review with severity-ranked findings.

### Single Agent

```bash
python -m src.main single security    # Run only the security agent
python -m src.main single logic       # Run only the logic agent
python -m src.main single performance # Run only the performance agent
```

### Tool-Use Demo

```bash
python -m src.main tools
```

Demonstrates Claude's **tool calling** capability. Claude autonomously decides to:
1. Call `get_pr_diff` to fetch code changes
2. Analyze the diff for vulnerabilities
3. Call `post_review_comment` to post findings

### Evaluation Suite

```bash
python -m src.main eval
```

Runs the full agent pipeline against 4 known test cases (SQL injection, hardcoded secrets, N+1 queries, clean code) and reports precision/recall metrics.

## Project Structure

```
Multi_Agent_Code_Reviewer/
├── src/
│   ├── main.py                    # CLI entry point with 5 demo modes
│   ├── config.py                  # Model selection, token limits, API keys
│   │
│   ├── agents/                    # Agent implementations
│   │   ├── base_agent.py          # Core agent with Anthropic API + tool-use loop
│   │   ├── logic_agent.py         # Agent 1: Logic bug detection
│   │   ├── security_agent.py      # Agent 2: Security vulnerability scanner
│   │   ├── performance_agent.py   # Agent 3: Performance issue detector
│   │   └── supervisor.py          # Supervisor: Merges all agent reports
│   │
│   ├── prompts/                   # Prompt engineering
│   │   └── system_prompts.py      # Expert system prompts (role, CoT, few-shot, XML)
│   │
│   ├── tools/                     # Tool calling / function execution
│   │   └── github_tools.py        # GitHub API tool schemas + executors
│   │
│   ├── graph/                     # Multi-agent orchestration
│   │   ├── workflow.py            # LangGraph StateGraph pipeline
│   │   └── tool_agent_workflow.py # Tool-use agent loop demonstration
│   │
│   └── evaluation/                # Testing & evaluation
│       └── evaluator.py           # Precision/recall metrics on known test cases
│
├── tests/
│   └── sample_diffs/              # Sample code diffs for testing
│       ├── vulnerable_api.diff    # Intentionally vulnerable Flask API
│       ├── mixed_issues.diff      # Mix of logic, security, and perf issues
│       └── clean_code.diff        # Clean code (tests for false positives)
│
├── Phase1_Hello_Claude/           # Learning phase: Anthropic API basics
│   ├── lesson1_first_message.py   # First API call
│   ├── lesson2_system_prompts.py  # System prompt techniques
│   ├── lesson3_conversation.py    # Multi-turn conversation
│   ├── lesson4_structured_output.py # JSON structured output
│   └── run_phase1.py              # Run all lessons sequentially
│
├── .env.example                   # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

## Technical Deep Dive

### Agent Design Pattern

Each agent follows the same pattern defined in `base_agent.py`:

```
Input (diff) → System Prompt → Claude API → JSON Response → Parsed Findings
```

The `BaseAgent` class provides:
- **Direct mode**: Send diff, get structured JSON response
- **Tool-use mode**: Agentic loop where Claude calls tools iteratively
- **Robust JSON parsing**: Handles markdown fences, extracts JSON from mixed text
- **Token tracking**: Records input/output tokens and estimates cost per call

### LangGraph State Machine

The workflow in `graph/workflow.py` defines a `StateGraph` with:

- **State**: `ReviewState` TypedDict with `diff`, `reviews` (append-only list), `final_report`, and `agent_stats`
- **Nodes**: Each agent is a graph node that reads `diff` from state and appends to `reviews`
- **Edges**: `logic_agent → security_agent → performance_agent → supervisor → END`
- **Shared Memory**: All agents share state via LangGraph's `Annotated[list, operator.add]` reducer

### Prompt Engineering Techniques

Every system prompt uses Claude-optimized techniques:

| Technique | How It's Used |
|-----------|--------------|
| **Role Prompting** | `<role>You are a Senior Security Engineer with 15 years...</role>` |
| **XML Tags** | `<role>`, `<task>`, `<rules>`, `<output_format>`, `<example>` |
| **Chain-of-Thought** | "Think step by step: trace through the code mentally" |
| **Few-Shot Examples** | Complete input/output example pairs in each prompt |
| **Structured Output** | Strict JSON schema definition with field descriptions |
| **Constraint Rules** | "ONLY flag real issues", "ONLY valid JSON, no markdown" |

### Tool Calling Pipeline

The tool-use demo (`graph/tool_agent_workflow.py`) implements the full agentic loop:

```
User Request → Claude → "I need to call get_pr_diff" → Execute tool →
Feed result back → Claude → "I need to call post_review_comment" → Execute →
Feed result back → Claude → Final text response (end_turn)
```

Tool definitions follow Anthropic's JSON schema format with `name`, `description`, and `input_schema`.

### Evaluation Framework

The evaluator (`evaluation/evaluator.py`) tests agents against known-vulnerable code:

- **4 test cases**: SQL injection, hardcoded secrets, N+1 queries, clean code
- **Metrics**: Precision (are the findings correct?) and Recall (did it find all issues?)
- **Pass threshold**: 80% recall

## Cost Analysis

Using **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`):

| Mode | Tokens | Cost | Runs per $5 |
|------|--------|------|-------------|
| Quick demo (1 agent) | ~1,700 | ~$0.004 | ~1,100 |
| Full pipeline (4 agents) | ~15,000 | ~$0.04 | ~125 |
| Tool-use demo | ~7,500 | ~$0.02 | ~250 |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Claude Haiku 4.5 (Anthropic API) |
| Orchestration | LangGraph (StateGraph) |
| Language | Python 3.10+ |
| GitHub Integration | PyGithub |
| Configuration | python-dotenv |

## License

MIT
