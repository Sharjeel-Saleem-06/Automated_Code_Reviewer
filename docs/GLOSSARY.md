# Glossary — Multi-Agent Code Reviewer

Technical terms used throughout this project. Each entry ties terminology to concrete code locations.

---

## AI Agent

An autonomous software component that receives inputs (here, a unified diff), applies reasoning via a large language model, and returns structured outputs such as JSON findings. In this codebase, specialist agents inherit shared behavior from `BaseAgent` while specializing through distinct system prompts in `src/prompts/system_prompts.py` (`LogicAgent`, `SecurityAgent`, `PerformanceAgent` in `src/agents/`).

---

## Agentic AI

Systems where the model does not only answer once but can plan, call external capabilities (tools), observe results, and iterate until a goal is satisfied. This project demonstrates agentic behavior in `src/agents/base_agent.py` (`_run_with_tools`) and in the standalone demo loop in `src/graph/tool_agent_workflow.py`, where Claude may fetch a PR diff and post a comment across multiple API rounds.

---

## Multi-Agent System

An architecture where several agents with different roles collaborate toward a outcome richer than any single prompt. Here, three reviewers analyze the same diff sequentially, then a supervisor merges outputs; orchestration lives in `src/graph/workflow.py` (`StateGraph`, nodes `logic_agent` → `security_agent` → `performance_agent` → `supervisor`).

---

## LLM (Large Language Model)

A neural model trained to predict and generate text, used as the reasoning engine for each agent. All agent calls use Anthropic’s Claude family; the configured identifier is `MODEL_NAME` in `src/config.py` (`claude-haiku-4-5-20251001`).

---

## Claude

Anthropic’s family of LLMs. This project uses Claude Haiku 4.5 for cost-effective, fast reviews while preserving strong instruction-following for JSON and tool schemas. Model id and token limits are set in `src/config.py` (`MODEL_NAME`, `MAX_TOKENS_AGENT`, `MAX_TOKENS_SUPERVISOR`).

---

## Anthropic API

The HTTP API that sends prompts and optional tool definitions to Claude and returns assistant messages, usage metadata, and stop reasons. Wrapped by the `anthropic` Python SDK in `src/agents/base_agent.py` and `src/agents/supervisor.py` via `anthropic.Anthropic` and `client.messages.create`.

---

## LangGraph

A library for building stateful, multi-step graphs (often for agents and workflows) on top of LangChain-core primitives. This project compiles a review pipeline with `StateGraph` in `src/graph/workflow.py` (`from langgraph.graph import StateGraph, END`).

---

## StateGraph

A graph type in LangGraph where nodes read and update a typed state object. `build_review_graph()` in `src/graph/workflow.py` constructs a `StateGraph(ReviewState)` with four nodes and linear edges ending at `END`.

---

## Prompt Engineering

The practice of shaping instructions, format constraints, and examples so models produce reliable, parseable outputs. Centralized in `src/prompts/system_prompts.py` via `<role>`, `<task>`, `<rules>`, `<output_format>`, and `<example>` blocks for each agent.

---

## Role Prompting

Assigning an expert persona (“Principal Software Engineer,” “Senior Application Security Engineer”) to bias the model toward domain-appropriate reasoning. Defined in `LOGIC_AGENT_PROMPT`, `SECURITY_AGENT_PROMPT`, and `PERFORMANCE_AGENT_PROMPT` in `src/prompts/system_prompts.py`.

---

## XML Tags

Structured delimiters like `<diff>` and `<agent_reports>` that segment prompts for clarity and model parsing. Used when sending user content in `src/agents/base_agent.py` (diff wrapped in `<diff>`) and `src/agents/supervisor.py` (JSON reports wrapped in `<agent_reports>`).

---

## Chain-of-Thought (CoT)

Instructions that ask the model to reason step-by-step before concluding, improving traceability of conclusions. Each specialist prompt in `src/prompts/system_prompts.py` includes variants of “Think step by step” in `<rules>`.

---

## Few-Shot Prompting

Providing input/output examples in the prompt so the model mimics the desired format and depth. Each agent prompt in `src/prompts/system_prompts.py` includes an `<example>` with a miniature diff and matching JSON `output`.

---

## Structured Output

Requiring machine-parseable responses (here, JSON with fixed keys) instead of free-form prose for downstream code and evaluation. Specialist agents demand JSON-only replies in `<output_format>` in `src/prompts/system_prompts.py`; parsing is implemented in `BaseAgent._parse_json` in `src/agents/base_agent.py`.

---

## Tool Calling

The API feature where the model returns `tool_use` blocks naming functions and arguments; the host executes them and returns `tool_result` messages. Configured via `tools=TOOL_DEFINITIONS` in `src/agents/base_agent.py` and `src/graph/tool_agent_workflow.py`, with schemas defined in `src/tools/github_tools.py`.

---

## Function Execution

Running the Python implementations that back each tool name after the model requests a call. The dispatch map `TOOL_EXECUTOR` in `src/tools/github_tools.py` maps `get_pr_diff`, `get_pr_files`, and `post_review_comment` to real or demo implementations.

---

## Tokens

Units that measure input and output length for billing and context limits. Accumulated per agent in `BaseAgent.token_usage` and `SupervisorAgent.token_usage`, surfaced in CLI tables via `get_stats()` from `src/main.py` (`print_stats_table`).

---

## Cost Estimation

