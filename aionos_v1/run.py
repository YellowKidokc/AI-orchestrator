#!/usr/bin/env python3
"""Entry point for executing a single AionOS orchestration cycle."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
PROMPTS_DIR = BASE_DIR / "prompts"
LOGS_DIR = BASE_DIR / "logs"
PROJECTS_DIR = BASE_DIR / "projects"
REWARDS_DIR = BASE_DIR / "rewards"


@dataclass
class AgentProfile:
    """Represents static configuration for an agent."""

    key: str
    name: str
    role: str
    description: str
    privileges: List[str]
    voice: str

    @classmethod
    def from_config(cls, key: str, payload: Dict[str, object]) -> "AgentProfile":
        return cls(
            key=key,
            name=str(payload.get("name", key.title())),
            role=str(payload.get("role", "Agent")),
            description=str(payload.get("description", "")),
            privileges=list(payload.get("privileges", [])),
            voice=str(payload.get("voice", "")),
        )


def load_json(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read().strip()


def append_to_log(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def format_conversation_entry(agent: AgentProfile, message: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    header = f"[{timestamp}] {agent.name} ({agent.role}):"
    return f"{header}\n{message.strip()}\n\n"


def craft_orchestrator_message(agent: AgentProfile, context: str) -> str:
    return (
        f"Greetings team, this is {agent.name}. Our focus is the current project brief. "
        f"Here is the essential context we will work from:\n\n{context}\n\n"
        "Claude, please explore the orchestration workflow and identify the key stages. "
        "ChatGPT, prepare to refine Claude's findings into a crisp narrative."
    )


def craft_researcher_message(agent: AgentProfile, context: str) -> str:
    return (
        "Building from the provided context, I propose outlining the AionOS workflow in three phases: "
        "preparation, collaboration, and consolidation. In preparation, Gemini frames the problem and "
        "aligns expectations. During collaboration, Claude examines reference material and surfaces "
        "insights about agent roles, while ChatGPT distills them into actionable guidance. Consolidation "
        "captures Gemini's evaluation, updates performance scores, and archives logs for transparency."
    )


def craft_editor_message(agent: AgentProfile, researcher_message: str) -> str:
    return (
        "Summarizing Claude's exploration: AionOS cycles begin with Gemini setting intent, which keeps the "
        "crew aligned on context and deliverables. Claude then investigates the brief to surface the major "
        "concepts and opportunities. ChatGPT reformats those ideas into a structured overview that highlights "
        "workflow stages, evaluation mechanics, and the importance of persistent logs. This rhythm reinforces "
        "a culture of trust and measurable improvement."
    )


def rate_contribution(message: str) -> Dict[str, int]:
    word_count = len(message.split())
    efficiency = 5 if word_count <= 140 else 3
    insight = 5 if "workflow" in message.lower() else 3
    collaboration = 4
    trust_delta = 2 if insight >= 5 else 1
    return {
        "efficiency": efficiency,
        "insight": insight,
        "collaboration": collaboration,
        "trust_delta": trust_delta,
    }


def build_self_reflection(agent: AgentProfile, prompt: str, message: str) -> str:
    clarity_score = max(6, min(10, 10 - max(0, (len(message.split()) - 120) // 20)))
    usefulness_score = max(6, min(10, 7 + ("workflow" in message.lower()) + ("evaluation" in message.lower())))
    reflection = (
        f"{prompt}\n"
        f"Clarity: {clarity_score}/10\n"
        f"Usefulness: {usefulness_score}/10\n"
        f"Notes: As {agent.role}, I will iterate on brevity while preserving detail."
    )
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"## {timestamp}\n{reflection}\n\n"


def update_rewards(scores: Dict[str, Dict[str, int]], agent_key: str, deltas: Dict[str, int]) -> None:
    agent_scores = scores.setdefault(agent_key, {})
    agent_scores["efficiency"] = agent_scores.get("efficiency", 0) + deltas["efficiency"]
    agent_scores["insight"] = agent_scores.get("insight", 0) + deltas["insight"]
    agent_scores["collaboration"] = agent_scores.get("collaboration", 0) + deltas["collaboration"]
    agent_scores["tasks_completed"] = agent_scores.get("tasks_completed", 0) + 1
    trust = agent_scores.get("trust_score", 50) + deltas["trust_delta"]
    agent_scores["trust_score"] = max(0, min(100, trust))


def main() -> None:
    agents_config = load_json(CONFIG_DIR / "agents.json")
    agent_profiles = {
        key: AgentProfile.from_config(key, payload)
        for key, payload in agents_config.items()
    }

    context_path = PROJECTS_DIR / "sample_project" / "context.md"
    project_context = load_text(context_path)

    self_eval_prompt = load_text(PROMPTS_DIR / "self_eval_prompt.txt")

    conversation: List[str] = []

    # Gemini initiates
    gemini = agent_profiles["gemini"]
    gemini_message = craft_orchestrator_message(gemini, project_context)
    conversation.append(format_conversation_entry(gemini, gemini_message))

    # Claude responds
    claude = agent_profiles["claude"]
    claude_message = craft_researcher_message(claude, project_context)
    conversation.append(format_conversation_entry(claude, claude_message))

    # ChatGPT refines
    chatgpt = agent_profiles["chatgpt"]
    chatgpt_message = craft_editor_message(chatgpt, claude_message)
    conversation.append(format_conversation_entry(chatgpt, chatgpt_message))

    # Self evaluations
    claude_reflection = build_self_reflection(claude, self_eval_prompt, claude_message)
    append_to_log(LOGS_DIR / "claude_log.md", claude_reflection)

    chatgpt_reflection = build_self_reflection(chatgpt, self_eval_prompt, chatgpt_message)
    append_to_log(LOGS_DIR / "chatgpt_log.md", chatgpt_reflection)

    # Gemini finalizes
    final_summary = (
        "Thank you both. Claude spotlighted how preparation, collaboration, and consolidation define the "
        "cycle. ChatGPT distilled that into an accessible overview highlighting how evaluations and logs "
        "drive trust. I'll record this session and update performance metrics accordingly."
    )
    conversation.append(format_conversation_entry(gemini, final_summary))

    # Update rewards
    rewards_path = REWARDS_DIR / "agent_scores.json"
    rewards = load_json(rewards_path)
    for agent_key, message in (("claude", claude_message), ("chatgpt", chatgpt_message)):
        deltas = rate_contribution(message)
        update_rewards(rewards, agent_key, deltas)
    with rewards_path.open("w", encoding="utf-8") as handle:
        json.dump(rewards, handle, indent=2)

    # Persist conversation history
    session_log = "".join(conversation)
    divider = "# Session on " + datetime.now(timezone.utc).isoformat(timespec="seconds") + "\n"
    append_to_log(LOGS_DIR / "session_history.log", divider + session_log + "\n")

    # Present results to the terminal
    print("--- Conversation Transcript ---")
    print(session_log)
    print("Rewards updated for Claude and ChatGPT. Session complete.")


if __name__ == "__main__":
    main()
