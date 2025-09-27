from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict


class RewardEngine:
    """Simple reward tracker persisting agent performance metrics."""

    def __init__(self, base_dir: Path, logger: logging.Logger) -> None:
        self.base_dir = base_dir
        self.logger = logger
        self.rewards_path = base_dir / "rewards" / "agent_scores.json"
        self.rewards_path.parent.mkdir(parents=True, exist_ok=True)
        self._scores = self._load_scores()

    # ------------------------------------------------------------------
    def record_contribution(self, agent_id: str, content: str) -> None:
        score_delta = self._score_from_content(content)
        entry = self._scores.setdefault(agent_id, {"score": 0, "last_updated": None})
        entry["score"] = entry.get("score", 0) + score_delta
        entry["last_updated"] = datetime.utcnow().isoformat()
        self._persist()
        self.logger.debug("Recorded contribution for %s (Δ=%s)", agent_id, score_delta)

    def get_scores(self) -> Dict[str, Dict]:
        return self._scores

    # ------------------------------------------------------------------
    def _score_from_content(self, content: str) -> int:
        """Naive heuristic: reward longer, structured contributions."""

        if not content:
            return 0
        lines = [line for line in content.splitlines() if line.strip()]
        return max(1, min(len(lines), 5))

    def _load_scores(self) -> Dict:
        if not self.rewards_path.exists():
            return {}
        try:
            return json.loads(self.rewards_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse rewards file; resetting.")
            return {}

    def _persist(self) -> None:
        with self.rewards_path.open("w", encoding="utf-8") as handle:
            json.dump(self._scores, handle, indent=2)
