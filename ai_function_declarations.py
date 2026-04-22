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

OFFER_CHOICE_DECLARATION = {
    "name": "offer_choice",
    "description": "Call when the player's action naturally leads to a branching micro-decision (e.g., 'Do you reach into the dark crevice, tap it with your spear, or back away?'). Present 2–3 concise options with pre-authored outcome narratives. The engine will ask the player to pick one and print only the chosen option's outcome. Use this to make scenes feel reactive instead of one-shot.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "setup_narrative": {
                "type": "STRING",
                "description": "One or two sentences framing the choice for the player. No questions — just the situation."
            },
            "choices": {
                "type": "ARRAY",
                "description": "2 to 3 options. Each label is short; each outcome_narrative is 1–2 sentences describing what happens if that option is taken.",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "label": {"type": "STRING", "description": "Short imperative label the player will pick from (e.g., 'Reach in carefully')."},
                        "outcome_narrative": {"type": "STRING", "description": "What happens when the player picks this option."}
                    },
                    "required": ["label", "outcome_narrative"]
                }
            }
        },
        "required": ["setup_narrative", "choices"]
    }
}

SET_WORLD_FLAG_DECLARATION = {
    "name": "set_world_flag",
    "description": "Record a narrative flag that should persist across future scenes (e.g., 'heard_rumor_of_captain', 'disturbed_shoreline_shrine'). Use sparingly — only for state that will matter later. Do NOT use for transient moods or one-off observations.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "flag_name": {
                "type": "STRING",
                "description": "A snake_case identifier. Prefix with 'ai_' if unsure about namespacing."
            },
            "scope": {
                "type": "STRING",
                "description": "'global' (default) or 'location' (attached to the current location)."
            },
            "narrative": {
                "type": "STRING",
                "description": "1–2 sentences describing what happened. Will be printed to the player."
            }
        },
        "required": ["flag_name", "narrative"]
    }
}

ADD_FLAVOR_POI_DECLARATION = {
    "name": "add_flavor_poi",
    "description": "Optionally contribute ONE ephemeral observation the player might investigate right now, alongside the game-defined points of interest. Make it small, specific, and grounded in the scene. This POI is purely narrative — no items, enemies, or state changes. If nothing fits the moment, call 'narrative_outcome' with text 'none' instead.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "display_text": {
                "type": "STRING",
                "description": "One short sentence the player will see in the list of things to investigate (e.g., 'A line of ants marches into a crack between two boulders.')."
            },
            "outcome_narrative": {
                "type": "STRING",
                "description": "1–3 sentences for what happens when the player investigates it. Pure description or flavor only."
            }
        },
        "required": ["display_text", "outcome_narrative"]
    }
}

INTRODUCE_NPC_DECLARATION = {
    "name": "introduce_npc",
    "description": (
        "Foreground an existing NPC in the scene — for example, when an NPC approaches the player, calls out, "
        "or otherwise makes themselves part of the current moment. The NPC must already be present at the current "
        "location (the engine will refuse unknown or off-site IDs). After narrating, the engine offers the player "
        "the chance to interact with them. Use this to make NPCs feel proactive; do not use to invent new people."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "npc_id": {
                "type": "STRING",
                "description": "Database ID of the NPC to foreground (e.g., 'morwyn_trader'). Must already be at the player's current location."
            },
            "disposition": {
                "type": "STRING",
                "description": "A short mood/attitude cue for this specific encounter (e.g., 'guarded', 'eager', 'tired'). Does not overwrite the NPC's baseline disposition."
            },
            "narrative": {
                "type": "STRING",
                "description": "1–3 sentences describing how the NPC enters this moment (e.g., 'Morwyn looks up from her bundles as you approach, wiping her hands on a salt-stained rag.')."
            }
        },
        "required": ["npc_id", "narrative"]
    }
}

SKILL_CHECK_DECLARATION = {
    "name": "skill_check",
    "description": "Call when the outcome of the player's action hinges on luck or skill. Provide a difficulty (1–10; 5 is moderate, 8 is hard) and BOTH narratives up-front. The engine will roll and print only the matching one. Prefer this over 'narrative_outcome' when the result could plausibly go either way.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "difficulty": {
                "type": "INTEGER",
                "description": "Target 1–10. Engine rolls 1d10 and succeeds on >= difficulty."
            },
            "description": {
                "type": "STRING",
                "description": "Short description of what the player is attempting (e.g., 'pry the warped lid', 'leap across the gap')."
            },
            "success_narrative": {
                "type": "STRING",
                "description": "Narrative printed on success."
            },
            "failure_narrative": {
                "type": "STRING",
                "description": "Narrative printed on failure. Avoid killing the player; minor setbacks are fine."
            }
        },
        "required": ["difficulty", "description", "success_narrative", "failure_narrative"]
    }
}
