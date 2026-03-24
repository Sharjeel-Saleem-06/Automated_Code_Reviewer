"""
Tool-Use Agent Workflow: Demonstrates Claude's tool calling capability.

This workflow shows the agentic loop where Claude:
1. Receives a request to review a PR
2. Calls get_pr_diff tool to fetch the code changes
3. Analyzes the diff
4. Calls post_review_comment to post findings

JD Coverage: "tool calling and function execution pipelines"
"""
import json
import anthropic

from ..config import ANTHROPIC_API_KEY, MODEL_NAME
from ..tools.github_tools import TOOL_DEFINITIONS, TOOL_EXECUTOR
from ..prompts.system_prompts import SECURITY_AGENT_PROMPT


TOOL_AGENT_SYSTEM = """You are a code review agent with access to GitHub tools.

When asked to review a Pull Request:
1. Use get_pr_diff to fetch the code changes
2. Analyze the diff for security vulnerabilities
3. Use post_review_comment to post your findings

Always think step by step. After fetching the diff, analyze it thoroughly
before posting your review.

For the review analysis, follow these rules:
""" + SECURITY_AGENT_PROMPT


def run_tool_agent_demo(owner: str = "acme", repo: str = "webapp", pr_number: int = 42):
    """Run the tool-use agent loop demonstration."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    messages = [{
        "role": "user",
        "content": (
            f"Review PR #{pr_number} in {owner}/{repo} for security vulnerabilities. "
            f"First fetch the diff, then analyze it, then post your findings as a review comment."
        )
    }]

    total_tokens = {"input": 0, "output": 0}
    tool_calls_log = []

    print("\n  Tool-Use Agent Loop Starting...\n")

    for iteration in range(6):
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=3000,
            system="You are a code review agent with GitHub tools. Fetch the PR diff, analyze it for security issues, then post a review comment.",
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        total_tokens["input"] += response.usage.input_tokens
        total_tokens["output"] += response.usage.output_tokens

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"    Step {iteration + 1}: Claude calls tool '{tool_name}'")
                    tool_calls_log.append({"tool": tool_name, "args": tool_input})

                    fn = TOOL_EXECUTOR.get(tool_name)
                    if fn:
                        result = fn(**tool_input)
                    else:
                        result = f"Unknown tool: {tool_name}"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
            print(f"    Step {iteration + 1}: Agent finished (end_turn)")
            return {
                "final_response": final_text,
                "tool_calls": tool_calls_log,
                "tokens": total_tokens,
                "iterations": iteration + 1
            }

    return {
        "final_response": "Agent did not complete within iteration limit",
        "tool_calls": tool_calls_log,
        "tokens": total_tokens,
        "iterations": 6
    }
