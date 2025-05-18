# ai_function_declarations.py

LIST_POINTS_OF_INTEREST_DECLARATION = {
    "name": "list_points_of_interest",
    "description": "Describe 2-4 distinct, concise points of interest or observations a player might notice in their current location. Number each observation for the player to choose from.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "observations_text": {
                "type": "STRING",
                "description": "A string containing a numbered list of 2-4 brief, one-sentence observations. Example: '1. An old, weathered chest lies half-buried in the sand.\n2. Strange footprints lead into the nearby cave.\n3. A faint melody drifts from the forest edge.'"
            }
        },
        "required": ["observations_text"]
    }
}

PLAYER_DISCOVERS_ITEM_DECLARATION = {
    "name": "player_discovers_item",
    "description": "Call this function when the player character discovers or obtains a new item during exploration or as a result of an action. Provide the unique ID of the item found and a short narrative of the discovery.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "item_id": {
                "type": "STRING",
                "description": "The unique database ID of the item found (e.g., 'healing_salve_minor', 'hermits_lost_locket'). This ID must exist in the game's item database."
            },
            "discovery_narrative": {
                "type": "STRING",
                "description": "A short, engaging narrative sentence describing how the player found this specific item (e.g., 'Rynn spots a glint under a rock and uncovers a Rusty Dagger.')."
            }
        },
        "required": ["item_id", "discovery_narrative"]
    }
}

PLAYER_ENCOUNTERS_ENEMY_DECLARATION = {
    "name": "player_encounters_enemy",
    "description": "Call this function when the player character encounters an enemy that will lead to combat. Provide the unique ID of the enemy and a short narrative of how the encounter begins.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "enemy_id": {
                "type": "STRING",
                "description": "The unique database ID of the enemy encountered (e.g., 'goblin_scout', 'giant_sand_crab'). This ID must exist in the game's enemy database."
            },
            "encounter_narrative": {
                "type": "STRING",
                "description": "A short, engaging narrative sentence describing how the player encountered this specific enemy (e.g., 'A Goblin Scout leaps out from behind a bush, brandishing a spear!')."
            }
        },
        "required": ["enemy_id", "encounter_narrative"]
    }
}

NARRATIVE_OUTCOME_DECLARATION = {
    "name": "narrative_outcome",
    "description": "Call this function when the result of the player's action or exploration is purely narrative, a piece of information, a clue, a simple observation, or a puzzle element without an immediate item, enemy, or specific NPC interaction. This is for descriptive text, lore, or minor environmental interactions.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "narrative_text": {
                "type": "STRING",
                "description": "The descriptive text detailing what the player observes, learns, or what happens. (e.g., 'Rynn notices strange markings on the old tree that seem to depict a constellation.', 'The heavy lever creaks but doesn\'t budge.')."
            }
        },
        "required": ["narrative_text"]
    }
}

# We can add more declarations here later, e.g., for NPC interactions, puzzle updates, etc. 