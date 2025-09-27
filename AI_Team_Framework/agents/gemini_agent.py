from __future__ import annotations

import logging
from typing import Dict

from .base_agent import BaseAgent


class GeminiAgent(BaseAgent):
    """Default implementation for the Gemini head orchestrator."""

    def __init__(self, config: Dict, prompt_library: Dict[str, str], logger: logging.Logger) -> None:
        super().__init__("gemini", config, prompt_library, logger)
