from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, Iterable, Optional

from agents.base_agent import AgentTurn
from .reward_engine import RewardEngine


class BudgetTracker:
    """Tracks usage against configured limits and raises on overflow."""

    def __init__(self, limits: Dict) -> None:
        self.limits = limits
        self.total_tokens = 0
        self.total_cost = 0.0
        self.start_time = time.monotonic()

    def register_turn(self, turn: AgentTurn) -> None:
        self.total_tokens += turn.tokens
        self.total_cost += turn.cost_usd

    def check_limits(self) -> Optional[str]:
        if self.total_tokens > self.limits.get("max_tokens_per_round", float("inf")):
            return "Token budget exceeded"
        if self.total_cost > self.limits.get("max_cost_usd", float("inf")):
            return "Cost budget exceeded"
        elapsed_minutes = (time.monotonic() - self.start_time) / 60
        if elapsed_minutes > self.limits.get("max_elapsed_minutes", float("inf")):
            return "Time budget exceeded"
        return None


class Coordinator:
    """Coordinates round-based collaboration between agents."""

    def __init__(
        self,
        base_dir: Path,
        agents: Dict[str, object],
        config: Dict,
        settings: Dict,
        limits: Dict,
        reward_engine: RewardEngine,
        logger: logging.Logger,
    ) -> None:
        self.base_dir = base_dir
        self.agents = agents
        self.config = config
        self.settings = settings
        self.limits = limits
        self.reward_engine = reward_engine
        self.logger = logger
        self.order = config.get("default_order", list(agents.keys()))
        self.log_dir = base_dir / settings.get("conversation_log_dir", "memory/logs")
        self.project_memory_path = base_dir / settings.get("project_memory_file", "memory/project_memory.md")
        self.output_path = base_dir / settings.get("output_file", "output/saved_outputs.md")

    # ------------------------------------------------------------------
    def run(self, rounds: int) -> None:
        for round_index in range(1, rounds + 1):
            self.logger.info("Starting round %s", round_index)
            budget = BudgetTracker(self.limits)
            round_context = self._initial_round_context(round_index)
            self._kickoff_round(round_context, budget)
            self._run_task_phase(round_context, budget)
            self._finalise_round(round_context, budget)
            self.logger.info("Completed round %s", round_index)

    # ------------------------------------------------------------------
    def _kickoff_round(self, context: Dict, budget: BudgetTracker) -> None:
        head_id = self.order[0]
        head_agent = self.agents[head_id]
        turn = head_agent.kickoff_round(context)
        self._persist_turn(turn, context)
        budget.register_turn(turn)
        self._check_budget(budget)
        context["conversation_summary"] = turn.content

    def _run_task_phase(self, context: Dict, budget: BudgetTracker) -> None:
        talk_back_cycles = self.settings.get("talk_back_cycles", 0)
        for cycle in range(talk_back_cycles):
            self.logger.debug("Talk-back cycle %s", cycle + 1)
            for agent_id in self._iter_task_agents():
                agent = self.agents[agent_id]
                turn = agent.perform_task(context)
                self._persist_turn(turn, context)
                budget.register_turn(turn)
                self._check_budget(budget)
                context["conversation_summary"] = self._update_summary(context, turn)
                self.reward_engine.record_contribution(agent_id, turn.content)

    def _finalise_round(self, context: Dict, budget: BudgetTracker) -> None:
        reviewer_id = self.order[0]
        reviewer = self.agents[reviewer_id]
        review_turn = reviewer.review_round(context)
        self._persist_turn(review_turn, context)
        budget.register_turn(review_turn)
        self._check_budget(budget)
        context["conversation_summary"] = self._update_summary(context, review_turn)
        self._append_round_summary(context)

    # ------------------------------------------------------------------
    def _persist_turn(self, turn: AgentTurn, context: Dict) -> None:
        log_path = self.log_dir / f"{turn.agent_id}_log.md"
        log_entry = self._format_log_entry(turn, context)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(log_entry + "\n\n")
        self.logger.debug("Logged turn for %s", turn.agent_id)

    def _format_log_entry(self, turn: AgentTurn, context: Dict) -> str:
        entry = {
            "agent": turn.agent_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tokens": turn.tokens,
            "cost": turn.cost_usd,
            "summary": context.get("conversation_summary", ""),
            "content": turn.content,
        }
        return json.dumps(entry, ensure_ascii=False, indent=2)

    def _check_budget(self, tracker: BudgetTracker) -> None:
        violation = tracker.check_limits()
        if violation:
            self.logger.error("%s -- initiating auto pause", violation)
            if self.limits.get("auto_pause", True):
                raise RuntimeError(violation)

    def _update_summary(self, context: Dict, turn: AgentTurn) -> str:
        summary = context.get("conversation_summary", "")
        updated = f"{summary}\n{turn.agent_id}: {turn.content.strip()}".strip()
        return updated

    def _append_round_summary(self, context: Dict) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n## Round Summary\n\n{context.get('conversation_summary', '').strip()}\n")

    def _initial_round_context(self, round_index: int) -> Dict:
        project_memory = ""
        if self.project_memory_path.exists():
            project_memory = self.project_memory_path.read_text(encoding="utf-8")
        return {
            "round": round_index,
            "objective": self.settings.get("round_objective", ""),
            "project_memory": project_memory,
            "conversation_summary": "",
        }

    def _iter_task_agents(self) -> Iterable[str]:
        if len(self.order) <= 1:
            return []
        return self.order
