"""Contextual events that can fire while moving between locations.

These are engine-determined mini outcomes: the event, loot, damage, or ambush is
chosen here; AI narration can still color the destination description separately.
"""

import random

import items
import locations
import world


BASE_EVENT_CHANCE = 0.35
RECENT_EVENT_WINDOW = 3


def _props(location_id):
    return set(locations.LOCATIONS.get(location_id, {}).get("properties", []))


def _is_safe(location_id):
    return bool(locations.LOCATIONS.get(location_id, {}).get("safe"))


def _is_coastal(from_location_id, to_location_id):
    return "coastal" in (_props(from_location_id) | _props(to_location_id))


def _has_any_property(from_location_id, to_location_id, props):
    return bool((_props(from_location_id) | _props(to_location_id)) & set(props))


def _weather(player, location_id):
    loc = locations.LOCATIONS.get(location_id, {})
    return world.current_weather(player, location_id, loc)


def _low_health(player):
    max_health = max(1, player.get("max_health", 1))
    return player.get("health", max_health) / max_health <= 0.4


def _recently_seen(player, event_id):
    flags = world.ensure(player).setdefault("flags", {})
    last_turn = flags.get(f"travel_event_seen_{event_id}")
    if last_turn is None:
        return False
    return world.turn_counter(player) - last_turn <= RECENT_EVENT_WINDOW


def _mark_seen(player, event_id):
    world.ensure(player).setdefault("flags", {})[f"travel_event_seen_{event_id}"] = world.turn_counter(player)


def _weighted_choice(candidates):
    total = sum(max(0, event["weight"]) for event in candidates)
    if total <= 0:
        return None
    pick = random.uniform(0, total)
    running = 0
    for event in candidates:
        running += max(0, event["weight"])
        if pick <= running:
            return event
    return candidates[-1] if candidates else None


def _valid_item_ids(item_ids):
    return [item_id for item_id in item_ids if item_id in items.ITEM_DB]


def _washed_up_cache(player, from_location_id, to_location_id, get_enemy_for_location):
    pool = _valid_item_ids(["rope_hempen_10ft", "ration_pack_basic", "broken_shell", "rusted_nail"])
    item_id = random.choice(pool) if pool else None
    return {
        "id": "washed_up_cache",
        "narrative": "The tide has thrown fresh wreckage across your path. Among the splinters, something useful has snagged in a twist of kelp.",
        "items": [item_id] if item_id else [],
        "significance": "normal",
    }


def _sudden_squall(player, from_location_id, to_location_id, get_enemy_for_location):
    damage = random.randint(1, 3)
    return {
        "id": "sudden_squall",
        "narrative": "A hard squall slams in from the water. Grit and spray blind you long enough for the rocks to punish a careless step.",
        "damage": damage,
        "significance": "normal",
    }


def _dune_tracks(player, from_location_id, to_location_id, get_enemy_for_location):
    pool = _valid_item_ids(["flint_sharp", "berries_wild", "bone_fragment"])
    item_id = random.choice(pool) if pool else None
    return {
        "id": "dune_tracks",
        "narrative": "You spot a line of shallow tracks crossing the sand. Following them a short way turns up a small find tucked against a wind-cut ridge.",
        "items": [item_id] if item_id else [],
        "significance": "normal",
    }


def _night_ambush(player, from_location_id, to_location_id, get_enemy_for_location):
    enemy_id = get_enemy_for_location(to_location_id, player=player)
    if not enemy_id:
        return None
    return {
        "id": "night_ambush",
        "narrative": "The dim light hides movement until it is almost on top of you.",
        "enemy_id": enemy_id,
        "significance": "significant",
    }


def _injured_breather(player, from_location_id, to_location_id, get_enemy_for_location):
    heal = random.randint(2, 5)
    return {
        "id": "injured_breather",
        "narrative": "Your pace falters, forcing a brief stop in the lee of the terrain. It is not much, but the pause steadies you.",
        "heal": heal,
        "significance": "minor",
    }


def _camp_trade_scrap(player, from_location_id, to_location_id, get_enemy_for_location):
    gold = random.randint(1, 4)
    return {
        "id": "camp_trade_scrap",
        "narrative": "Near the camp trail, someone has dropped a few coins in the sand. No one nearby seems eager to claim them.",
        "gold": gold,
        "significance": "minor",
    }


def _wreckage_sign(player, from_location_id, to_location_id, get_enemy_for_location):
    scope = to_location_id if to_location_id in locations.LOCATIONS else None
    if scope:
        world.set_flag(player, "fresh_wreckage_seen", True, scope=scope)
    return {
        "id": "wreckage_sign",
        "narrative": "A plank beside the trail bears the same cargo mark you saw in the ship records. The wreckage trail is not random; something was carried this way.",
        "significance": "normal",
    }


TRAVEL_EVENTS = [
    {
        "id": "washed_up_cache",
        "weight": 14,
        "condition": lambda p, f, t: _is_coastal(f, t),
        "build": _washed_up_cache,
    },
    {
        "id": "sudden_squall",
        "weight": 12,
        "condition": lambda p, f, t: _is_coastal(f, t) and _weather(p, t) in ("stormy", "windy"),
        "build": _sudden_squall,
    },
    {
        "id": "dune_tracks",
        "weight": 10,
        "condition": lambda p, f, t: _has_any_property(f, t, {"sandy_terrain", "coastal_dunes"}),
        "build": _dune_tracks,
    },
    {
        "id": "night_ambush",
        "weight": 9,
        "condition": lambda p, f, t: world.current_phase(p) in ("dusk", "night") and not _is_safe(t),
        "build": _night_ambush,
    },
    {
        "id": "injured_breather",
        "weight": 8,
        "condition": lambda p, f, t: _low_health(p),
        "build": _injured_breather,
    },
    {
        "id": "camp_trade_scrap",
        "weight": 7,
        "condition": lambda p, f, t: "survivor_camp" in (f, t),
        "build": _camp_trade_scrap,
    },
    {
        "id": "wreckage_sign",
        "weight": 7,
        "condition": lambda p, f, t: (
            "captain_log_waterlogged" in p.get("inventory", [])
            and _has_any_property(f, t, {"shipwreck", "rocky_terrain"})
        ),
        "build": _wreckage_sign,
    },
]


def _event_chance(player, from_location_id, to_location_id):
    chance = BASE_EVENT_CHANCE
    if _weather(player, to_location_id) in ("stormy", "foggy"):
        chance += 0.1
    if world.current_phase(player) in ("dusk", "night"):
        chance += 0.08
    if _low_health(player):
        chance += 0.07
    return min(chance, 0.6)


def maybe_trigger(player, from_location_id, to_location_id, get_enemy_for_location):
    """Return a travel event dict, or None if the journey is uneventful."""
    if random.random() > _event_chance(player, from_location_id, to_location_id):
        return None

    candidates = [
        event for event in TRAVEL_EVENTS
        if not _recently_seen(player, event["id"])
        and event["condition"](player, from_location_id, to_location_id)
    ]
    chosen = _weighted_choice(candidates)
    if not chosen:
        return None

    outcome = chosen["build"](player, from_location_id, to_location_id, get_enemy_for_location)
    if not outcome:
        return None
    _mark_seen(player, chosen["id"])
    return outcome
