# locations.py

# --- Encounter Group Definitions ---
# Defines sets of enemies that can be encountered in various locations.
# 'weight' can be used for weighted random selection.
ENCOUNTER_GROUPS = {
    "beach_low_level": [
        {"enemy_id": "giant_sand_crab", "weight": 60},
        {"enemy_id": "sea_serpent_hatchling", "weight": 15},
        {"enemy_id": "goblin_scout", "weight": 25} # Goblins might scavenge beaches
    ],
    "dunes_low_level": [
        {"enemy_id": "desert_scorpion_giant", "weight": 40},
        {"enemy_id": "sand_viper", "weight": 30},
        {"enemy_id": "bandit_archer", "weight": 30} # Bandits might use dunes for ambushes
    ],
    "generic_weak_creatures": [
        {"enemy_id": "giant_rat", "weight": 70},
        {"enemy_id": "cave_bat_swarm", "weight": 30}
    ]
    # Add more encounter groups for different environments/difficulty levels
}

# --- Loot Table Definitions for POIs ---
# Defines what items can be found in specific lootable POIs.
# Structure: "table_id": [{"item_id": "...", "chance": 0.X, "min_qty": 1, "max_qty": 1}, ...]
POI_LOOT_TABLES = {
    "beach_chest_common_loot": [
        {"item_id": "pebble_shiny", "chance": 0.6, "min_qty": 1, "max_qty": 3},
        {"item_id": "broken_shell", "chance": 0.4, "min_qty": 1, "max_qty": 2},
        {"item_id": "healing_salve_minor", "chance": 0.15, "min_qty": 1, "max_qty": 1},
        {"item_id": "small_tarnished_bronze_key", "chance": 0.05, "min_qty": 1, "max_qty": 1}
    ],
    "driftwood_log_etchings_clue": [], # No direct items, but could trigger a flag or quest update later
    "shipwreck_crate_shoreline": [
        {"item_id": "ration_pack_basic", "chance": 0.5, "min_qty": 1, "max_qty": 1},
        {"item_id": "rope_hempen_10ft", "chance": 0.3, "min_qty": 1, "max_qty": 1},
        {"item_id": "rusted_nail", "chance": 0.7, "min_qty": 2, "max_qty": 5}
    ]
}

