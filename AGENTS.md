# Silent Symphony — Agent Guide

> **This file is the canonical briefing for any AI agent (Claude, subagents, other tools) working in this repo.** Read this AND `TODO.md` before doing any work.

## What this project is

A Python text-RPG with AI-narrated exploration. Player explores locations, investigates points of interest (POIs), fights enemies, manages inventory. Single-player, terminal UI (uses `curses` for the inventory screen and menus).

## Core architecture

**Exploration is a two-stage flow (deliberate design, do not regress):**

1. **Game logic decides the mechanical outcome.** When the player picks a POI, code in `main.py` rolls against the POI definition (loot_container / loot_scatter / clue_object / navigation_hint / simple_description) and determines items found, enemies spawned, or clues revealed.
2. **AI narrates the game-determined outcome.** The engine then prompts the AI to call one of three function tools (`player_discovers_item`, `player_encounters_enemy`, `narrative_outcome`) with game-provided args. **The AI does not decide what happens — it only wraps flavor text around the engine's decision.**

Keep this separation. If you need the AI to influence outcomes, add a new function-call tool with a constrained surface area (see `ai_function_declarations.py`).

## File map

| File | Role |
|---|---|
| `main.py` | Game loop, POI resolution, AI response dispatch, NPC interaction flows |
| `character.py` | Character creation, XP, leveling, equipment slot helpers |
| `combat.py` | Turn-based combat loop, specials, abilities, XP/gold/loot awards |
| `locations.py` | `LOCATIONS`, `ENCOUNTER_GROUPS`, `POI_LOOT_TABLES` |
| `entities.py` | `ENEMY_TEMPLATES`, `SHARED_LOOT_GROUPS`, `get_enemy_instance` |
| `items.py` | `ITEM_DB` |
| `npcs.py` | `NPC_DB`, `npcs_at(location_id)`, pricing helpers |
| `effects.py` | Status effects, buffs, `apply_item_effect`, per-turn ticks |
| `abilities.py` | Player ability registry, star-sign → starting ability map |
| `enemy_specials.py` | Enemy special-attack handlers (poison_bite, slam_stun, etc.) |
| `world.py` | World state helpers (per-POI status, visit counts, flags, slain uniques) |
| `ai_context.py` | Prompt context builder + event history log |
| `ai_utils.py` | Provider-agnostic `get_ai_model_response` (Gemini + OpenAI) |
| `ai_function_declarations.py` | AI function-calling schemas |
| `config.py` | AI provider setup, env loading, model IDs, schema conversion |
| `ui.py` | Curses-based menus and inventory screen |
| `saveload.py` | JSON save/load with `migrate_player` for legacy saves |
| `game_data.py` | Static lists (races, origins, star signs) |

### NPC-as-POI pattern

NPCs live in `npcs.NPC_DB` keyed by location. At exploration time, `_npc_pois_for(location_id)` builds ephemeral POI entries and PREPENDS them to the presented POI list. They are always visible (never filtered by world_state) and short-circuit to `_interact_with_npc` on selection rather than invoking the Stage-3 AI. Role-specific sub-flows (`_merchant_loop`, future `_healer_loop`, etc.) dispatch from there.

## Running the game

```bash
# venv lives at ./gamerpg (git-ignored)
./gamerpg/bin/python3 main.py
```

Requires `.env` with `OPENAI_API_KEY` (or `GOOGLE_API_KEY`) and `AI_PROVIDER=OPENAI|GEMINI`. Without keys the game still runs; AI narration falls back to generic text.

Deps: `python-dotenv openai google-genai`. There's no `requirements.txt` yet (on TODO).

## Rules of engagement for agents

1. **Always read `TODO.md` first.** Pick tasks from there rather than inventing new work. If you propose new work, add it to `TODO.md` in the right priority tier.
2. **Check tasks off in `TODO.md` as you complete them.** Use `[x]` for done, `[~]` for in-progress, `[?]` for proposed/needs-discussion. Delete tasks that become obsolete. Add a 1-line note under a task if the implementation deviated from the original plan.
3. **Preserve the two-stage exploration flow.** Do not let the AI decide item/enemy IDs. The engine decides; the AI narrates.
4. **Item effects, status effects, abilities, and character traits must be data-driven.** Add fields to existing dicts in `items.py` / `entities.py` / `game_data.py` rather than hardcoding behavior per ID in `main.py` or `combat.py`.
5. **Respect existing save files.** `saveload.py` uses JSON. If you add new player fields, add migration in `saveload.load_game_state` so old saves still load (default missing keys).
6. **Watch for test leftovers.** The codebase has forced-debug paths (e.g. `elif True:`, `trapped_chance: 1.0`) left over from development. When you touch a system, check for them and clean up.
7. **Don't add comments that restate the code.** Only comment non-obvious *why* (hidden constraints, subtle invariants).
8. **No feature flags or backwards-compat shims.** This is a solo hobby project — just change the code.

## Known issues & footguns

- `character.py:20` has a typo (`['level' -1]`) that crashes on first level-up. Fix before touching anything leveling-related.
- `locations.py` has `trapped_chance: 1.0` left in for testing.
- `main.py` has `elif True:` forcing an enemy encounter on "look around generally."
- `ai_utils.py` has a dead `get_ai_description` function referencing a no-longer-existent `global_generation_config`.
- The AI provider in `config.py` is hardcoded to `"OPENAI"` despite a commented-out `os.getenv` fallback — flip as needed.
- Combat reads **very few** fields from items/enemies. Lots of scaffolding (`magic_bonus`, `special_attack`, `effect`, `slot`, `reach`, etc.) is defined in data but never consumed. Assume a field is unused unless you can grep for its read site.

## Saving memory (for Claude)

When you learn something non-obvious about this project — a user preference, a design decision, a recurring pitfall — save it via the auto-memory system so future sessions don't relearn it.

## Sister file

`CLAUDE.md` is a short pointer to this file for Claude Code's auto-loading. Keep both in sync — update this file as the source of truth.
