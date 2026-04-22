import random


# Each handler takes (player, enemy) and returns a dict:
#   narrative: str (required)
#   damage: int — raw damage BEFORE player defense/guard
#   bypasses_defense: bool — if True, armor and guard don't reduce damage
#   status_to_player: {kind, turns, tick_dmg} — status inflicted on player


def _poison_bite(player, enemy):
    return {
        "narrative": f"The {enemy['name']} sinks its fangs into you! Venom courses through your veins.",
        "damage": random.randint(1, 3),
        "status_to_player": {"kind": "poison", "turns": 3, "tick_dmg": 2},
    }


def _slam_stun(player, enemy):
    return {
        "narrative": f"The {enemy['name']} crashes into you with bone-rattling force!",
        "damage": random.randint(3, 6),
        "status_to_player": {"kind": "stun", "turns": 1},
    }


def _ember_burst(player, enemy):
    return {
        "narrative": f"The {enemy['name']} erupts in a sudden burst of flame!",
        "damage": random.randint(3, 5),
        "bypasses_defense": True,
        "damage_type": "magical",
        "status_to_player": {"kind": "burn", "turns": 2, "tick_dmg": 2},
    }


def _tail_spikes(player, enemy):
    return {
        "narrative": f"The {enemy['name']} whips its tail, firing a volley of spikes!",
        "damage": random.randint(6, 10),
    }


def _precise_shot(player, enemy):
    return {
        "narrative": f"The {enemy['name']} takes careful aim and looses a precise shot!",
        "damage": random.randint(4, 7),
        "bypasses_defense": True,
    }


def _rending_claw(player, enemy):
    return {
        "narrative": f"The {enemy['name']} rakes you with its claws, leaving deep wounds.",
        "damage": random.randint(2, 4),
        "status_to_player": {"kind": "bleeding", "turns": 2, "tick_dmg": 1},
    }


HANDLERS = {
    "poison_bite": _poison_bite,
    "slam_stun": _slam_stun,
    "ember_burst": _ember_burst,
    "tail_spikes": _tail_spikes,
    "precise_shot": _precise_shot,
    "rending_claw": _rending_claw,
}


DEFAULT_SPECIAL_CHANCE = 0.3


def get_special_for_turn(enemy):
    """Decide whether the enemy uses a special attack this turn. Returns special_id or None."""
    specials = enemy.get("special_attacks")
    if specials:
        for entry in specials:
            if random.random() < entry.get("chance", 0):
                return entry["id"]
        return None
    legacy = enemy.get("special_attack")
    if legacy and random.random() < DEFAULT_SPECIAL_CHANCE:
        return legacy
    return None


def execute_special(special_id, player, enemy):
    handler = HANDLERS.get(special_id)
    if not handler:
        return None
    return handler(player, enemy)
