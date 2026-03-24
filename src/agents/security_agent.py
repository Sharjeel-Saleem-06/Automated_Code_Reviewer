from .base_agent import BaseAgent
from ..prompts.system_prompts import SECURITY_AGENT_PROMPT


class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="security",
            system_prompt=SECURITY_AGENT_PROMPT,
            use_tools=False,
        )
