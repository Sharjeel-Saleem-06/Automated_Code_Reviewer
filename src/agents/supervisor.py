"""
Supervisor Agent: Merges all specialist reports into a final PR review.

This agent does NOT review code directly — it synthesizes the outputs of
the 3 specialist agents into a unified, severity-ranked markdown report.

JD Coverage: "multi-step agent workflows, reasoning chains, memory handling"
"""
import json
import time
import anthropic

from ..config import ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS_SUPERVISOR
from ..prompts.system_prompts import SUPERVISOR_PROMPT


class SupervisorAgent:
    def __init__(self):
        self.name = "supervisor"
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.token_usage = {"input": 0, "output": 0}
        self.latency_ms = 0

    def merge_reports(self, agent_reports: list[dict]) -> str:
        """Take list of agent findings dicts, return unified markdown report."""
        start = time.time()

        reviews_json = json.dumps(agent_reports, indent=2)

        response = self.client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS_SUPERVISOR,
            system=SUPERVISOR_PROMPT,
            messages=[{
                "role": "user",
                "content": f"<agent_reports>\n{reviews_json}\n</agent_reports>"
            }]
        )

        self.token_usage["input"] += response.usage.input_tokens
        self.token_usage["output"] += response.usage.output_tokens
        self.latency_ms = int((time.time() - start) * 1000)

        return response.content[0].text

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
        input_cost = self.token_usage["input"] * 1.0 / 1_000_000
        output_cost = self.token_usage["output"] * 5.0 / 1_000_000
        return round(input_cost + output_cost, 6)
