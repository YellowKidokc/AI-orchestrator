from __future__ import annotations

import logging
from typing import Dict

from .base_agent import BaseAgent


class DeepSeekAgent(BaseAgent):
    """Implementation strategy and optimisation agent."""

    def __init__(self, config: Dict, prompt_library: Dict[str, str], logger: logging.Logger) -> None:
        super().__init__("deepseek", config, prompt_library, logger)
