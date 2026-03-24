from .base_agent import BaseAgent
from ..prompts.system_prompts import PERFORMANCE_AGENT_PROMPT


class PerformanceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="performance",
            system_prompt=PERFORMANCE_AGENT_PROMPT,
            use_tools=False,
        )
