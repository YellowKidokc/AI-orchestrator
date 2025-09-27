from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AgentTurn:
    agent_id: str
    content: str
    cost_usd: float = 0.0
    tokens: int = 0


class BaseAgent:
    """Base class encapsulating common agent behaviour.

    The default implementation simply echoes structured placeholders so that
    the orchestration flow can be exercised without real model calls. Concrete
    subclasses can override :meth:`compose_turn` to integrate with an API or
    local model backend.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        prompt_library: Dict[str, str],
        logger: logging.Logger,
    ) -> None:
        self.agent_id = agent_id
        self.config = config
        self.prompt_library = prompt_library
        self.logger = logger

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def kickoff_round(self, context: Dict) -> AgentTurn:
        prompt = self._format_prompt("kickoff_prompt", context)
        return self.compose_turn(prompt, context)

    def perform_task(self, context: Dict) -> AgentTurn:
        prompt = self._format_prompt("task_prompt", context)
        return self.compose_turn(prompt, context)

    def self_evaluate(self, context: Dict) -> AgentTurn:
        prompt = self._format_prompt("self_eval_prompt", context)
        return self.compose_turn(prompt, context)

    def review_round(self, context: Dict) -> AgentTurn:
        prompt = self._format_prompt("review_prompt", context)
        return self.compose_turn(prompt, context)

    # ------------------------------------------------------------------
    # Extension hooks
    # ------------------------------------------------------------------
    def compose_turn(self, prompt: str, context: Optional[Dict]) -> AgentTurn:
        """Compose a response for a turn.

        Subclasses should override this method to connect with real LLM APIs.
        The default implementation simply returns a structured stub message so
        that the orchestration layer can be exercised in offline mode.
        """

        self.logger.debug("Stub compose_turn invoked for %s", self.agent_id)
        headline = self.config.get("role", "team member")
        response_lines: List[str] = [
            f"[{self.config.get('display_name', self.agent_id)} | {headline}]",
            "Prompt summary:",
            prompt.strip(),
        ]
        if context:
            summary = context.get("conversation_summary") or "(no summary yet)"
            response_lines.append(f"Latest summary: {summary}")
        return AgentTurn(agent_id=self.agent_id, content="\n".join(response_lines))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _format_prompt(self, prompt_key: str, context: Dict) -> str:
        template = self.prompt_library.get(prompt_key, "")
        if not template:
            self.logger.warning("Prompt '%s' missing for agent %s", prompt_key, self.agent_id)
            return ""

        populated = template.format(
            agent_name=self.config.get("display_name", self.agent_id),
            agent_role=self.config.get("role", ""),
            project_objective=context.get("objective", ""),
            project_memory=context.get("project_memory", ""),
        )
        return populated


def load_prompt_library(base_dir: Path, settings: Dict) -> Dict[str, str]:
    """Load prompt templates declared in the settings file."""

    prompt_map: Dict[str, str] = {}
    for key in [
        "kickoff_prompt",
        "task_prompt",
        "self_eval_prompt",
        "review_prompt",
    ]:
        path_value = settings.get(key)
        if not path_value:
            continue
        prompt_path = base_dir / path_value
        try:
            prompt_map[key] = prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            prompt_map[key] = ""
    return prompt_map
