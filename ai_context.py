"""Build rich context prefixes for AI prompts and maintain an event history.

The engine drives mechanics; the AI narrates. But narration that ignores the
player's state and recent history feels scripted. This module assembles a
compact briefing that the AI sees before every task prompt.
"""

import character
import world
import npcs


EVENT_HISTORY_CAP = 20
EVENTS_TO_INCLUDE = 6
SIGNIFICANCE_LEVELS = ("significant", "normal", "minor")


# Static system instruction for the AI. Never changes across calls, so it sits
# at the very head of the message list and benefits from provider-side prompt
# caching (OpenAI auto-caches ≥1024 tok prefixes; Gemini passes this as
# `system_instruction`).
SYSTEM_INSTRUCTION = (
    "You are the narrator for a text-based fantasy RPG called Silent Symphony. "
    "The game engine decides mechanical outcomes (items found, enemies spawned, clues revealed); "
    "your job is to wrap those outcomes in evocative, concise prose. "
    "You MUST respond by calling one of the provided function tools — never plain chat. "
    "Do not invent item_ids, enemy_ids, or NPC_ids; the engine supplies them when relevant. "
    "Keep narration to 1–3 short sentences unless the tool's schema suggests otherwise. "
    "Honor the player's character details, the location's traits, time of day, weather, "
    "and recent events shown in the CONTEXT block that follows."
)


def log_event(player, text, significance="normal"):
    """Append an event to the player's ring-buffer history.

    `significance`: 'significant' (combat outcomes, traps, flag changes),
    'normal' (POI resolutions, travel), or 'minor' (rest, idle).
    """
    if not text:
        return
    if significance not in SIGNIFICANCE_LEVELS:
        significance = "normal"
    history = player.setdefault("event_history", [])
    history.append({"text": text, "significance": significance})
    if len(history) > EVENT_HISTORY_CAP:
        del history[: len(history) - EVENT_HISTORY_CAP]


def recent_events(player, limit=EVENTS_TO_INCLUDE):
    """Return the most contextually useful events — prefers significant, fills with normal, then minor."""
    history = player.get("event_history", [])
    return _select_for_context(history, limit)


def _select_for_context(history, limit):
    if not history or limit <= 0:
        return []

    def sig(e):
        if isinstance(e, dict):
            return e.get("significance", "normal")
        return "normal"

    picked_indices = set()
    for required in SIGNIFICANCE_LEVELS:
        for i in range(len(history) - 1, -1, -1):
            if i in picked_indices:
                continue
            if sig(history[i]) == required:
                picked_indices.add(i)
                if len(picked_indices) >= limit:
                    break
        if len(picked_indices) >= limit:
            break

    return [history[i] for i in sorted(picked_indices)]


def build_context_prefix(player, current_location_id, locations_db, items_db):
    blocks = [
        _character_block(player, items_db),
        _location_block(player, current_location_id, locations_db),
        _recent_events_block(player),
    ]
    joined = "\n\n".join(b for b in blocks if b)
    if joined:
        return f"=== CONTEXT ===\n{joined}\n=== END CONTEXT ===\n\n"
    return ""


def _character_block(player, items_db):
    lines = ["# Character"]
    trait_suffix = f" ({player['race_trait']})" if player.get('race_trait') else ""
    lines.append(
        f"- {player.get('name','?')}, {player.get('race','?')}{trait_suffix} {player.get('origin','?')}, "
        f"sign of {player.get('star_sign','?')}. Level {player.get('level',1)}."
    )
    lines.append(
        f"- HP {player.get('health',0)}/{player.get('max_health',0)} | "
        f"Mana {player.get('mana',0)}/{player.get('max_mana',0)} | "
        f"Stamina {player.get('stamina',0)}/{player.get('max_stamina',0)}"
    )
    gear = _gear_summary(player, items_db)
    if gear:
        lines.append(f"- Gear: {gear}")
    if player.get("known_abilities"):
        lines.append(f"- Abilities: {', '.join(player['known_abilities'])}")
    if player.get("effects"):
        labels = []
        for e in player["effects"]:
            kind = e.get("kind", "?")
            turns = e.get("turns_remaining", 0)
            labels.append(f"{kind}({turns})")
        lines.append(f"- Active effects: {', '.join(labels)}")
    return "\n".join(lines)


def _gear_summary(player, items_db):
    parts = []
    weapon_id = player.get("equipped_weapon")
    if weapon_id and weapon_id in items_db:
        parts.append(f"weapon={items_db[weapon_id]['name']}")
    shield_id = player.get("equipped_shield")
    if shield_id and shield_id in items_db:
        parts.append(f"shield={items_db[shield_id]['name']}")
    for slot in character.ARMOR_SLOTS:
        iid = player.get(f"equipped_{slot}")
        if iid and iid in items_db:
            parts.append(f"{slot}={items_db[iid]['name']}")
    return ", ".join(parts)


def _location_block(player, location_id, locations_db):
    loc = locations_db.get(location_id, {})
    wloc = world.location(player, location_id)
    lines = ["# Location"]
    lines.append(f"- {loc.get('name', location_id)} (visit #{wloc.get('visits', 0)})")
    phase = world.current_phase(player)
    weather = world.current_weather(player, location_id, loc)
    lines.append(f"- Time: {phase} | Weather: {weather} | Turn {world.turn_counter(player)}")
    properties = loc.get("properties") or []
    if properties:
        lines.append(f"- Traits: {', '.join(properties)}")
    resolved = []
    for pid, pstate in wloc.get("pois", {}).items():
        resolved.append(f"{pid}:{pstate.get('status', '?')}")
    if resolved:
        lines.append(f"- Already resolved here: {', '.join(resolved)}")
    flags = wloc.get("flags") or {}
    if flags:
        flag_str = ", ".join(f"{k}={v}" for k, v in flags.items())
        lines.append(f"- Local flags: {flag_str}")
    global_flags = world.ensure(player).get("flags") or {}
    if global_flags:
        lines.append(f"- Global flags: {', '.join(k for k, v in global_flags.items() if v)}")
    present_npcs = npcs.npcs_at(location_id)
    if present_npcs:
        labels = [f"{n['id']} ({n.get('name','?')}, {n.get('role','?')})" for n in present_npcs]
        lines.append(f"- NPCs here: {', '.join(labels)}")
    return "\n".join(lines)


def _recent_events_block(player):
    history = recent_events(player)
    if not history:
        return ""
    lines = ["# Recent events (oldest → newest; ! = significant)"]
    for event in history:
        if isinstance(event, dict):
            text = event.get("text", "")
            marker = "!" if event.get("significance") == "significant" else "-"
        else:
            text = str(event)
            marker = "-"
        lines.append(f"{marker} {text}")
    return "\n".join(lines)
