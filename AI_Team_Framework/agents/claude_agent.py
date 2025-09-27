from __future__ import annotations

import logging
from typing import Dict

from .base_agent import BaseAgent


class ClaudeAgent(BaseAgent):
    """Research synthesis specialist agent."""

    def __init__(self, config: Dict, prompt_library: Dict[str, str], logger: logging.Logger) -> None:
        super().__init__("claude", config, prompt_library, logger)
