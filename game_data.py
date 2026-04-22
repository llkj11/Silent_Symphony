# List of valid races and origins
valid_races = ["Human", "Orc", "Naiad", "Elf", "Dwarf", "Maithar", "Urthar"]
valid_origins = ["Lowborn", "Highborn", "Rural", "Marauder"]
valid_actions = ["Attack", "Flee"] # Note: This might be combat specific, consider if it belongs elsewhere or is general enough.
valid_star_signs = ["Aegis", "Seraph", "Eclipse", "Lumos", "Verdant", "Tempest", "Solstice", "Nexus", "Ember", "Astral"]


# Race → stat modifiers (deltas applied to base max_*) + one passive trait.
# Traits are read back at combat time via player['race_trait']; keep strings stable.
RACE_TRAITS = {
    "Human": {
        "description": "Versatile — a steady all-rounder.",
        "stat_mods": {"max_health": 0, "max_mana": 2, "max_stamina": 2},
        "trait": None,
        "trait_description": "",
    },
    "Orc": {
        "description": "Fierce and hardy, more deadly when bloodied.",
        "stat_mods": {"max_health": 10, "max_mana": -2, "max_stamina": 2},
        "trait": "low_hp_fury",
        "trait_description": "+2 damage when at or below 1/3 max HP.",
    },
    "Naiad": {
        "description": "Of the rivers — deep reservoir of mana.",
        "stat_mods": {"max_health": -5, "max_mana": 6, "max_stamina": 2},
        "trait": "river_born",
        "trait_description": "Immune to future thirst and dehydration effects.",
    },
    "Elf": {
        "description": "Keen-eyed and deft in combat.",
        "stat_mods": {"max_health": -3, "max_mana": 4, "max_stamina": 4},
        "trait": "elven_accuracy",
        "trait_description": "+5% hit chance on attacks.",
    },
    "Dwarf": {
        "description": "Stonebound — armor fits you like a second skin.",
        "stat_mods": {"max_health": 5, "max_mana": -4, "max_stamina": 2},
        "trait": "armor_mastery",
        "trait_description": "+1 defense per piece of armor you wear.",
    },
    "Maithar": {
        "description": "Starborn — thought and will run deep.",
        "stat_mods": {"max_health": -5, "max_mana": 10, "max_stamina": 0},
        "trait": "mana_attuned",
        "trait_description": "+1 damage on magic-scaling abilities.",
    },
    "Urthar": {
        "description": "Wildborn — endurance beyond most.",
        "stat_mods": {"max_health": 5, "max_mana": -2, "max_stamina": 6},
        "trait": "stout",
        "trait_description": "+1 extra stamina regen per combat round.",
    },
}


# Origin → starting kit. Items are item_ids from items.ITEM_DB; gold is flat.
ORIGIN_STARTING_KIT = {
    "Lowborn": {
        "inventory": ["old_coin_tarnished"],
        "gold": 0,
        "flavor": "a tarnished coin kept for luck",
    },
    "Highborn": {
        "inventory": [],
        "gold": 25,
        "flavor": "a small purse heavy with coin",
    },
    "Rural": {
        "inventory": ["ration_pack_basic", "flint_sharp"],
        "gold": 3,
        "flavor": "a day's rations and a sharp flint",
    },
    "Marauder": {
        "inventory": ["wooden_club"],
        "gold": 1,
        "flavor": "a crude club taken in some raid",
    },
}
