import random


# Ability handler: (player, enemy) -> dict with any of:
#   narrative, damage, self_heal,
#   status_to_enemy {kind, turns, tick_dmg}, status_to_self {kind, turns, value, tick_dmg}


def _fire_dart(player, enemy):
    dmg = random.randint(4, 7)
    return {
        "narrative": f"You fling a dart of flame at the {enemy['name']}. It sizzles on impact!",
        "damage": dmg,
        "status_to_enemy": {"kind": "burn", "turns": 2, "tick_dmg": 2},
    }


def _gust(player, enemy):
    dmg = random.randint(2, 4)
    return {
        "narrative": f"A sharp gust slams the {enemy['name']}, knocking it off balance!",
        "damage": dmg,
        "status_to_enemy": {"kind": "stun", "turns": 1},
    }


def _invigorate(player, enemy):
    return {
        "narrative": "You draw on inner reserves; warmth floods your limbs.",
        "self_heal": 8,
    }


def _shadow_strike(player, enemy):
    dmg = random.randint(5, 9)
    return {
        "narrative": f"You slip behind the {enemy['name']} and strike from the shadows!",
        "damage": dmg,
        "bypasses_defense": True,
    }


def _warcry(player, enemy):
    return {
        "narrative": "You let out a roar that rattles your own bones. Muscles tighten with fury.",
        "status_to_self": {"kind": "buff_strength", "turns": 3, "value": 2},
    }


ABILITIES = {
    "fire_dart": {
        "name": "Fire Dart",
        "description": "Hurl a bolt of flame. Burns the target.",
        "mana_cost": 3,
        "stamina_cost": 0,
        "magic_scales": True,
        "handler": _fire_dart,
    },
    "gust": {
        "name": "Gust",
        "description": "A hammering wind that briefly stuns a foe.",
        "mana_cost": 2,
        "stamina_cost": 1,
        "magic_scales": True,
        "handler": _gust,
    },
    "invigorate": {
        "name": "Invigorate",
        "description": "Channel inner vigor to heal 8 HP.",
        "mana_cost": 2,
        "stamina_cost": 2,
        "handler": _invigorate,
    },
    "shadow_strike": {
        "name": "Shadow Strike",
        "description": "A precise attack that bypasses armor.",
        "mana_cost": 0,
        "stamina_cost": 3,
        "handler": _shadow_strike,
    },
    "warcry": {
        "name": "War Cry",
        "description": "Gain +2 strength for 3 turns.",
        "mana_cost": 0,
        "stamina_cost": 3,
        "handler": _warcry,
    },
}


STAR_SIGN_STARTING_ABILITY = {
    "Ember": "fire_dart",
    "Solstice": "fire_dart",
    "Tempest": "gust",
    "Astral": "gust",
    "Aegis": "invigorate",
    "Seraph": "invigorate",
    "Verdant": "invigorate",
    "Lumos": "invigorate",
    "Eclipse": "shadow_strike",
    "Nexus": "warcry",
}


def starting_abilities_for(star_sign):
    ability_id = STAR_SIGN_STARTING_ABILITY.get(star_sign)
    return [ability_id] if ability_id else []


def format_cost(ability):
    parts = []
    if ability.get("mana_cost"):
        parts.append(f"{ability['mana_cost']}M")
    if ability.get("stamina_cost"):
        parts.append(f"{ability['stamina_cost']}S")
    return "/".join(parts) if parts else "free"


def can_afford(player, ability):
    return (
        player.get("mana", 0) >= ability.get("mana_cost", 0)
        and player.get("stamina", 0) >= ability.get("stamina_cost", 0)
    )


def pay_cost(player, ability):
    player["mana"] = player.get("mana", 0) - ability.get("mana_cost", 0)
    player["stamina"] = player.get("stamina", 0) - ability.get("stamina_cost", 0)
