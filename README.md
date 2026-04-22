# Silent Symphony

A Python text-RPG with AI-narrated exploration. Game logic decides the mechanical outcome of each player action; the AI narrates the result. Single-player, terminal UI.

## Setup

```bash
# 1. Create a virtualenv (Python 3.11+ recommended)
python3 -m venv gamerpg
./gamerpg/bin/pip install -r requirements.txt

# 2. Configure your AI provider
cp .env.example .env
# Edit .env and set OPENAI_API_KEY (or GOOGLE_API_KEY + AI_PROVIDER=GEMINI)

# 3. Run
./gamerpg/bin/python3 main.py
```

Without an API key the game still runs — AI narration silently falls back to generic text.

## Architecture

See [`AGENTS.md`](./AGENTS.md) for the architecture overview, file map, and contributor rules.

## Roadmap

See [`TODO.md`](./TODO.md) for the priority-ordered task backlog.
