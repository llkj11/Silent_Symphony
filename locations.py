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

# --- Location Definitions ---
LOCATIONS = {
    "beach_starting": {
        "id": "beach_starting",
        "name": "Shifting Sands Beach",
        "description_first_visit_prompt": "The player has just arrived at the Shifting Sands Beach. Describe the scene atmospherically: the relentless sun, the sound of waves, scattered driftwood, perhaps the distant shimmer of dunes or dark rocks. Convey a sense of new beginnings and underlying mystery or potential danger.",
        "description_revisit_prompt": "The player returns to the Shifting Sands Beach. Briefly remind them of its key features, perhaps noting any subtle changes like the tide or new debris.",
        "poi_keywords": [
            "a large, weathered driftwood log with strange markings",
            "a half-buried, barnacle-encrusted chest",
            "a narrow, almost hidden path leading into the dunes",
            "a flock of unusual seabirds squabbling over something shiny",
            "a tattered piece of sailcloth caught on a rock"
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
        "poi_keywords": [
            "a weathered animal skull half-buried in sand",
            "unusual tracks leading deeper into the dunes",
            "a patch of surprisingly vibrant desert flowers",
            "a glint of metal sticking out from a dune crest",
            "a crumbling, ancient stone marker"
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
        "poi_keywords": [
            "a small cave entrance revealed at low tide", 
            "a shipwrecked crate lodged between rocks",
            "a colony of nesting seabirds on a high ledge",
            "an old, rusted anchor half-submerged in a tide pool",
            "strange, luminescent seaweed clinging to the dark rocks"
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