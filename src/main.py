"""
Multi-Agent Code Reviewer — Main Entry Point

A production-grade multi-agent system where 3 specialized AI agents
(Logic, Security, Performance) review code changes from Pull Requests,
orchestrated via LangGraph with a Supervisor agent that merges findings.

Usage:
    python -m src.main                    # Interactive demo menu
    python -m src.main review             # Run full multi-agent review on sample diff
    python -m src.main review --file PATH # Review a specific diff file
    python -m src.main tools              # Demo tool-use agent loop
    python -m src.main eval               # Run evaluation suite
    python -m src.main single AGENT       # Run single agent (logic/security/performance)
"""
import sys
import os
import time
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import MODEL_NAME
from src.agents import LogicAgent, SecurityAgent, PerformanceAgent, SupervisorAgent
from src.graph.workflow import run_review
from src.graph.tool_agent_workflow import run_tool_agent_demo
from src.evaluation.evaluator import TEST_SUITE, evaluate_agent_output, print_eval_summary
from src.tools.github_tools import _get_demo_diff


BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ███████╗██╗   ██╗     ║
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔════╝██║   ██║     ║
║  ██║     ██║   ██║██║  ██║█████╗      ██████╔╝█████╗  ██║   ██║     ║
║  ██║     ██║   ██║██║  ██║██╔══╝      ██╔══██╗██╔══╝  ╚██╗ ██╔╝     ║
║  ╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║███████╗ ╚████╔╝      ║
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝       ║
║                                                                      ║
║          Multi-Agent Code Reviewer  [Powered by Claude]              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def print_header(title: str):
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_stats_table(stats_list: list[dict]):
    """Print a nice token/cost summary table."""
    print("\n  Agent Performance Metrics:")
    print("  " + "-" * 56)
    print(f"  {'Agent':<14} {'Tokens':>8} {'Latency':>10} {'Cost (USD)':>12}")
    print("  " + "-" * 56)
    total_tokens = 0
    total_cost = 0.0
    for s in stats_list:
        total_tokens += s["total_tokens"]
        total_cost += s["estimated_cost_usd"]
        print(f"  {s['agent']:<14} {s['total_tokens']:>8} {s['latency_ms']:>8}ms ${s['estimated_cost_usd']:>10.4f}")
    print("  " + "-" * 56)
    print(f"  {'TOTAL':<14} {total_tokens:>8} {'':>10} ${total_cost:>10.4f}")
    print(f"\n  Model: {MODEL_NAME}")


def load_diff(file_path: str = None) -> str:
    """Load a diff from file or return the demo diff."""
    if file_path:
        with open(file_path, "r") as f:
            return f.read()
    return _get_demo_diff()


def cmd_review(args):
    """Run the full multi-agent review pipeline."""
    print_header("MULTI-AGENT CODE REVIEW")
    print(f"\n  Mode: Full Pipeline (3 Agents + Supervisor)")
    print(f"  Model: {MODEL_NAME}")

    if args.file:
        print(f"  Input: {args.file}")
        diff = load_diff(args.file)
    else:
        print(f"  Input: Built-in demo diff (vulnerable Flask API)")
        diff = load_diff()

    print(f"\n  Starting review pipeline...\n")
    start = time.time()

    result = run_review(diff)

    elapsed = time.time() - start

    print_header("FINAL REVIEW REPORT")
    print()
    print(result["final_report"])

    print_stats_table(result["agent_stats"])
    print(f"\n  Total pipeline time: {elapsed:.1f}s")

    # Show individual agent findings summary
    print_header("INDIVIDUAL AGENT FINDINGS (RAW JSON)")
    for i, review in enumerate(result["reviews"]):
        agent = review.get("agent", f"agent_{i}")
        count = review.get("total_issues", len(review.get("findings", [])))
        print(f"\n  --- {agent.upper()} Agent: {count} issue(s) ---")
        for finding in review.get("findings", []):
            severity = finding.get("severity", "?")
            desc = finding.get("description", finding.get("vulnerability_type", finding.get("bug_type", "?")))
            icon = {"critical": "!!!", "high": "!! ", "medium": "!  ", "low": ".  "}.get(severity, "?  ")
            print(f"    [{icon}] {severity.upper()}: {desc[:80]}")


def cmd_single(args):
    """Run a single agent for focused demo."""
    agents = {
        "logic": LogicAgent,
        "security": SecurityAgent,
        "performance": PerformanceAgent,
    }

    if args.agent not in agents:
        print(f"  Unknown agent: {args.agent}. Choose from: {list(agents.keys())}")
        return

    print_header(f"SINGLE AGENT: {args.agent.upper()}")
    diff = load_diff(args.file if hasattr(args, 'file') and args.file else None)

    agent = agents[args.agent]()
    print(f"\n  Running {args.agent} agent...")
    result = agent.run(diff)
    stats = agent.get_stats()

    print(f"\n  Result:")
    print(json.dumps(result, indent=2))
    print_stats_table([stats])


