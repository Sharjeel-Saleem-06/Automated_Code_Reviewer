from .base_agent import BaseAgent
from ..prompts.system_prompts import LOGIC_AGENT_PROMPT


class LogicAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="logic",
            system_prompt=LOGIC_AGENT_PROMPT,
            use_tools=False,
        )
