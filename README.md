# Logos-Coherent Multi-Agent AI Orchestra

This repository contains a runnable prototype for David Lowe's **Project Symphony**. The goal is to provide a coherent, turn-based coordination layer that enables several foundation models (Gemini, Claude, GPT, DeepSeek) to collaborate politely while respecting budget, time, and governance constraints.

The prototype currently ships with the API-based approach described by the Architect. It emphasises clear structure, configuration-driven behaviour, and safe extension points for future API calls or browser-automation integrations.

## Folder Structure

```
AI_Team_Framework/
├── run.py
├── agents/
│   ├── base_agent.py
│   ├── claude_agent.py
│   ├── deepseek_agent.py
│   ├── gemini_agent.py
│   └── gpt_agent.py
├── orchestrator/
│   ├── __init__.py
│   ├── coordinator.py
│   └── reward_engine.py
├── memory/
│   ├── project_memory.md
│   └── logs/
│       ├── claude_log.md
│       ├── deepseek_log.md
│       ├── gemini_log.md
│       └── gpt_log.md
├── prompts/
│   ├── round_kickoff_prompt.txt
│   ├── review_prompt.txt
│   ├── self_eval_prompt.txt
│   └── task_prompt.txt
├── config/
│   ├── agents.json
│   ├── limits.json
│   └── settings.json
├── rewards/
│   └── agent_scores.json
└── output/
    └── saved_outputs.md
```

Each directory is intentionally human-readable and editable, making it simple to adapt the orchestration behaviour without modifying Python code.

## Quick Start

1. **Install dependencies** (Python 3.9+ is required). The current prototype only uses the standard library, but virtualenv management is recommended for future API client installations.

   ```bash
   cd AI_Team_Framework
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt  # optional; create when adding dependencies
   ```

2. **Provide API keys** (future use). Create a `.env` file in `AI_Team_Framework/` with entries such as `OPENAI_API_KEY=...`, `ANTHROPIC_API_KEY=...`, etc. The stub agent implementations do not yet call external services, but the structure is ready for those integrations.

3. **Run a coordination round**:

   ```bash
   python run.py
   ```

   Use `--rounds N` to run multiple rounds or `--base-dir` to point at a different project directory.

4. **Inspect the results**:
   * `memory/logs/<agent>_log.md` – JSON-formatted entries for each turn.
   * `rewards/agent_scores.json` – evolving performance scores.
   * `output/saved_outputs.md` – round summaries suitable for canonisation.

## Configuration

- `config/agents.json` – Declares available agents, their model providers, and privilege levels. Add additional metadata (e.g., budgeting rules, orchestration weights) as needed.
- `config/settings.json` – Controls the rhythm of the conversation (round count, talk-back cycles, prompt paths, logging level).
- `config/limits.json` – Defines strict caps on tokens, cost, and elapsed time. When a limit is exceeded the run halts automatically.

All configuration files are editable while the system is offline. The coordinator re-reads them on startup.

## Extending the Prototype

- **API Integration** – Override `BaseAgent.compose_turn` within the concrete agent classes to call real APIs. The `AgentTurn` dataclass already carries token and cost metadata for budget enforcement.
- **Browser Automation Mode** – Implement an alternative agent subclass that drives browsers via Playwright/Selenium. The current coordinator can host both API and browser-driven agents simultaneously.
- **Private Side-Chats** – Extend `Coordinator` with a method that spins up 1-on-1 contexts, reusing the existing logging and budgeting tools.
- **Reward Policies** – Adjust `RewardEngine._score_from_content` to incorporate rubric-based scoring, human feedback, or automated evaluation metrics.

## Safety & Governance

- **Budget Guardrails** – `BudgetTracker` halts execution when limits are breached (tokens, cost, or wall-clock time).
- **Logging & Transparency** – Every agent contribution is persisted alongside a timestamp and the latest conversation summary for post-run auditing.
- **Role Rotation** – Update `default_order` in `config/agents.json` to rotate the Head AI and control speaking order. Future enhancements can derive the order dynamically from reward scores.

## Next Steps

- Connect each agent to the respective API clients and populate `.env` handling.
- Implement private manager-agent conversations and approval workflows for privileged actions.
- Build the browser automation alternative for environments where API usage is cost-prohibitive.
- Replace the stub scoring heuristic with a rubric informed by canon integration decisions.

The current code base is intentionally lightweight yet opinionated, providing the scaffolding required to conduct structured multi-agent collaboration in alignment with the Architect's ethos.
