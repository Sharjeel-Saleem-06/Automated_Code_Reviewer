"""
Multi-Agent Orchestration using LangGraph StateGraph.

Architecture:
  START → [Logic Agent] → [Security Agent] → [Performance Agent] → [Supervisor] → END

Each agent reads the shared state (diff), appends its findings,
and the Supervisor merges everything into a final review.

JD Coverage:
- "Multi-step agent workflows including reasoning chains, memory handling"
- "Architect multi-step agent workflows"
- Uses LangGraph (orchestration framework like LangChain)
"""
from typing import TypedDict, Annotated
import operator
import json

from langgraph.graph import StateGraph, END

from ..agents.logic_agent import LogicAgent
from ..agents.security_agent import SecurityAgent
from ..agents.performance_agent import PerformanceAgent
from ..agents.supervisor import SupervisorAgent


class ReviewState(TypedDict):
    """Shared state accessible by all agents in the graph."""
    diff: str
    reviews: Annotated[list, operator.add]
    final_report: str
    agent_stats: Annotated[list, operator.add]


_logic = LogicAgent()
_security = SecurityAgent()
_performance = PerformanceAgent()
_supervisor = SupervisorAgent()


def logic_node(state: ReviewState) -> dict:
    print("  [1/4] Logic Agent analyzing...")
    result = _logic.run(state["diff"])
    stats = _logic.get_stats()
    print(f"        Found {result.get('total_issues', len(result.get('findings', [])))} issue(s) "
          f"({stats['total_tokens']} tokens, ${stats['estimated_cost_usd']:.4f})")
    return {"reviews": [result], "agent_stats": [stats]}


def security_node(state: ReviewState) -> dict:
    print("  [2/4] Security Agent analyzing...")
    result = _security.run(state["diff"])
    stats = _security.get_stats()
    print(f"        Found {result.get('total_issues', len(result.get('findings', [])))} issue(s) "
          f"({stats['total_tokens']} tokens, ${stats['estimated_cost_usd']:.4f})")
    return {"reviews": [result], "agent_stats": [stats]}


def performance_node(state: ReviewState) -> dict:
    print("  [3/4] Performance Agent analyzing...")
    result = _performance.run(state["diff"])
    stats = _performance.get_stats()
    print(f"        Found {result.get('total_issues', len(result.get('findings', [])))} issue(s) "
          f"({stats['total_tokens']} tokens, ${stats['estimated_cost_usd']:.4f})")
    return {"reviews": [result], "agent_stats": [stats]}


def supervisor_node(state: ReviewState) -> dict:
    print("  [4/4] Supervisor merging reports...")
    report = _supervisor.merge_reports(state["reviews"])
    stats = _supervisor.get_stats()
    print(f"        Report generated ({stats['total_tokens']} tokens, ${stats['estimated_cost_usd']:.4f})")
    return {"final_report": report, "agent_stats": [stats]}


def build_review_graph() -> StateGraph:
    """Construct and compile the multi-agent review workflow."""
    graph = StateGraph(ReviewState)

    graph.add_node("logic_agent", logic_node)
    graph.add_node("security_agent", security_node)
    graph.add_node("performance_agent", performance_node)
    graph.add_node("supervisor", supervisor_node)

    graph.set_entry_point("logic_agent")
    graph.add_edge("logic_agent", "security_agent")
    graph.add_edge("security_agent", "performance_agent")
    graph.add_edge("performance_agent", "supervisor")
    graph.add_edge("supervisor", END)

    return graph.compile()


def run_review(diff: str) -> dict:
    """Main entry: run the full multi-agent review pipeline on a diff."""
    app = build_review_graph()

    result = app.invoke({
        "diff": diff,
        "reviews": [],
        "final_report": "",
        "agent_stats": [],
    })

    return result
