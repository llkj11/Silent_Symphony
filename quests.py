"""Quest data + progression.

Quests are data-driven: each has an ordered list of steps, and each step has a
matcher dict describing the event that advances it. The engine calls `on_event`
at known trigger points (POI resolution, item acquisition, location entry, NPC
interaction, enemy slain) and this module decides what to start or advance.

Player state:
    player['quests'] = {
        quest_id: {"status": "active"|"completed", "step_index": int}
    }

Event matcher shape:
    {"event": "<event_type>", "<key>": "<required_value>", ...}
    All keys except "event" must equal-match the payload.
"""

import ai_context


QUEST_DB = {
    "echoes_of_the_wreck": {
        "id": "echoes_of_the_wreck",
        "name": "Echoes of the Wreck",
        "description": (
            "Driftwood and wreckage litter the shore. Find the story of the ship that ran aground — "
            "and what, or who, made it to land."
        ),
        "auto_start": {"event": "poi_resolved", "location_id": "beach_starting", "poi_id": "beach_log_markings"},
        "steps": [
            {
                "id": "open_chest",
                "text": "Open the barnacle-encrusted chest on Shifting Sands Beach.",
                "advance_on": {
                    "event": "poi_resolved",
                    "location_id": "beach_starting",
                    "poi_id": "beach_chest_barnacled",
                    "status": "looted",
                },
            },
            {
                "id": "recover_log",
                "text": "Recover the captain's log from the chest.",
                "advance_on": {"event": "item_obtained", "item_id": "captain_log_waterlogged"},
            },
            {
                "id": "find_survivors",
                "text": "Seek out other survivors along the coast.",
                "advance_on": {"event": "location_entered", "location_id": "survivor_camp"},
            },
            {
                "id": "speak_to_morwyn",
                "text": "Share what you found with Morwyn at the camp.",
                "advance_on": {"event": "npc_interacted", "npc_id": "morwyn_trader"},
                "requires_item": "captain_log_waterlogged",
            },
        ],
    },
    "markings_on_the_log": {
        "id": "markings_on_the_log",
        "name": "Markings on the Log",
        "description": (
            "The driftwood log's markings looked like a rough map. Follow their hints inland and see "
            "what the carver was trying to show."
        ),
        "auto_start": {
            "event": "poi_resolved",
            "location_id": "beach_starting",
            "poi_id": "beach_log_markings",
            "status": "read",
        },
        "steps": [
            {
                "id": "reach_dunes",
                "text": "Push inland toward the Coastal Dunes.",
                "advance_on": {"event": "location_entered", "location_id": "coastal_dunes_edge"},
            },
            {
                "id": "find_waypoint",
                "text": "Find a landmark in the dunes that matches the markings.",
                "advance_on": {
                    "event": "poi_resolved",
                    "location_id": "coastal_dunes_edge",
                    "poi_id": "dunes_skull",
                },
            },
        ],
    },
}


def _ensure(player):
    return player.setdefault("quests", {})


def quest_entry(player, quest_id):
    return _ensure(player).get(quest_id)


def status(player, quest_id):
    entry = quest_entry(player, quest_id)
    return entry.get("status") if entry else None


def is_active(player, quest_id):
    return status(player, quest_id) == "active"


def is_completed(player, quest_id):
    return status(player, quest_id) == "completed"


def active_quests(player):
    return [qid for qid, q in _ensure(player).items() if q.get("status") == "active"]


def completed_quests(player):
    return [qid for qid, q in _ensure(player).items() if q.get("status") == "completed"]


def current_step(player, quest_id):
    entry = quest_entry(player, quest_id)
    if not entry:
        return None
    quest = QUEST_DB.get(quest_id)
    if not quest:
        return None
    idx = entry.get("step_index", 0)
    steps = quest.get("steps", [])
    if 0 <= idx < len(steps):
        return steps[idx]
    return None


def start(player, quest_id):
    quests = _ensure(player)
    if quest_id in quests:
        return False
    quest = QUEST_DB.get(quest_id)
    if not quest:
        return False
    quests[quest_id] = {"status": "active", "step_index": 0}
    print(f"\n[Quest started: {quest['name']}]")
    first = current_step(player, quest_id)
    if first:
        print(f"  Objective: {first['text']}")
    ai_context.log_event(player, f"Started quest: {quest['name']}.", significance="significant")
    return True


def _advance(player, quest_id):
    entry = quest_entry(player, quest_id)
    quest = QUEST_DB.get(quest_id)
    if not entry or not quest:
        return
    entry["step_index"] = entry.get("step_index", 0) + 1
    steps = quest.get("steps", [])
    if entry["step_index"] >= len(steps):
        entry["status"] = "completed"
        print(f"\n[Quest completed: {quest['name']}]")
        ai_context.log_event(player, f"Completed quest: {quest['name']}.", significance="significant")
    else:
        nxt = steps[entry["step_index"]]
        print(f"\n[Quest updated — {quest['name']}]")
        print(f"  Objective: {nxt['text']}")
        ai_context.log_event(player, f"Advanced quest: {quest['name']} → {nxt['id']}.", significance="normal")


def _matches(matcher, event_type, payload):
    if not matcher or matcher.get("event") != event_type:
        return False
    for k, v in matcher.items():
        if k == "event":
            continue
        if payload.get(k) != v:
            return False
    return True


def on_event(player, event_type, **payload):
    """Dispatch a gameplay event to the quest system.

    Auto-starts quests whose `auto_start` matches, then advances any active
    quest whose current step's `advance_on` matches.
    """
    # Auto-start quests not yet seen.
    for qid, quest in QUEST_DB.items():
        if qid in _ensure(player):
            continue
        if _matches(quest.get("auto_start"), event_type, payload):
            start(player, qid)

    # Advance active quests.
    for qid in list(active_quests(player)):
        step = current_step(player, qid)
        if not step:
            continue
        if not _matches(step.get("advance_on"), event_type, payload):
            continue
        # Optional gate: step may require an item to be in inventory.
        needed = step.get("requires_item")
        if needed and needed not in player.get("inventory", []):
            continue
        _advance(player, qid)


def describe_quest(player, quest_id):
    """Return a multi-line string describing the quest's current state."""
    quest = QUEST_DB.get(quest_id)
    entry = quest_entry(player, quest_id)
    if not quest or not entry:
        return ""
    lines = [f"{quest['name']} — {entry['status']}"]
    lines.append(f"  {quest['description']}")
    steps = quest.get("steps", [])
    idx = entry.get("step_index", 0)
    for i, step in enumerate(steps):
        if i < idx or entry["status"] == "completed":
            marker = "[x]"
        elif i == idx:
            marker = "[~]"
        else:
            marker = "[ ]"
        lines.append(f"  {marker} {step['text']}")
    return "\n".join(lines)