Approximate USD spend derived from token counts and published per-million-token rates. Implemented in `BaseAgent._estimate_cost` and `SupervisorAgent._estimate_cost` using Haiku-style $1/M input and $5/M output assumptions (`src/agents/base_agent.py`, `src/agents/supervisor.py`).

---

## Orchestration

Coordinating multiple steps and agents in a defined order with shared data. The LangGraph pipeline in `src/graph/workflow.py` (`run_review`, `build_review_graph`) orchestrates Logic → Security → Performance → Supervisor.

---

## Shared State

A single state object passed through graph nodes so each step can read prior results and append new data. `ReviewState` in `src/graph/workflow.py` holds `diff`, aggregated `reviews`, `final_report`, and `agent_stats`.

---

## Supervisor Pattern

A higher-level agent that does not redo specialist work but synthesizes, deduplicates, and formats their outputs. `SupervisorAgent.merge_reports` in `src/agents/supervisor.py` consumes the list of JSON reviews and returns one markdown PR comment per `SUPERVISOR_PROMPT`.

---

## System Prompt

Instructions sent separately from the user turn, defining behavior, constraints, and output format. Passed as `system=` to `messages.create` in `src/agents/base_agent.py` and `src/agents/supervisor.py`, sourced from `src/prompts/system_prompts.py`.

---

## Messages API

Anthropic’s chat-style interface (`client.messages.create`) accepting `model`, `system`, `messages`, optional `tools`, and returning `content`, `stop_reason`, and `usage`. Used throughout `src/agents/base_agent.py`, `src/agents/supervisor.py`, and `src/graph/tool_agent_workflow.py`.

---

## JSON Schema

A structured description of JSON shapes; here, tool `input_schema` objects in `TOOL_DEFINITIONS` (`src/tools/github_tools.py`) tell Claude the required parameters for each GitHub tool. Specialist outputs follow documented JSON shapes in prompts (conceptually schema-like) and are validated by parsing in code.

---

## Evaluation

Automated checking of agent outputs against known diffs and expected finding types. Implemented in `src/evaluation/evaluator.py` (`TEST_SUITE`, `evaluate_agent_output`, `print_eval_summary`), invoked from `src/main.py` (`cmd_eval`).

---

## Precision

The fraction of reported findings that match expected categories (approximated by type overlap in this suite). Computed in `evaluate_agent_output` in `src/evaluation/evaluator.py` when `found_lower` is non-empty.

---

## Recall

The fraction of expected issue types that appear in the agent’s findings (substring match between expected and found types). Computed in `evaluate_agent_output` in `src/evaluation/evaluator.py`; CLI treats recall ≥ 0.8 as pass in `src/main.py`.

---

## Git Diff

A textual representation of file changes (added lines prefixed with `+`, removed with `-`) produced by version control. Loaded from disk, demo fixtures, or GitHub in `src/main.py` (`load_diff`, `get_pr_diff`), then passed as `state["diff"]` in `src/graph/workflow.py`.

---

## Pull Request (PR)

A GitHub request to merge a branch, associated with reviewable patches. Real diffs are fetched in `src/tools/github_tools.py` (`get_pr_diff` via PyGithub), and the CLI accepts PR URLs in `src/main.py` (`cmd_pr`, `parse_pr_url`).

---

## Base Agent

The shared superclass implementing direct JSON calls, optional tool loops, JSON recovery, and stats. Defined in `src/agents/base_agent.py` (`class BaseAgent`); `LogicAgent`, `SecurityAgent`, and `PerformanceAgent` in `src/agents/*.py` subclass it with `use_tools=False` by default.

---

## Stop Reason

A field on the API response indicating why generation ended, e.g. `tool_use` (model wants to invoke tools) or `end_turn` (model finished the turn). Branched on in `src/agents/base_agent.py` (`_run_with_tools`) and `src/graph/tool_agent_workflow.py` to decide whether to execute tools or return text.

---

## Tool Use Loop

Repeated cycle: model returns tool calls → host executes → results appended to `messages` → next `messages.create` until `end_turn` or max iterations. Capped at 5 iterations in `src/agents/base_agent.py` (`for _ in range(5)`); the demo workflow in `src/graph/tool_agent_workflow.py` uses up to 6 iterations.

---

## ReviewState

The `TypedDict` describing LangGraph state fields: `diff`, list fields merged with `operator.add`, `final_report`, and `agent_stats`. Declared in `src/graph/workflow.py`.

---

## Annotated[list, operator.add]

A LangGraph typing pattern marking list fields that should merge by concatenation across nodes rather than overwrite. Applied to `reviews` and `agent_stats` in `ReviewState` inside `src/graph/workflow.py`.

---

## OWASP / CWE

Industry taxonomies for web risks and weakness IDs. Referenced in specialist instructions: the security prompt in `src/prompts/system_prompts.py` asks for OWASP Top 10 categories and CWE-style rigor in findings.

---

## PyGithub

Python client for the GitHub REST API, used when a valid `GITHUB_TOKEN` is set to fetch PR patches and post comments. Imported inside functions in `src/tools/github_tools.py` (`get_pr_diff`, `get_pr_files`, `post_review_comment`).

---

## Hallucination (mitigation context)

Fabricated issues or missed real ones; mitigated here by structured JSON requirements, evaluation against labeled diffs (`src/evaluation/evaluator.py`), and supervisor consolidation (`src/agents/supervisor.py`).

---

## Demo Mode (GitHub tools)

When no real token is configured, GitHub tools return synthetic diff and file lists and simulate comment posting. Implemented via token checks and `_get_demo_diff()` in `src/tools/github_tools.py`.
