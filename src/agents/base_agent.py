"""
Base agent with Anthropic tool-use loop.

This implements the core agentic pattern:
  User message → Claude thinks → Claude requests tool → Execute tool →
  Feed result back → Claude continues → ... → Final answer

JD Coverage: "multi-step agent workflows", "tool calling and function execution pipelines"
"""
import json
import time
from typing import Optional
import anthropic

from ..config import ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS_AGENT
from ..tools.github_tools import TOOL_DEFINITIONS, TOOL_EXECUTOR


class BaseAgent:
    def __init__(self, name: str, system_prompt: str, use_tools: bool = False):
        self.name = name
        self.system_prompt = system_prompt
        self.use_tools = use_tools
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.token_usage = {"input": 0, "output": 0}
        self.latency_ms = 0

    def run(self, diff: str) -> dict:
        """Execute the agent on a code diff and return structured findings."""
        start = time.time()

        if self.use_tools:
            result = self._run_with_tools(diff)
        else:
            result = self._run_direct(diff)

        self.latency_ms = int((time.time() - start) * 1000)
        return result

    def _run_direct(self, diff: str) -> dict:
        """Simple mode: send diff, get JSON response."""
        response = self.client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS_AGENT,
            system=self.system_prompt,
            messages=[{"role": "user", "content": f"<diff>\n{diff}\n</diff>"}]
        )

        self.token_usage["input"] += response.usage.input_tokens
        self.token_usage["output"] += response.usage.output_tokens

        raw = response.content[0].text
        return self._parse_json(raw)

    def _run_with_tools(self, user_message: str) -> dict:
        """Agentic loop: Claude can call tools iteratively until done."""
        messages = [{"role": "user", "content": user_message}]

        for _ in range(5):  # max 5 tool-use iterations to prevent runaway
            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS_AGENT,
                system=self.system_prompt,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            self.token_usage["input"] += response.usage.input_tokens
            self.token_usage["output"] += response.usage.output_tokens

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        fn = TOOL_EXECUTOR.get(block.name)
                        if fn:
                            result = fn(**block.input)
                        else:
                            result = f"Unknown tool: {block.name}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return self._parse_json(block.text)
                break

        return {"agent": self.name, "summary": "Agent completed without structured output", "findings": [], "total_issues": 0}

    def _parse_json(self, raw: str) -> dict:
        """Robustly parse JSON from Claude's response."""
        text = raw.strip()

        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

            return {
                "agent": self.name,
                "summary": "Failed to parse structured output",
                "findings": [],
                "total_issues": 0,
                "_raw_response": text[:500]
            }

    def get_stats(self) -> dict:
        return {
            "agent": self.name,
            "model": MODEL_NAME,
            "input_tokens": self.token_usage["input"],
            "output_tokens": self.token_usage["output"],
            "total_tokens": self.token_usage["input"] + self.token_usage["output"],
            "latency_ms": self.latency_ms,
            "estimated_cost_usd": self._estimate_cost()
        }

    def _estimate_cost(self) -> float:
        # Claude Haiku 4.5 pricing: $1/MTok input, $5/MTok output
        input_cost = self.token_usage["input"] * 1.0 / 1_000_000
        output_cost = self.token_usage["output"] * 5.0 / 1_000_000
        return round(input_cost + output_cost, 6)
