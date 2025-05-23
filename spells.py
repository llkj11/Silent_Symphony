# spells.py

SPELL_DB = {
    "firebolt": {
        "id": "firebolt",
        "name": "Firebolt",
        "description": "Hurls a small bolt of fire at the enemy. May cause burning.",
        "type": "OFFENSE",
        "target": "ENEMY",
        "mana_cost": 3,
        "value": 8,
        "duration": 0,
        "school": "evocation",
        "level": 1
    },
    "minor_heal": {
        "id": "minor_heal",
        "name": "Minor Heal",
        "description": "Slightly mends your wounds.",
        "type": "HEAL",
        "target": "SELF",
        "mana_cost": 2,
        "value": 10,
        "duration": 0,
        "school": "restoration",
        "level": 1
    },
    "arcane_shield": {
        "id": "arcane_shield",
        "name": "Arcane Shield",
        "description": "Summons a temporary shield, absorbing incoming damage.",
        "type": "DEFENSE_BUFF",
        "target": "SELF",
        "mana_cost": 4,
        "value": 3,
        "duration": 3,
        "school": "abjuration",
        "level": 1
    },
    "frost_lance": {
        "id": "frost_lance",
        "name": "Frost Lance",
        "description": "A piercing shard of ice that may slow enemies.",
        "type": "OFFENSE",
        "target": "ENEMY",
        "mana_cost": 4,
        "value": 10,
        "duration": 0,
        "school": "evocation",
        "level": 2,
        "special_effect": "slow_chance"
    },
    "healing_ward": {
        "id": "healing_ward",
        "name": "Healing Ward",
        "description": "Creates a magical ward that heals you over time.",
        "type": "HEAL_OVER_TIME",
        "target": "SELF",
        "mana_cost": 6,
        "value": 3,  # HP per turn
        "duration": 5,  # turns
        "school": "restoration",
        "level": 2
    },
    "weakness": {
        "id": "weakness",
        "name": "Weakness",
        "description": "Curses an enemy, reducing their attack power.",
        "type": "DEBUFF",
        "target": "ENEMY",
        "mana_cost": 5,
        "value": -3,  # Attack reduction
        "duration": 4,
        "school": "necromancy",
        "level": 2
    },
    "lightning_bolt": {
        "id": "lightning_bolt",
        "name": "Lightning Bolt",
        "description": "A powerful bolt of electricity that never misses.",
        "type": "OFFENSE",
        "target": "ENEMY",
        "mana_cost": 7,
        "value": 15,
        "duration": 0,
        "school": "evocation",
        "level": 3,
        "special_effect": "cannot_miss"
    },
    "battle_fury": {
        "id": "battle_fury",
        "name": "Battle Fury",
        "description": "Enhances your combat prowess, increasing damage and critical chance.",
        "type": "ATTACK_BUFF",
        "target": "SELF",
        "mana_cost": 8,
        "value": 4,  # Attack bonus
        "duration": 6,
        "school": "transmutation",
        "level": 3,
        "special_effect": "crit_bonus"
    },
    "poison_cloud": {
        "id": "poison_cloud",
        "name": "Poison Cloud",
        "description": "Creates a toxic cloud that poisons enemies over time.",
        "type": "OFFENSE_DOT",
        "target": "ENEMY",
        "mana_cost": 6,
        "value": 4,  # Damage per turn
        "duration": 4,
        "school": "conjuration",
        "level": 2
    },
    "mana_burn": {
        "id": "mana_burn",
        "name": "Mana Burn",
        "description": "Disrupts enemy magic and deals damage based on their remaining energy.",
        "type": "UTILITY",
        "target": "ENEMY",
        "mana_cost": 5,
        "value": 8,
        "duration": 0,
        "school": "abjuration",
        "level": 2,
        "special_effect": "mana_damage"
    },
    "stone_skin": {
        "id": "stone_skin",
        "name": "Stone Skin",
        "description": "Hardens your skin like stone, greatly increasing defense.",
        "type": "DEFENSE_BUFF",
        "target": "SELF",
        "mana_cost": 10,
        "value": 5,  # Defense bonus
        "duration": 8,
        "school": "transmutation",
        "level": 3
    },
    "life_drain": {
        "id": "life_drain",
        "name": "Life Drain",
        "description": "Drains life from your enemy to heal yourself.",
        "type": "VAMPIRIC",
        "target": "ENEMY",
        "mana_cost": 8,
        "value": 12,  # Damage dealt (50% converted to healing)
        "duration": 0,
        "school": "necromancy",
        "level": 3
    },
    "dispel_magic": {
        "id": "dispel_magic",
        "name": "Dispel Magic",
        "description": "Removes magical effects from yourself or enemies.",
        "type": "UTILITY",
        "target": "ANY",
        "mana_cost": 4,
        "value": 0,
        "duration": 0,
        "school": "abjuration",
        "level": 2,
        "special_effect": "dispel"
    },
    "meteor": {
        "id": "meteor",
        "name": "Meteor",
        "description": "Calls down a devastating meteor from the sky.",
        "type": "OFFENSE",
        "target": "ENEMY",
        "mana_cost": 15,
        "value": 25,
        "duration": 0,
        "school": "evocation",
        "level": 4,
        "special_effect": "massive_damage"
    },
    "time_slow": {
        "id": "time_slow",
        "name": "Time Slow",
        "description": "Slows down time around your enemy, reducing their effectiveness.",
        "type": "DEBUFF",
        "target": "ENEMY",
        "mana_cost": 12,
        "value": -50,  # Reduces enemy action efficiency
        "duration": 3,
        "school": "transmutation",
        "level": 4,
        "special_effect": "time_manipulation"
    },
    "phoenix_flame": {
        "id": "phoenix_flame",
        "name": "Phoenix Flame",
        "description": "A powerful fire spell that may revive you if you fall in battle.",
        "type": "OFFENSE",
        "target": "ENEMY",
        "mana_cost": 20,
        "value": 20,
        "duration": 0,
        "school": "evocation",
        "level": 5,
        "special_effect": "revival_chance"
    }
}

