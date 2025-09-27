from __future__ import annotations

import logging
from typing import Dict

from .base_agent import BaseAgent


class GPTAgent(BaseAgent):
    """Technical planning and specification agent."""

    def __init__(self, config: Dict, prompt_library: Dict[str, str], logger: logging.Logger) -> None:
        super().__init__("gpt", config, prompt_library, logger)