# --- Location Definitions ---
LOCATIONS = {
    "beach_starting": {
        "id": "beach_starting",
        "name": "Shifting Sands Beach",
        "description_first_visit_prompt": "The player has just arrived at the Shifting Sands Beach. Describe the scene atmospherically: the relentless sun, the sound of waves, scattered driftwood, perhaps the distant shimmer of dunes or dark rocks. Convey a sense of new beginnings and underlying mystery or potential danger.",
        "description_revisit_prompt": "The player returns to the Shifting Sands Beach. Briefly remind them of its key features, perhaps noting any subtle changes like the tide or new debris.",
        "defined_pois": [
            {
                "poi_id": "beach_log_markings",
                "display_text_for_player_choice": "A large, weathered driftwood log with strange markings.",
                "type": "clue_object", # Game logic will know this provides a narrative/clue
                "clue_id_for_ai_narrative": "log_ancient_map_hint", # Hint for AI to narrate
                "interaction_prompt_to_ai": "The player examines the strange markings on the driftwood log. Describe what they see or decipher. This is a clue, not a physical item."
            },
            {
                "poi_id": "beach_chest_barnacled",
                "display_text_for_player_choice": "A half-buried, barnacle-encrusted chest.",
                "type": "loot_container",
                "loot_table_ids": ["beach_chest_common_loot"],
                "locked": True, "key_id": "small_tarnished_bronze_key", "lock_difficulty": 5, 
                "trapped_chance": 1.0, # TEMPORARILY SET TO 1.0 FOR TESTING
                "trap_enemy_id": "giant_sand_crab", 
                "interaction_prompt_to_ai_on_open": "The player manages to open the barnacle-encrusted chest.",
                "interaction_prompt_to_ai_if_locked": "The player tries the barnacle-encrusted chest, but it's firmly locked.",
                "interaction_prompt_to_ai_if_trap_sprung": "As the player tampers with the chest, a trap springs!"
            },
            {
                "poi_id": "beach_dune_path",
                "display_text_for_player_choice": "A narrow, almost hidden path leading into the dunes.",
                "type": "navigation_hint", # Or "hidden_exit"
                "reveals_exit_to": "coastal_dunes_edge", # Could unlock this exit or provide info
                "interaction_prompt_to_ai": "The player investigates the narrow path leading into the dunes. Describe the path and where it seems to lead, hinting at the coastal dunes beyond."
            },
            {
                "poi_id": "beach_seabirds_shiny",
                "display_text_for_player_choice": "A flock of unusual seabirds squabbling over something shiny.",
                "type": "loot_scatter", # A POI that directly yields an item if player interacts successfully
                "item_id_to_yield": "small_tarnished_bronze_key", # Example direct item
                "success_chance": 0.7, # Chance to get the item vs birds fly away with it
                "interaction_prompt_to_ai_on_success": "The player successfully scares off the seabirds and retrieves the shiny object.",
                "interaction_prompt_to_ai_on_fail": "The player startles the seabirds, and they fly off, taking the shiny object with them."
            }
        ],
        "encounter_groups": ["beach_low_level"], # Which sets of enemies can appear here
        "exits": {
            "north": "coastal_dunes_edge",
            "east": "rocky_shoreline_west"
            # "west": "ocean_shallows" # Example for later
        },
        "items_common_find": ["pebble_shiny", "seaweed_clump", "broken_shell"], # Items found generically
        "properties": ["coastal", "sandy_terrain", "open_area", "salt_air"],
        "ambient_sounds_ai_prompt": "Describe the ambient sounds of Shifting Sands Beach: waves, seabirds, wind."
    },
    "coastal_dunes_edge": {
        "id": "coastal_dunes_edge",
        "name": "Edge of the Coastal Dunes",
        "description_first_visit_prompt": "The player has reached the edge of vast coastal dunes. Describe the transition from beach to dunes: rolling hills of sand, sparse, tough vegetation, the sound of wind. Hint at the expanse beyond.",
        "description_revisit_prompt": "The player is back at the edge of the Coastal Dunes. Remind them of the sandy expanse and the path back to the beach.",
        "defined_pois": [
            {
                "poi_id": "dunes_skull", 
                "display_text_for_player_choice": "A weathered animal skull half-buried in sand.",
                "type": "simple_description",
                "interaction_prompt_to_ai": "The player examines the weathered animal skull. Describe its appearance and any thoughts it might provoke."
            }
        ],
        "encounter_groups": ["dunes_low_level", "beach_low_level"], # Can have some overlap
        "exits": {
            "south": "beach_starting",
            "northwest": "dunes_hinterland" # Deeper into the dunes
        },
        "items_common_find": ["flint_sharp", "bent_spoon"],
        "properties": ["coastal_dunes", "sandy_terrain", "exposed", "windy"],
        "ambient_sounds_ai_prompt": "Describe the ambient sounds of the Coastal Dunes edge: wind whistling, distant surf, maybe the skittering of unseen creatures."
    },
    "rocky_shoreline_west": {
        "id": "rocky_shoreline_west",
        "name": "West Rocky Shoreline",
        "description_first_visit_prompt": "The player is on a rugged, rocky shoreline west of the main beach. Jagged black rocks meet the churning sea, and tide pools teem with small life. It feels more secluded and treacherous.",
        "description_revisit_prompt": "The player returns to the West Rocky Shoreline. Briefly mention the dark rocks and crashing waves.",
        "defined_pois": [
             {
                "poi_id": "shoreline_crate",
                "display_text_for_player_choice": "A shipwrecked crate lodged between rocks.",
                "type": "loot_container",
                "loot_table_ids": ["shipwreck_crate_shoreline"],
                "locked": False, 
                "interaction_prompt_to_ai_on_open": "The player manages to break open the shipwrecked crate."
            }
        ],
        "encounter_groups": ["beach_low_level", "giant_crab_rockshore"], # Specific enemy type
        "exits": {
            "east": "beach_starting"
        },
        "items_common_find": ["broken_shell", "seaweed_clump", "crab_chitin_fragment"],
        "properties": ["coastal", "rocky_terrain", "tide_pools", "slippery"],
        "ambient_sounds_ai_prompt": "Describe the ambient sounds of the Rocky Shoreline: crashing waves, seabird cries, water gurgling in crevices."
    }
    # Add more locations as the game expands
} 