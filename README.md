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

## Quick Start

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add your ANTHROPIC_API_KEY

# Run
python -m src.main          # Interactive menu
python -m src.main quick    # Fast single-agent demo (~$0.004)
python -m src.main review   # Full 3-agent pipeline (~$0.04)
python -m src.main tools    # Tool calling demo
python -m src.main eval     # Evaluation suite
```

## Documentation

| Document | Description |
|----------|-------------|
| [INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md) | Project intro pitch, live demo script, Q&A for every JD qualification, command reference |
| [GLOSSARY.md](docs/GLOSSARY.md) | Every technical term explained — LLM, agent, tokens, LangGraph, prompt engineering, tool calling, and more |
| [HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) | Step-by-step walkthrough of the internal workflow mechanism |
| [USAGE_AND_FEATURES.md](docs/USAGE_AND_FEATURES.md) | How to run every mode, all features listed, and a recommended demo script |

## Project Structure

```
Multi_Agent_Code_Reviewer/
│
├── src/                           # Production source code
│   ├── main.py                    # CLI entry point (5 demo modes)
│   ├── config.py                  # Model, tokens, API key config
│   │
│   ├── agents/                    # Agent implementations
│   │   ├── base_agent.py          # Core engine: API calls, tool-use loop, JSON parsing
│   │   ├── logic_agent.py         # Agent 1: Logic bug detection
│   │   ├── security_agent.py      # Agent 2: Security vulnerability scanner
│   │   ├── performance_agent.py   # Agent 3: Performance issue detector
│   │   └── supervisor.py          # Supervisor: Merges all agent reports
│   │
│   ├── prompts/                   # Prompt engineering library
│   │   └── system_prompts.py      # Expert prompts (role, CoT, few-shot, XML, JSON schema)
│   │
│   ├── tools/                     # Tool calling / function execution
│   │   └── github_tools.py        # GitHub API tool schemas + dual-mode executors
│   │
│   ├── graph/                     # Multi-agent orchestration
│   │   ├── workflow.py            # LangGraph StateGraph (4-node pipeline)
│   │   └── tool_agent_workflow.py # Agentic loop with autonomous tool selection
│   │
│   └── evaluation/                # Testing & quality
│       └── evaluator.py           # Precision/recall metrics against known test cases
│
├── tests/
│   └── sample_diffs/              # Test data
│       ├── vulnerable_api.diff    # Intentionally vulnerable Flask API (10+ issues)
│       ├── mixed_issues.diff      # Mix of logic, security, and perf issues
│       └── clean_code.diff        # Clean code (tests for false positives)
│
├── tutorials/                     # Learning material
│   └── Phase1_Hello_Claude/       # Anthropic API basics (4 lessons)
│       ├── lesson1_first_message.py
│       ├── lesson2_system_prompts.py
│       ├── lesson3_conversation.py
│       ├── lesson4_structured_output.py
│       └── run_phase1.py
│
├── docs/                          # Documentation
│   ├── INTERVIEW_GUIDE.md         # Project pitch, demo script, Q&A
│   ├── GLOSSARY.md                # Technical terms reference
│   ├── HOW_IT_WORKS.md            # Workflow mechanism explained
│   ├── USAGE_AND_FEATURES.md      # Usage guide + feature list
│   └── reference/                 # Planning & research documents
│       └── job_description.txt
│
├── .env.example                   # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

## JD Coverage Map

This project covers every requirement from the Claude Specialist job description:

| JD Requirement | Implementation |
|---|---|
| Claude (Anthropic API) | `base_agent.py` — direct `client.messages.create()` calls |
| Prompt engineering (few-shot, CoT, role, structured) | `system_prompts.py` — 5 techniques per prompt |
| Multi-step agent workflows with reasoning chains | `graph/workflow.py` — LangGraph 4-node StateGraph |
| Memory handling | `ReviewState` shared state with append-only lists |
| Tool calling and function execution pipelines | `github_tools.py` + `tool_agent_workflow.py` |
| Structured outputs (JSON schemas) | Strict JSON schema in every prompt, `_parse_json()` robust parser |
| Integrate with APIs and enterprise systems | GitHub API (PyGithub) — real + simulated modes |
| Orchestration frameworks (LangChain) | LangGraph (part of LangChain ecosystem) |
| Testing and evaluation frameworks | `evaluator.py` — 4 test cases, precision/recall |
| Minimize hallucinations | Evaluation suite + strict schemas + clean code false-positive test |
| AI safety and guardrails | Iteration limits, cost tracking, structured output enforcement |
| Monitor agent performance in production | Per-agent token, latency, and cost metrics |
| Cost-performance trade-offs | Haiku (10x cheaper than Sonnet), per-call cost estimation |
| Document systems, workflows, and prompt libraries | `docs/` folder + `system_prompts.py` as a reusable library |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Claude Haiku 4.5 (Anthropic API) |
| Orchestration | LangGraph StateGraph |
| Language | Python 3.10+ |
| GitHub Integration | PyGithub |
| Configuration | python-dotenv |

## Cost

| Mode | Cost per run | Runs on $5 |
|------|-------------|------------|
| Quick demo | ~$0.004 | ~1,100 |
| Full pipeline | ~$0.04 | ~125 |
| Tool-use demo | ~$0.02 | ~250 |

## License

MIT
