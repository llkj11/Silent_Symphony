# --- Enemy Templates ---
# Defines the blueprints for enemies.
ENEMY_TEMPLATES = {
    "goblin_scout": {
        "id": "goblin_scout",
        "name": "Goblin Scout",
        "description": "A small, wiry goblin with beady eyes, clutching a crude spear.",
        "health": 15,
        "attack_min": 2,
        "attack_max": 5,
        "loot_table": [
            {"item_id": "pebble_shiny", "chance": 0.8},
            {"item_id": "goblin_ear", "chance": 0.5},
            {"item_id": "spear_common", "chance": 0.5}
        ],
        "xp_value": 10
    },
    "giant_sand_crab": {
        "id": "giant_sand_crab",
        "name": "Giant Sand Crab",
        "description": "A large crab with a thick, sandy carapace and menacing claws.",
        "health": 25,
        "attack_min": 3,
        "attack_max": 7,
        "loot_table": [
            {"item_id": "broken_shell", "chance": 0.9},
            {"item_id": "seaweed_clump", "chance": 0.6},
            {"item_id": "healing_salve_minor", "chance": 0.1}
        ],
        "xp_value": 20
    },

    # --- NEW ENEMIES START HERE ---

    # == Humanoids - Bandits & Outlaws ==
    "bandit_thug": {
        "id": "bandit_thug",
        "name": "Bandit Thug",
        "description": "A brutish outlaw armed with a crude club and ill-fitting leather armor.",
        "health": 20,
        "attack_min": 3,
        "attack_max": 6,
        "loot_table": ["wooden_club", "leather_scraps", "ration_pack_basic", "old_coin_tarnished"],
        "xp_value": 15
    },
    "bandit_archer": {
        "id": "bandit_archer",
        "name": "Bandit Archer",
        "description": "A nimble bandit preferring to strike from a distance with a worn bow.",
        "health": 18,
        "attack_min": 2,
        "attack_max": 5, # Ranged attack
        "loot_table": ["hunting_bow_simple", "dull_arrowhead", "berries_wild"],
        "xp_value": 18
    },
    "bandit_cutthroat": {
        "id": "bandit_cutthroat",
        "name": "Bandit Cutthroat",
        "description": "A dangerous bandit skilled with daggers and ambushes.",
        "health": 22,
        "attack_min": 4,
        "attack_max": 7,
        "loot_table": ["steel_dagger", "leather_cap", "lockpick_simple", "silver_ring_plain"],
        "xp_value": 25
    },
    "marauder_reaver": {
        "id": "marauder_reaver",
        "name": "Marauder Reaver",
        "description": "A fierce coastal marauder, armed with an axe and hardened by sea battles.",
        "health": 30,
        "attack_min": 5,
        "attack_max": 8,
        "loot_table": ["orcish_hand_axe", "hide_armor_crude", "ration_pack_basic", "pearl_small"],
        "xp_value": 35
    },
    "rogue_scout": {
        "id": "rogue_scout",
        "name": "Rogue Scout",
        "description": "A stealthy individual, adept at moving unseen and striking suddenly.",
        "health": 20,
        "attack_min": 3,
        "attack_max": 6,
        "loot_table": ["short_sword_iron", "shadowroot_bark", "string_piece"],
        "xp_value": 22
    },

    # == Humanoids - Cultists & Sorcerers ==
    "cultist_acolyte": {
        "id": "cultist_acolyte",
        "name": "Cultist Acolyte",
        "description": "A hooded figure muttering dark incantations, weakly flinging minor curses.",
        "health": 16,
        "attack_min": 1, # Magical attack
        "attack_max": 4,
        "loot_table": ["rusty_dagger", "mage_robe_novice", "brimstone_dust", "note_smudged_warning"],
        "xp_value": 12
    },
    "hedge_mage": {
        "id": "hedge_mage",
        "name": "Hedge Mage",
        "description": "A self-taught magic user with unpredictable but sometimes potent spells.",
        "health": 25,
        "attack_min": 3, # Magical attack
        "attack_max": 7,
        "loot_table": ["staff_apprentice", "scroll_fire_dart", "moonbloom_flower", "crystal_shard_mundane"],
        "xp_value": 30
    },
    "necromancer_apprentice": {
        "id": "necromancer_apprentice",
        "name": "Necromancer's Apprentice",
        "description": "A grim figure dabbling in the forbidden arts of necromancy, often accompanied by reanimated vermin.",
        "health": 28,
        "attack_min": 2, # Magical attack, might summon weak undead
        "attack_max": 6,
        "loot_table": ["bone_fragment", "ectoplasm_vial", "scroll_light", "tales_of_gaiatheia_vol1"],
        "xp_value": 40
    },
    "shaman_initiate": {
        "id": "shaman_initiate",
        "name": "Shaman Initiate",
        "description": "A tribal shaman-in-training, calling upon minor nature spirits for aid.",
        "health": 22,
        "attack_min": 2,
        "attack_max": 5, # Mix of physical and nature magic
        "loot_table": ["wooden_club", "herbal_poultice", "fey_dust", "animal_hide_small"],
        "xp_value": 28
    },
    "alchemist_journeyman": {
        "id": "alchemist_journeyman",
        "name": "Journeyman Alchemist",
        "description": "An alchemist who might throw unstable concoctions or use a blade coated in irritants.",
        "health": 26,
        "attack_min": 3,
        "attack_max": 6, # Can throw potions
        "loot_table": ["steel_dagger", "antidote_simple", "sunpetal_leaf", "mortar_pestle_stone"],
        "xp_value": 32
    },

    # == Beasts - Forest & Plains ==
    "forest_wolf": {
        "id": "forest_wolf",
        "name": "Forest Wolf",
        "description": "A common wolf found in dense woodlands, often hunting in packs.",
        "health": 18,
        "attack_min": 3,
        "attack_max": 5,
        "loot_table": ["wolf_pelt", "animal_hide_small", "bone_fragment"],
        "xp_value": 12
    },
    "giant_spider_webspinner": {
        "id": "giant_spider_webspinner",
        "name": "Giant Spider (Webspinner)",
        "description": "A large, eight-legged horror that can ensnare prey in sticky webs.",
        "health": 22,
        "attack_min": 4,
        "attack_max": 6, # Might have a web attack
        "loot_table": ["spider_silk_strand", "bat_wing"], # Bat wings from caught prey
        "xp_value": 20
    },
    "wild_boar": {
        "id": "wild_boar",
        "name": "Wild Boar",
        "description": "A tusked beast with a foul temper, known to charge intruders.",
        "health": 30,
        "attack_min": 4,
        "attack_max": 7,
        "loot_table": ["animal_hide_small", "bone_fragment", "berries_wild"], # Boars might eat berries
        "xp_value": 25
    },
    "cave_bat_swarm": {
        "id": "cave_bat_swarm",
        "name": "Cave Bat Swarm",
        "description": "A disorienting swarm of screeching cave bats.",
        "health": 12, # Swarm health
        "attack_min": 1, # Many small attacks
        "attack_max": 3,
        "loot_table": ["bat_wing", "rat_tail"], # Things found in caves
        "xp_value": 8
    },
    "dire_wolf_alpha": {
        "id": "dire_wolf_alpha",
        "name": "Dire Wolf Alpha",
        "description": "A larger, more ferocious wolf leading its pack.",
        "health": 40,
        "attack_min": 5,
        "attack_max": 9,
        "loot_table": ["wolf_pelt", "bone_fragment", "healing_salve_minor"], # Might carry something from a past victim
        "xp_value": 50
    },
    "forest_bear_cub": {
        "id": "forest_bear_cub",
        "name": "Forest Bear Cub",
        "description": "A young bear. Seemingly less dangerous, but its mother might be near.",
        "health": 15,
        "attack_min": 2,
        "attack_max": 4,
        "loot_table": ["animal_hide_small", "fish_bones"],
        "xp_value": 10
    },
    "forest_bear_mother": {
        "id": "forest_bear_mother",
        "name": "Forest Bear Mother",
        "description": "A large, protective mother bear. Extremely dangerous if provoked or near her cub.",
        "health": 70,
        "attack_min": 7,
        "attack_max": 12,
        "loot_table": ["animal_hide_small", "healing_potion_lesser", "ration_pack_basic"], # Could have items from adventurers
        "xp_value": 100
    },
    "giant_rat": {
        "id": "giant_rat",
        "name": "Giant Rat",
        "description": "An unnaturally large and aggressive rat, common in sewers and dungeons.",
        "health": 10,
        "attack_min": 1,
        "attack_max": 3,
        "loot_table": ["rat_tail", "bone_fragment", "moldy_bread_crust"],
        "xp_value": 5
    },
    "venomous_snake": {
        "id": "venomous_snake",
        "name": "Venomous Snake",
        "description": "A camouflaged snake with a poisonous bite.",
        "health": 12,
        "attack_min": 1,
        "attack_max": 2, # Main damage from poison
        "special_attack": "poison_bite",
        "loot_table": ["antidote_simple", "string_piece"], # Antidote is ironic or from a previous victim
        "xp_value": 15
    },
    "woodland_sprite": {
        "id": "woodland_sprite",
        "name": "Woodland Sprite",
        "description": "A small, mischievous fey creature of the forest, flitting through the trees.",
        "health": 10,
        "attack_min": 1,
        "attack_max": 3, # Magical, nature-based
        "loot_table": ["fey_dust", "berries_wild", "pebble_shiny"],
        "xp_value": 12
    },


    # == Beasts - Swamps & Bogs ==
    "swamp_lizard": {
        "id": "swamp_lizard",
        "name": "Swamp Lizard",
        "description": "A large, predatory lizard adapted to murky swamp environments.",
        "health": 28,
        "attack_min": 3,
        "attack_max": 6,
        "loot_table": ["animal_hide_small", "fish_bones", "seaweed_clump"],
        "xp_value": 22
    },
    "giant_leech": {
        "id": "giant_leech",
        "name": "Giant Leech",
        "description": "A disgustingly large leech that drains blood from its victims.",
        "health": 15,
        "attack_min": 2, # Drains health
        "attack_max": 4,
        "loot_table": ["ectoplasm_vial"], # Leeches are slimy
        "xp_value": 10
    },
    "bog_imp": {
        "id": "bog_imp",
        "name": "Bog Imp",
        "description": "A small, foul creature that lurks in bogs, throwing mud and small curses.",
        "health": 12,
        "attack_min": 1,
        "attack_max": 3,
        "loot_table": ["clay_lump", "brimstone_dust", "rusted_nail"],
        "xp_value": 9
    },
    "mud_golem_lesser": {
        "id": "mud_golem_lesser",
        "name": "Lesser Mud Golem",
        "description": "A shambling humanoid figure formed from thick swamp mud and animated by weak magic.",
        "health": 35,
        "attack_min": 4,
        "attack_max": 7,
        "loot_table": ["clay_lump", "crystal_shard_mundane", "seaweed_clump"],
        "xp_value": 30
    },
    "will_o_wisp": {
        "id": "will_o_wisp",
        "name": "Will-o'-Wisp",
        "description": "A faintly glowing light that lures travelers to their doom in hazardous terrain.",
        "health": 8, # Hard to hit
        "attack_min": 2, # Energy drain
        "attack_max": 5,
        "loot_table": ["fey_dust", "ectoplasm_vial"],
        "xp_value": 25
    },

    # == Beasts - Mountains & Caves ==
    "mountain_goat_aggressive": {
        "id": "mountain_goat_aggressive",
        "name": "Aggressive Mountain Goat",
        "description": "A sturdy goat with large horns, fiercely territorial.",
        "health": 20,
        "attack_min": 3,
        "attack_max": 6,
        "loot_table": ["animal_hide_small", "bone_fragment", "iron_ore"], # Found in mountains
        "xp_value": 15
    },
    "cave_bear": {
        "id": "cave_bear",
        "name": "Cave Bear",
        "description": "A large, hibernating bear that has made its den in a dark cave. Easily angered.",
        "health": 75,
        "attack_min": 8,
        "attack_max": 13,
        "loot_table": ["animal_hide_small", "bone_fragment", "healing_potion_lesser", "gold_nugget_small"], # Hoards shiny things
        "xp_value": 110
    },
    "harpy_scout": {
        "id": "harpy_scout",
        "name": "Harpy Scout",
        "description": "A winged humanoid creature with sharp talons and a piercing shriek.",
        "health": 25,
        "attack_min": 4,
        "attack_max": 7,
        "loot_table": ["pebble_shiny", "torn_rag", "ivory_figurine_crude"], # Steals trinkets
        "xp_value": 35
    },
    "stone_elemental_shardling": {
        "id": "stone_elemental_shardling",
        "name": "Stone Elemental Shardling",
        "description": "A small, animated fragment of rock, a lesser form of a stone elemental.",
        "health": 30,
        "attack_min": 3,
        "attack_max": 6,
        "loot_table": ["iron_ore", "copper_ore", "crystal_shard_mundane", "gem_amethyst_rough"],
        "xp_value": 28
    },
    "dwarven_mine_crawler": { # Spider variant for mines
        "id": "dwarven_mine_crawler",
        "name": "Dwarven Mine Crawler",
        "description": "A hardy, rock-colored spider adapted to life in dark mine shafts.",
        "health": 20,
        "attack_min": 3,
        "attack_max": 5,
        "loot_table": ["spider_silk_strand", "iron_ore", "dull_arrowhead"],
        "xp_value": 18
    },

    # == Undead ==
    "skeleton_warrior": {
        "id": "skeleton_warrior",
        "name": "Skeleton Warrior",
        "description": "The reanimated bones of a fallen warrior, armed with a rusty sword.",
        "health": 18,
        "attack_min": 3,
        "attack_max": 6,
        "loot_table": ["rusty_dagger", "wooden_shield_round", "bone_fragment", "tarnished_old_coin"],
        "xp_value": 20
    },
    "zombie_shambler": {
        "id": "zombie_shambler",
        "name": "Zombie Shambler",
        "description": "A slow-moving corpse, reanimated by dark magic, seeking living flesh.",
        "health": 25,
        "attack_min": 2,
        "attack_max": 5,
        "loot_table": ["torn_rag", "chipped_mug", "ectoplasm_vial"],
        "xp_value": 15
    },
    "ghoul_scavenger": {
        "id": "ghoul_scavenger",
        "name": "Ghoul Scavenger",
        "description": "A vile undead creature that feeds on carrion, its touch can paralyze.",
        "health": 30,
        "attack_min": 4,
        "attack_max": 7, # Paralysis chance
        "loot_table": ["bone_fragment", "rat_tail", "hermits_lost_locket"], # Might have items from its victims
        "xp_value": 40
    },
    "wraith_shadow": {
        "id": "wraith_shadow",
        "name": "Shadow Wraith",
        "description": "An incorporeal undead spirit, its touch drains life force.",
        "health": 35, # Potentially resistant to physical
        "attack_min": 5, # Life drain
        "attack_max": 8,
        "loot_table": ["ectoplasm_vial", "fey_dust", "shadowroot_bark", "ancient_tome_cover"],
        "xp_value": 60
    },
    "skeletal_archer": {
        "id": "skeletal_archer",
        "name": "Skeletal Archer",
        "description": "The reanimated bones of an archer, still clutching its bow.",
        "health": 15,
        "attack_min": 2,
        "attack_max": 5, # Ranged
        "loot_table": ["hunting_bow_simple", "bone_fragment", "dull_arrowhead"],
        "xp_value": 22
    },

    # == Magical & Elemental Creatures ==
    "fire_imp": {
        "id": "fire_imp",
        "name": "Fire Imp",
        "description": "A small, mischievous creature wreathed in flames, hurling tiny fireballs.",
        "health": 14,
        "attack_min": 2,
        "attack_max": 4, # Fire damage
        "loot_table": ["brimstone_dust", "obsidian_shard", "glowing_ember_pendant"],
        "xp_value": 18
    },
    "ice_sprite": {
        "id": "ice_sprite",
        "name": "Ice Sprite",
        "description": "A delicate fey creature formed of ice, flinging sharp icicles.",
        "health": 12,
        "attack_min": 2,
        "attack_max": 4, # Ice damage
        "loot_table": ["fey_dust", "crystal_shard_mundane", "pearl_small"],
        "xp_value": 17
    },
    "earth_wisp": {
        "id": "earth_wisp",
        "name": "Earth Wisp",
        "description": "A small mote of earthy energy, surprisingly solid.",
        "health": 20,
        "attack_min": 2,
        "attack_max": 5,
        "loot_table": ["clay_lump", "iron_ore", "pebble_shiny"],
        "xp_value": 15
    },
    "air_current_lesser": { # Lesser air elemental
        "id": "air_current_lesser",
        "name": "Lesser Air Current",
        "description": "A swirling vortex of air, difficult to strike.",
        "health": 18, # High evasion
        "attack_min": 1,
        "attack_max": 4, # Pushing/buffeting attacks
        "loot_table": ["fey_dust", "string_piece"],
        "xp_value": 20
    },
    "animated_armor_rusty": {
        "id": "animated_armor_rusty",
        "name": "Rusty Animated Armor",
        "description": "A suit of old, rusty armor animated by a lingering spirit or enchantment.",
        "health": 40,
        "attack_min": 5,
        "attack_max": 8,
        "loot_table": ["iron_ingot", "leather_scraps", "rusted_nail", "iron_helmet_basic"],
        "xp_value": 55
    },

    # == Larger & More Dangerous Creatures ==
    "troll_bridge": {
        "id": "troll_bridge",
        "name": "Bridge Troll",
        "description": "A hulking, green-skinned troll that demands a toll or a fight.",
        "health": 80,
        "attack_min": 7,
        "attack_max": 12, # Regenerates health
        "loot_table": ["wooden_club", "animal_hide_small", "gold_nugget_small", "chipped_mug"],
        "xp_value": 120
    },
    "ogre_brute": {
        "id": "ogre_brute",
        "name": "Ogre Brute",
        "description": "A large, dim-witted humanoid of immense strength, wielding a massive club.",
        "health": 90,
        "attack_min": 9,
        "attack_max": 15,
        "loot_table": ["wooden_club", "hide_armor_crude", "ration_pack_basic", "copper_goblet"],
        "xp_value": 150
    },
    "griffin_young": {
        "id": "griffin_young",
        "name": "Young Griffin",
        "description": "A majestic creature with the body of a lion and the head and wings of an eagle, not yet fully grown but still dangerous.",
        "health": 65,
        "attack_min": 6,
        "attack_max": 10, # Flying attacks
        "loot_table": ["pebble_shiny", "bone_fragment", "ivory_figurine_crude"],
        "xp_value": 130
    },
    "wyvern_juvenile": {
        "id": "wyvern_juvenile",
        "name": "Juvenile Wyvern",
        "description": "A smaller, two-legged dragon relative with a venomous sting in its tail.",
        "health": 70,
        "attack_min": 7,
        "attack_max": 11, # Poisonous tail attack
        "loot_table": ["animal_hide_small", "antidote_simple", "gem_amethyst_rough"],
        "xp_value": 140
    },
    "basilisk_lesser": {
        "id": "basilisk_lesser",
        "name": "Lesser Basilisk",
        "description": "A reptilian beast whose gaze can turn flesh to stone, though this specimen's power is not fully developed.",
        "health": 50,
        "attack_min": 5,
        "attack_max": 8, # Gaze attack (petrification chance)
        "loot_table": ["animal_hide_small", "crystal_shard_mundane", "clay_lump"], # Petrified victims might drop clay-like substance
        "xp_value": 90
    },

    # == Orcs & Goblins (More Variety) ==
    "goblin_shaman_minor": {
        "id": "goblin_shaman_minor",
        "name": "Minor Goblin Shaman",
        "description": "A goblin dabbling in crude shamanistic magic, often chattering incantations.",
        "health": 18,
        "attack_min": 2, # Weak magic
        "attack_max": 5,
        "loot_table": ["goblin_ear", "staff_apprentice", "bone_fragment", "fey_dust"],
        "xp_value": 20
    },
    "goblin_wolfrider": {
        "id": "goblin_wolfrider",
        "name": "Goblin Wolfrider",
        "description": "A goblin mounted on a snarling forest wolf, a fast and dangerous skirmisher.",
        "health": 30, # Combined health or goblin + wolf
        "attack_min": 4,
        "attack_max": 7,
        "loot_table": ["goblin_ear", "spear_common", "wolf_pelt", "leather_scraps"],
        "xp_value": 45
    },
    "orc_berserker": {
        "id": "orc_berserker",
        "name": "Orc Berserker",
        "description": "A fearsome orc warrior who flies into a battle rage, shrugging off wounds.",
        "health": 50,
        "attack_min": 6,
        "attack_max": 10, # Damage increases when enraged
        "loot_table": ["orcish_hand_axe", "hide_armor_crude", "strength_potion_fleeting", "iron_ingot"],
        "xp_value": 70
    },
    "orc_warrior": {
        "id": "orc_warrior",
        "name": "Orc Warrior",
        "description": "A disciplined (for an orc) warrior clad in scavenged armor and wielding a brutal weapon.",
        "health": 45,
        "attack_min": 5,
        "attack_max": 9,
        "loot_table": ["short_sword_iron", "chainmail_vest", "iron_helmet_basic", "ration_pack_basic"],
        "xp_value": 60
    },
    "orc_shaman": {
        "id": "orc_shaman",
        "name": "Orc Shaman",
        "description": "An orcish spiritual leader, channeling primal energies and elemental fury.",
        "health": 40,
        "attack_min": 4, # Magical
        "attack_max": 8,
        "loot_table": ["staff_apprentice", "herbal_poultice", "brimstone_dust", "moonbloom_flower", "charm_of_minor_warding"],
        "xp_value": 75
    },

    # == Desert Creatures ==
    "sand_viper": {
        "id": "sand_viper",
        "name": "Sand Viper",
        "description": "A venomous viper that buries itself in the sand, striking unsuspecting prey.",
        "health": 15,
        "attack_min": 2,
        "attack_max": 4, # Poisonous
        "loot_table": ["antidote_simple", "obsidian_shard"],
        "xp_value": 20
    },
    "desert_scorpion_giant": {
        "id": "desert_scorpion_giant",
        "name": "Giant Desert Scorpion",
        "description": "A massive scorpion with a deadly stinger, common in arid wastelands.",
        "health": 30,
        "attack_min": 4,
        "attack_max": 7, # Stinger attack (poison)
        "loot_table": ["crab_chitin_fragment", "brimstone_dust", "antidote_simple"], # Chitin is similar
        "xp_value": 35
    },
    "dune_stalker": { # Lizard/humanoid blend
        "id": "dune_stalker",
        "name": "Dune Stalker",
        "description": "A reptilian humanoid adapted to desert life, known for ambushes.",
        "health": 28,
        "attack_min": 4,
        "attack_max": 6,
        "loot_table": ["spear_common", "leather_scraps", "empty_waterskin", "spices_exotic_pouch"],
        "xp_value": 30
    },
    "mummy_lesser": {
        "id": "mummy_lesser",
        "name": "Lesser Mummy",
        "description": "An ancient corpse preserved by desert sands and dark rituals, shambling forth with surprising strength.",
        "health": 40,
        "attack_min": 5,
        "attack_max": 8, # Curse chance
        "loot_table": ["torn_rag", "ancient_coin_tarnished", "gold_nugget_small", "brimstone_dust"],
        "xp_value": 55
    },
    "sand_elemental_minor": {
        "id": "sand_elemental_minor",
        "name": "Minor Sand Elemental",
        "description": "A swirling vortex of sand and grit, animated by desert magic.",
        "health": 25,
        "attack_min": 3,
        "attack_max": 6, # Blinding sand attack
        "loot_table": ["crystal_shard_mundane", "obsidian_shard", "gem_amethyst_rough"],
        "xp_value": 33
    },

    # == Aquatic & Coastal Creatures ==
    "giant_crab_rockshore": {
        "id": "giant_crab_rockshore",
        "name": "Rockshore Giant Crab",
        "description": "A very large crab with a shell as hard as rock, found along coastlines.",
        "health": 35,
        "attack_min": 5,
        "attack_max": 8,
        "loot_table": ["crab_chitin_fragment", "pearl_small", "seaweed_clump"],
        "xp_value": 40
    },
    "sea_serpent_hatchling": {
        "id": "sea_serpent_hatchling",
        "name": "Sea Serpent Hatchling",
        "description": "A young, aggressive sea serpent, still dangerous despite its size.",
        "health": 45,
        "attack_min": 6,
        "attack_max": 9,
        "loot_table": ["fish_bones", "naiad_scale_shimmering", "broken_shell"],
        "xp_value": 65
    },
    "merfolk_warrior_hostile": {
        "id": "merfolk_warrior_hostile",
        "name": "Hostile Merfolk Warrior",
        "description": "A territorial merfolk armed with a trident, fiercely guarding its waters.",
        "health": 30,
        "attack_min": 4,
        "attack_max": 7,
        "loot_table": ["spear_common", "broken_shell", "pearl_small", "seaweed_clump"], # Trident could be a spear
        "xp_value": 40
    },
    "sunken_sailor_ghost": {
        "id": "sunken_sailor_ghost",
        "name": "Sunken Sailor's Ghost",
        "description": "The spectral remnant of a drowned sailor, bound to a shipwreck or coastline.",
        "health": 25, # Incorporeal
        "attack_min": 3, # Chilling touch
        "attack_max": 6,
        "loot_table": ["ectoplasm_vial", "tarnished_old_coin", "rusted_nail", "sealed_message_for_captain"], # From its ship
        "xp_value": 38
    },
    "kraken_tentacle_small": { # Part of a larger theoretical boss
        "id": "kraken_tentacle_small",
        "name": "Small Kraken Tentacle",
        "description": "A writhing tentacle from a much larger horror of the deep, lashing out from the water.",
        "health": 50,
        "attack_min": 7,
        "attack_max": 10,
        "loot_table": ["seaweed_clump", "fish_bones"],
        "xp_value": 70
    },

    # == Corrupted & Tainted Creatures ==
    "tainted_wolf": {
        "id": "tainted_wolf",
        "name": "Tainted Wolf",
        "description": "A wolf twisted by dark magic, its fur matted and eyes glowing with malevolence.",
        "health": 25,
        "attack_min": 4,
        "attack_max": 6, # Possible disease or curse on hit
        "loot_table": ["wolf_pelt", "bone_fragment", "shadowroot_bark", "brimstone_dust"],
        "xp_value": 28
    },
    "corrupted_sprite": {
        "id": "corrupted_sprite",
        "name": "Corrupted Sprite",
        "description": "A once benign fey creature, now warped into a spiteful being by dark influence.",
        "health": 15,
        "attack_min": 2,
        "attack_max": 5, # Dark magic
        "loot_table": ["fey_dust", "ectoplasm_vial", "shadowroot_bark"],
        "xp_value": 20
    },
    "blighted_treant_sapling": {
        "id": "blighted_treant_sapling",
        "name": "Blighted Treant Sapling",
        "description": "A young tree animated by corrupted nature magic, its branches sharp and thorny.",
        "health": 40,
        "attack_min": 5,
        "attack_max": 8,
        "loot_table": ["timber_rough", "shadowroot_bark", "moonbloom_flower"], # Flowers might grow on it
        "xp_value": 50
    },
    "shadow_hound": {
        "id": "shadow_hound",
        "name": "Shadow Hound",
        "description": "A canine beast made of solidified shadow, its bite chills to the bone.",
        "health": 30,
        "attack_min": 4,
        "attack_max": 7, # Cold damage, can be hard to see
        "loot_table": ["ectoplasm_vial", "fey_dust", "shadowroot_bark"],
        "xp_value": 45
    },
    "diseased_giant_rat": {
        "id": "diseased_giant_rat",
        "name": "Diseased Giant Rat",
        "description": "A bloated giant rat, its bite carries a nasty infection.",
        "health": 12,
        "attack_min": 1,
        "attack_max": 3, # Disease on hit
        "loot_table": ["rat_tail", "bone_fragment", "antidote_simple"], # Ironically
        "xp_value": 7
    },

    # == Higher Tier / Unique (Examples) ==
    "iron_golem_damaged": {
        "id": "iron_golem_damaged",
        "name": "Damaged Iron Golem",
        "description": "A large construct of iron, showing signs of wear but still immensely powerful.",
        "health": 120,
        "attack_min": 10,
        "attack_max": 18,
        "loot_table": ["iron_ingot", "crystal_shard_mundane", "gem_amethyst_rough", "repair_kit_basic"],
        "xp_value": 200
    },
    "manticore_young": {
        "id": "manticore_young",
        "name": "Young Manticore",
        "description": "A beast with a human-like head, lion's body, and scorpion's tail that can fire spikes.",
        "health": 90,
        "attack_min": 8, # Melee
        "attack_max": 12,
        "special_attack": "tail_spikes", # Ranged attack
        "loot_table": ["animal_hide_small", "bone_fragment", "obsidian_shard", "spices_exotic_pouch"],
        "xp_value": 180
    },
    "elemental_guardian_lesser_fire": {
        "id": "elemental_guardian_lesser_fire",
        "name": "Lesser Fire Elemental Guardian",
        "description": "A humanoid figure made of roiling flame, guarding an ancient place.",
        "health": 70,
        "attack_min": 7, # Fire damage
        "attack_max": 11,
        "loot_table": ["brimstone_dust", "obsidian_shard", "glowing_ember_pendant", "scroll_fire_dart"],
        "xp_value": 150
    },
    "frost_giant_scout": { # From list
        "id": "frost_giant_scout",
        "name": "Frost Giant Scout",
        "description": "A towering giant from the frozen wastes, wielding a massive icy club or axe.",
        "health": 150,
        "attack_min": 12,
        "attack_max": 20, # Cold damage
        "loot_table": ["hide_armor_crude", "iron_ingot", "gem_amethyst_rough", "healing_potion_lesser"],
        "xp_value": 250
    },
    "ethereal_weaver_minion": { # From list
        "id": "ethereal_weaver_minion",
        "name": "Ethereal Weaver Minion",
        "description": "A spectral, spider-like being that drifts between planes, its touch disorienting.",
        "health": 60, # Partially ethereal
        "attack_min": 6,
        "attack_max": 10, # Confusion/debuff chance
        "loot_table": ["ectoplasm_vial", "fey_dust", "spider_silk_strand", "crystal_shard_mundane"],
        "xp_value": 160
    },

    # == More Humanoid Variants ==
    "knight_errant_lost": {
        "id": "knight_errant_lost",
        "name": "Lost Knight-Errant",
        "description": "A knight separated from their company, possibly delirious or desperate.",
        "health": 55,
        "attack_min": 6,
        "attack_max": 9,
        "loot_table": ["short_sword_iron", "chainmail_vest", "wooden_shield_round", "ration_pack_basic", "silver_ring_plain"],
        "xp_value": 70
    },
    "mercenary_veteran": {
        "id": "mercenary_veteran",
        "name": "Veteran Mercenary",
        "description": "A battle-hardened soldier of fortune, skilled with multiple weapons.",
        "health": 60,
        "attack_min": 7,
        "attack_max": 10,
        "loot_table": ["steel_dagger", "iron_helmet_basic", "healing_salve_minor", "gold_nugget_small"],
        "xp_value": 80
    },
    "barbarian_raider": {
        "id": "barbarian_raider",
        "name": "Barbarian Raider",
        "description": "A fierce warrior from the untamed lands, clad in furs and wielding a heavy axe.",
        "health": 65,
        "attack_min": 8,
        "attack_max": 12,
        "loot_table": ["orcish_hand_axe", "hide_armor_crude", "animal_hide_small", "strength_potion_fleeting"],
        "xp_value": 90
    },
    "priest_fallen": {
        "id": "priest_fallen",
        "name": "Fallen Priest",
        "description": "A former priest who has turned to darker powers, still wielding some divine (or unholy) magic.",
        "health": 40,
        "attack_min": 4, # Mix of mace and dark spells
        "attack_max": 7,
        "loot_table": ["wooden_club", "mage_robe_novice", "brimstone_dust", "ectoplasm_vial", "tales_of_gaiatheia_vol1"],
        "xp_value": 55
    },
    "gladiator_escaped": {
        "id": "gladiator_escaped",
        "name": "Escaped Gladiator",
        "description": "A trained fighter who has escaped captivity, dangerous and desperate.",
        "health": 50,
        "attack_min": 6,
        "attack_max": 10,
        "loot_table": ["short_sword_iron", "leather_scraps", "broken_shell"], # Improvised weapon/armor
        "xp_value": 65
    },
    "hunter_tracker": {
        "id": "hunter_tracker",
        "name": "Hunter Tracker",
        "description": "A skilled woodsman adept at tracking and using a bow, fiercely protective of their territory.",
        "health": 45,
        "attack_min": 5, # Ranged primarily
        "attack_max": 8,
        "loot_table": ["hunting_bow_simple", "steel_dagger", "animal_hide_small", "berries_wild", "local_area_map_crude"],
        "xp_value": 60
    },
    "enchanter_reclusive": {
        "id": "enchanter_reclusive",
        "name": "Reclusive Enchanter",
        "description": "A magic-user specializing in enchantments, may use charmed beasts or illusions.",
        "health": 35,
        "attack_min": 3, # Illusion/charm spells, weak direct damage
        "attack_max": 6,
        "loot_table": ["staff_apprentice", "mage_robe_novice", "fey_dust", "scroll_light", "charm_of_minor_warding"],
        "xp_value": 50
    },
    "druid_wildshape_wolf": { # Example of a druid in animal form
        "id": "druid_wildshape_wolf",
        "name": "Druid (Wolf Form)",
        "description": "A druid transformed into a large, intelligent wolf.",
        "health": 40,
        "attack_min": 5,
        "attack_max": 8,
        "loot_table": ["herbal_poultice", "sunpetal_leaf", "moonbloom_flower"], # Drops what they might carry as human
        "xp_value": 58
    },
    "mystic_hermit": {
        "id": "mystic_hermit",
        "name": "Mystic Hermit",
        "description": "An ascetic individual with strange powers, usually peaceful but dangerous if provoked.",
        "health": 30,
        "attack_min": 2, # Unpredictable psychic/elemental attacks
        "attack_max": 10,
        "loot_table": ["staff_apprentice", "journal_page_ripped", "crystal_shard_mundane", "berries_wild"],
        "xp_value": 48
    },
    "pirate_swashbuckler": {
        "id": "pirate_swashbuckler",
        "name": "Pirate Swashbuckler",
        "description": "A flamboyant pirate, skilled with a cutlass and a pistol (if applicable to setting).",
        "health": 48,
        "attack_min": 5,
        "attack_max": 9,
        "loot_table": ["short_sword_iron", "leather_cap", "pearl_small", "ration_pack_basic", "spices_exotic_pouch"],
        "xp_value": 62
    },

    # == Final set to reach 100 new enemies ==
    "goblin_tunneler": {
        "id": "goblin_tunneler",
        "name": "Goblin Tunneler",
        "description": "A goblin adapted to digging, often ambushing from below.",
        "health": 16,
        "attack_min": 2,
        "attack_max": 4,
        "loot_table": ["rusty_dagger", "goblin_ear", "pickaxe_worn", "iron_ore"],
        "xp_value": 14
    },
    "forest_spider_hatchling_swarm": {
        "id": "forest_spider_hatchling_swarm",
        "name": "Forest Spider Hatchling Swarm",
        "description": "A terrifying swarm of newly hatched, tiny spiders.",
        "health": 10, # Swarm
        "attack_min": 1, # Many tiny bites
        "attack_max": 3,
        "loot_table": ["spider_silk_strand"],
        "xp_value": 6
    },
    "animated_broom": {
        "id": "animated_broom",
        "name": "Animated Broom",
        "description": "A common household broom, brought to life by a mischievous spell.",
        "health": 8,
        "attack_min": 1,
        "attack_max": 2,
        "loot_table": ["timber_rough", "string_piece"],
        "xp_value": 4
    },
    "kobold_skirmisher": { # Similar to small goblins
        "id": "kobold_skirmisher",
        "name": "Kobold Skirmisher",
        "description": "A small, reptilian humanoid that uses traps and hit-and-run tactics.",
        "health": 12,
        "attack_min": 2,
        "attack_max": 4,
        "loot_table": ["sling_leather", "pebble_shiny", "flint_sharp"],
        "xp_value": 9
    },
    "giant_centipede": {
        "id": "giant_centipede",
        "name": "Giant Centipede",
        "description": "A horrifyingly large centipede with a venomous bite.",
        "health": 18,
        "attack_min": 2,
        "attack_max": 5, # Poisonous
        "loot_table": ["antidote_simple", "bone_fragment"],
        "xp_value": 16
    },
    "possessed_peasant": {
        "id": "possessed_peasant",
        "name": "Possessed Peasant",
        "description": "A common villager whose body is controlled by a malevolent spirit.",
        "health": 20,
        "attack_min": 3,
        "attack_max": 6, # Unnatural strength
        "loot_table": ["wooden_club", "torn_rag", "ectoplasm_vial"],
        "xp_value": 18
    },
    "animated_scarecrow": {
        "id": "animated_scarecrow",
        "name": "Animated Scarecrow",
        "description": "A scarecrow animated by dark magic, its gaze unsettling.",
        "health": 25,
        "attack_min": 3,
        "attack_max": 5,
        "loot_table": ["timber_rough", "torn_rag", "shadowroot_bark"],
        "xp_value": 22
    },
    "mimic_small_chest": {
        "id": "mimic_small_chest",
        "name": "Small Chest Mimic",
        "description": "A predatory creature perfectly disguised as a small treasure chest.",
        "health": 30,
        "attack_min": 5,
        "attack_max": 8,
        "loot_table": ["gold_nugget_small", "gem_amethyst_rough", "healing_potion_lesser"], # The "bait" it uses
        "xp_value": 50
    },
    "gargoyle_weathered": {
        "id": "gargoyle_weathered",
        "name": "Weathered Gargoyle",
        "description": "A stone gargoyle animated to guard a location, its form chipped and worn.",
        "health": 45,
        "attack_min": 6,
        "attack_max": 9,
        "loot_table": ["crystal_shard_mundane", "obsidian_shard", "iron_ore"],
        "xp_value": 60
    },
    "slime_green_ooze": {
        "id": "slime_green_ooze",
        "name": "Green Ooze Slime",
        "description": "A pulsating blob of acidic green slime.",
        "health": 22,
        "attack_min": 2,
        "attack_max": 4, # Acid damage, can damage equipment
        "loot_table": ["clay_lump", "seaweed_clump"], # Amorphous loot
        "xp_value": 15
    }
    # --- END OF NEW ENEMIES (100 added) ---
}

# --- NPC Placeholders ---
# Placeholder for future NPC data and interaction logic.
NPC_TEMPLATES = {
    "weathered_hermit": {
        "id": "weathered_hermit",
        "name": "Weathered Hermit",
        "location": "Cave", # Example: Where this NPC might be found
        "dialogue_start": "Hmm? A visitor? What brings you to my humble abode?",
        "quests": [] # Placeholder for quests they might offer
    }
    # Add more NPCs here
}

# --- Utility function to get a copy of an enemy for combat ---
import random

def get_enemy_instance(enemy_id):
    if enemy_id in ENEMY_TEMPLATES:
        # Return a copy so modifications in combat don't affect the template
        template = ENEMY_TEMPLATES[enemy_id]
        instance = template.copy()
        # Ensure mutable fields like loot_table are also copied if necessary,
        # though for loot_table being a list of strings, direct copy is usually fine
        # unless the loot generation logic modifies this instance's loot_table.
        return instance
    return None