def cmd_tools(args):
    """Demo the tool-use agent loop."""
    print_header("TOOL-USE AGENT DEMO")
    print(f"\n  Demonstrating Claude's Tool Calling capability")
    print(f"  Claude will: fetch PR diff -> analyze -> post comment\n")

    result = run_tool_agent_demo()

    print(f"\n  Tool calls made: {len(result['tool_calls'])}")
    for i, tc in enumerate(result["tool_calls"]):
        print(f"    {i+1}. {tc['tool']}({json.dumps(tc['args'])})")
    print(f"\n  Total iterations: {result['iterations']}")
    total = result["tokens"]["input"] + result["tokens"]["output"]
    print(f"  Tokens used: {total}")


def cmd_eval(args):
    """Run evaluation suite against known test cases."""
    print_header("EVALUATION SUITE")
    print(f"\n  Testing agents against {len(TEST_SUITE)} known test cases...")

    all_results = []

    for tc in TEST_SUITE:
        print(f"\n  Test: {tc.name}")
        print(f"  " + "-" * 40)

        result = run_review(tc.diff)

        for review in result.get("reviews", []):
            agent_name = review.get("agent", "unknown")
            eval_result = evaluate_agent_output(tc, agent_name, review)
            all_results.append(eval_result)

            status = "PASS" if eval_result.recall >= 0.8 else "FAIL"
            icon = "  " if status == "PASS" else "XX"
            print(f"    [{icon}] {agent_name}: found {eval_result.found_count} "
                  f"(expected types: {eval_result.expected_types})")

    print_eval_summary(all_results)


def cmd_interactive(args=None):
    """Interactive demo menu."""
    print(BANNER)
    print("  Choose a demo mode:\n")
    print("  [1] Full Multi-Agent Review  — 3 agents + supervisor analyze code")
    print("  [2] Single Agent             — Run one specialist agent")
    print("  [3] Tool-Use Demo            — Watch Claude call GitHub tools")
    print("  [4] Evaluation Suite         — Test agents against known vulnerabilities")
    print("  [5] Quick Demo (Recommended) — Fast review with summary stats")
    print("  [q] Quit\n")

    choice = input("  Enter choice (1-5, q): ").strip()

    if choice == "1":
        cmd_review(argparse.Namespace(file=None))
    elif choice == "2":
        agent = input("  Which agent? (logic/security/performance): ").strip()
        cmd_single(argparse.Namespace(agent=agent, file=None))
    elif choice == "3":
        cmd_tools(argparse.Namespace())
    elif choice == "4":
        cmd_eval(argparse.Namespace())
    elif choice == "5":
        cmd_quick_demo()
    elif choice == "q":
        print("  Goodbye!")
    else:
        print("  Invalid choice.")


def cmd_quick_demo():
    """Quick demo: run security agent on a small diff to minimize cost."""
    print_header("QUICK DEMO — Security Agent")
    print(f"  Model: {MODEL_NAME}")

    diff = """diff --git a/app.py b/app.py
+import sqlite3
+API_KEY = "sk-live-abc123"
+def get_user(name):
+    conn = sqlite3.connect('db.sqlite')
+    query = f"SELECT * FROM users WHERE name = '{name}'"
+    return conn.execute(query).fetchone()
+def hash_password(pw):
+    import hashlib
+    return hashlib.md5(pw.encode()).hexdigest()"""

    print(f"\n  Running security agent on small sample...\n")
    agent = SecurityAgent()
    result = agent.run(diff)
    stats = agent.get_stats()

    print(f"  Summary: {result.get('summary', 'N/A')}")
    print(f"  Issues found: {result.get('total_issues', len(result.get('findings', [])))}\n")
    for f in result.get("findings", []):
        sev = f.get("severity", "?").upper()
        vtype = f.get("vulnerability_type", "?")
        desc = f.get("description", "")
        print(f"  [{sev}] {vtype}")
        print(f"         {desc[:100]}")
        print()

    print_stats_table([stats])
    print(f"\n  This single call cost ~${stats['estimated_cost_usd']:.4f}")
    print(f"  With $5 credit, you can run ~{int(5.0 / max(stats['estimated_cost_usd'], 0.0001))} such calls")


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Code Reviewer")
    subparsers = parser.add_subparsers(dest="command")

    review_p = subparsers.add_parser("review", help="Run full multi-agent review")
    review_p.add_argument("--file", "-f", help="Path to a .diff file")

    single_p = subparsers.add_parser("single", help="Run a single agent")
    single_p.add_argument("agent", choices=["logic", "security", "performance"])
    single_p.add_argument("--file", "-f", help="Path to a .diff file")

    subparsers.add_parser("tools", help="Demo tool-use agent loop")
    subparsers.add_parser("eval", help="Run evaluation suite")
    subparsers.add_parser("quick", help="Quick cost-effective demo")

    args = parser.parse_args()

    if args.command == "review":
        cmd_review(args)
    elif args.command == "single":
        cmd_single(args)
    elif args.command == "tools":
        cmd_tools(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "quick":
        cmd_quick_demo()
    else:
        cmd_interactive()


if __name__ == "__main__":
    main()