# Spell learning requirements
SPELL_REQUIREMENTS = {
    "firebolt": {"level": 1, "prerequisite": None},
    "minor_heal": {"level": 1, "prerequisite": None},
    "arcane_shield": {"level": 1, "prerequisite": None},
    "frost_lance": {"level": 3, "prerequisite": "firebolt"},
    "healing_ward": {"level": 4, "prerequisite": "minor_heal"},
    "weakness": {"level": 3, "prerequisite": None},
    "lightning_bolt": {"level": 5, "prerequisite": "firebolt"},
    "battle_fury": {"level": 6, "prerequisite": None},
    "poison_cloud": {"level": 4, "prerequisite": None},
    "mana_burn": {"level": 4, "prerequisite": "arcane_shield"},
    "stone_skin": {"level": 7, "prerequisite": "arcane_shield"},
    "life_drain": {"level": 6, "prerequisite": "weakness"},
    "dispel_magic": {"level": 5, "prerequisite": "arcane_shield"},
    "meteor": {"level": 10, "prerequisite": "lightning_bolt"},
    "time_slow": {"level": 12, "prerequisite": None},
    "phoenix_flame": {"level": 15, "prerequisite": "meteor"}
}

# Magic schools for character specialization
MAGIC_SCHOOLS = {
    "evocation": {
        "name": "Evocation",
        "description": "The school of raw magical energy - fireballs, lightning, and pure force.",
        "bonus": "Increased spell damage"
    },
    "restoration": {
        "name": "Restoration",
        "description": "Healing magic and protective wards.",
        "bonus": "Enhanced healing and mana efficiency"
    },
    "abjuration": {
        "name": "Abjuration",
        "description": "Protective and defensive magic.",
        "bonus": "Stronger shields and spell resistance"
    },
    "necromancy": {
        "name": "Necromancy",
        "description": "Dark magic dealing with life force and death.",
        "bonus": "Life drain effects and fear abilities"
    },
    "transmutation": {
        "name": "Transmutation",
        "description": "Magic that changes and enhances physical properties.",
        "bonus": "Longer lasting buffs and transformations"
    },
    "conjuration": {
        "name": "Conjuration",
        "description": "Summoning and creation magic.",
        "bonus": "Area effect spells and summons"
    }
}

def can_learn_spell(player_character, spell_id):
    """Check if a player can learn a specific spell"""
    if spell_id not in SPELL_REQUIREMENTS:
        return False
    
    req = SPELL_REQUIREMENTS[spell_id]
    
    # Check level requirement
    if player_character.get('level', 1) < req['level']:
        return False
    
    # Check prerequisite spell
    if req['prerequisite'] and req['prerequisite'] not in player_character.get('known_spells', []):
        return False
    
    # Check if already known
    if spell_id in player_character.get('known_spells', []):
        return False
    
    return True

def get_available_spells_to_learn(player_character):
    """Get list of spells the player can currently learn"""
    available = []
    for spell_id in SPELL_DB:
        if can_learn_spell(player_character, spell_id):
            available.append(spell_id)
    return available
