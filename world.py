"""World-state helpers: per-location POI status, visit counts, global flags,
slain unique enemies, turn/time/weather. All reads go through these helpers so
the nested shape can evolve without the call sites caring."""

import random

# Day/night cycle — 16 turns per full day, four phases.
PHASE_BOUNDS = (
    ("dawn", 0, 3),
    ("day", 4, 9),
    ("dusk", 10, 11),
    ("night", 12, 15),
)
DAY_LENGTH = 16

DEFAULT_WEATHER_POOL = ["clear", "overcast", "windy", "foggy"]
WEATHER_REROLL_INTERVAL = 5  # turns of the same weather before considering a reroll


def ensure(player):
    """Return the player's world_state, creating any missing top-level shape."""
    ws = player.setdefault("world_state", {})
    ws.setdefault("locations", {})
    ws.setdefault("slain_unique_enemies", [])
    ws.setdefault("flags", {})
    ws.setdefault("turn_counter", 0)
    return ws


def location(player, location_id):
    ws = ensure(player)
    loc = ws["locations"].setdefault(location_id, {})
    loc.setdefault("visits", 0)
    loc.setdefault("pois", {})
    loc.setdefault("flags", {})
    return loc


def mark_visit(player, location_id):
    loc = location(player, location_id)
    loc["visits"] = loc.get("visits", 0) + 1
    return loc["visits"]


def visit_count(player, location_id):
    return location(player, location_id).get("visits", 0)


def poi_state(player, location_id, poi_id):
    """Return the recorded state dict for a POI, or None if untouched."""
    loc = location(player, location_id)
    return loc["pois"].get(poi_id)


def set_poi_state(player, location_id, poi_id, status, **extra):
    """Record a POI outcome. `status` is a short tag like 'looted'/'sprung'/'read'."""
    loc = location(player, location_id)
    entry = loc["pois"].setdefault(poi_id, {})
    entry["status"] = status
    for k, v in extra.items():
        entry[k] = v
    return entry


def is_poi_completed(player, location_id, poi):
    """True if the POI has a status that should remove it from the investigation pool."""
    state = poi_state(player, location_id, poi.get("poi_id"))
    return state is not None and state.get("status") is not None


def active_pois(player, location_id, defined_pois):
    return [poi for poi in defined_pois if not is_poi_completed(player, location_id, poi)]


def is_enemy_slain(player, enemy_id):
    ws = ensure(player)
    return enemy_id in ws.get("slain_unique_enemies", [])


def mark_enemy_slain(player, enemy_id):
    ws = ensure(player)
    if enemy_id not in ws["slain_unique_enemies"]:
        ws["slain_unique_enemies"].append(enemy_id)


def set_flag(player, key, value=True, scope=None):
    """Set a global flag, or a per-location flag if `scope` is a location_id."""
    if scope is None:
        ensure(player)["flags"][key] = value
    else:
        location(player, scope)["flags"][key] = value


def get_flag(player, key, scope=None, default=None):
    if scope is None:
        return ensure(player)["flags"].get(key, default)
    return location(player, scope)["flags"].get(key, default)


def tick_turn(player, count=1):
    ws = ensure(player)
    ws["turn_counter"] = ws.get("turn_counter", 0) + count
    return ws["turn_counter"]


def turn_counter(player):
    return ensure(player).get("turn_counter", 0)


def current_phase(player):
    """Return the day/night phase name for the current turn."""
    t = turn_counter(player) % DAY_LENGTH
    for name, lo, hi in PHASE_BOUNDS:
        if lo <= t <= hi:
            return name
    return "day"


def current_weather(player, location_id, location_data=None):
    """Return (and lazily roll) the weather for the given location.

    Weather persists for WEATHER_REROLL_INTERVAL turns, then has a chance to
    reroll on the next read. Per-location pool takes precedence over the default.
    """
    loc = location(player, location_id)
    entry = loc.setdefault("weather", {})
    now = turn_counter(player)
    pool = (location_data or {}).get("weather_pool") or DEFAULT_WEATHER_POOL

    current = entry.get("id")
    set_on = entry.get("set_on_turn", -999)
    age = now - set_on

    if not current or age >= WEATHER_REROLL_INTERVAL:
        # 100% reroll once stale, small chance earlier (already rerolled recently).
        if not current or random.random() < 0.6:
            entry["id"] = random.choice(pool)
            entry["set_on_turn"] = now
    return entry.get("id", "clear")
