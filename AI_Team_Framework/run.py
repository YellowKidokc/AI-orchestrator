from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict

from agents.base_agent import load_prompt_library
from agents.claude_agent import ClaudeAgent
from agents.deepseek_agent import DeepSeekAgent
from agents.gemini_agent import GeminiAgent
from agents.gpt_agent import GPTAgent
from orchestrator.coordinator import Coordinator
from orchestrator.reward_engine import RewardEngine


AGENT_FACTORY = {
    "gemini": GeminiAgent,
    "claude": ClaudeAgent,
    "gpt": GPTAgent,
    "deepseek": DeepSeekAgent,
}


def configure_logging(level: str) -> logging.Logger:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("ai_orchestra")


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing configuration file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def initialise_agents(agent_config: Dict, prompt_library: Dict[str, str], logger: logging.Logger):
    agents = {}
    for spec in agent_config.get("agents", []):
        agent_id = spec["id"]
        factory = AGENT_FACTORY.get(agent_id)
        if not factory:
            logger.warning("No factory registered for agent '%s'", agent_id)
            continue
        agent_logger = logging.getLogger(f"ai_orchestra.agent.{agent_id}")
        agents[agent_id] = factory(spec, prompt_library, agent_logger)
    return agents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI Orchestra prototype")
    parser.add_argument("--base-dir", default=Path(__file__).resolve().parent, type=Path)
    parser.add_argument("--rounds", type=int, default=None, help="Override number of rounds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir: Path = args.base_dir

    settings = load_json(base_dir / "config" / "settings.json")
    limits = load_json(base_dir / "config" / "limits.json")
    agent_config = load_json(base_dir / "config" / "agents.json")

    logger = configure_logging(settings.get("log_level", "INFO"))
    logger.info("Initialising AI Orchestra from %s", base_dir)

    prompt_library = load_prompt_library(base_dir, settings)
    reward_engine = RewardEngine(base_dir, logger.getChild("rewards"))

    agents = initialise_agents(agent_config, prompt_library, logger)
    if not agents:
        raise RuntimeError("No agents could be initialised. Check config/agents.json")

    rounds = args.rounds or settings.get("rounds", 1)
    coordinator = Coordinator(
        base_dir=base_dir,
        agents=agents,
        config=agent_config,
        settings=settings,
        limits=limits,
        reward_engine=reward_engine,
        logger=logger.getChild("coordinator"),
    )

    try:
        coordinator.run(rounds=rounds)
    except RuntimeError as exc:
        logger.error("Run halted: %s", exc)


if __name__ == "__main__":
    main()
