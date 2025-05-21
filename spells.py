# spells.py

SPELL_DB = {
    "firebolt": {
        "id": "firebolt",
        "name": "Firebolt",
        "description": "Hurls a small bolt of fire at the enemy.",
        "type": "OFFENSE", # e.g., OFFENSE, HEAL, BUFF, DEBUFF, SUMMON
        "target": "ENEMY", # e.g., SELF, ENEMY, ALL_ENEMIES, ALL_ALLIES
        "mana_cost": 3,
        "value": 8, # Base damage for OFFENSE, heal amount for HEAL, buff strength for BUFF
        "duration": 0, # In turns. 0 for instant effects.
        # "effect_properties": {} # For more complex effects like DoT, stat modifiers
    },
    "minor_heal": {
        "id": "minor_heal",
        "name": "Minor Heal",
        "description": "Slightly mends your wounds.",
        "type": "HEAL",
        "target": "SELF",
        "mana_cost": 2,
        "value": 10, # Amount of health restored
        "duration": 0,
    },
    "arcane_shield": {
        "id": "arcane_shield",
        "name": "Arcane Shield",
        "description": "Summons a temporary shield, increasing defense for a few turns.",
        "type": "DEFENSE_BUFF", # Specific type of buff
        "target": "SELF",
        "mana_cost": 4,
        "value": 3, # Defense bonus
        "duration": 3, # Number of turns the buff lasts
        # "affected_stat": "defense" # Could be explicit if needed by game logic
    }
    # Future spells could include:
    # "ice_lance": { ... "type": "OFFENSE", "effect_properties": {"status_effect": "FROZEN", "chance": 0.3} ... }
    # "strength_blessing": { ... "type": "ATTACK_BUFF", "target": "SELF", "value": 5, "duration": 3, "affected_stat": "attack_power" ... }
}
