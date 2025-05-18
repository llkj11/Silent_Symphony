import random
import os 
import json 
import curses # Import curses for the wrapper
import re # For parsing AI responses

import config
import items
import ai_utils # Now has get_ai_model_response
import game_data 
import ui # ui.py now contains display_curses_menu and get_numbered_choice
import character
import combat
import saveload
import entities
import locations # Import the new locations module

# Helper function to safely get text from AI response part
def get_text_from_part(part):
    try:
        return part.text
    except AttributeError:
        return "" # Or some other placeholder if part.text doesn't exist

# --- Helper function to parse observations from AI (specifically from list_points_of_interest) ---
def parse_listed_observations(text_with_observations):
    observations = []
    # Regex to find numbered list items (e.g., "1. Text", "2. More text")
    pattern = re.compile(r"^\s*\d+\.\s*(.+)", re.MULTILINE)
    matches = pattern.findall(text_with_observations)
    if matches:
        observations = [match.strip() for match in matches if match.strip()]
    
    # Fallback if no numbered list is found but text exists
    if not observations and text_with_observations:
        lines = [line.strip() for line in text_with_observations.split('\n') if line.strip() and len(line) > 10 and len(line) < 150]
        observations = lines[:4] # Take up to 4 reasonable lines

    return observations if observations else ["You find nothing of particular interest to investigate closely right now."]

# --- Helper function to parse observations from AI ---
def parse_observations(ai_text):
    observations = []
    # Try to find numbered list items
    pattern = re.compile(r"^\s*\d+\.\s*(.*)", re.MULTILINE)
    matches = pattern.findall(ai_text)
    if matches:
        observations = [match.strip() for match in matches if match.strip()] # Ensure no empty strings
    
    if not observations and ai_text:
        lines = [line.strip() for line in ai_text.split('\n') if line.strip()]
        observations = [line for line in lines if len(line) > 10 and len(line) < 150][:4] # Max 4

    if not observations: # If still no good observations
        return ["You look around, but nothing specific catches your eye right now."]
    return observations


# --- Helper function to parse outcomes from AI response ---
def parse_outcome(ai_text):
    outcome = {"description": ai_text, "item_id": None, "enemy_id": None, "npc_id": None}
    
    # Make tags more flexible with optional spaces around the colon and content
    item_match = re.search(r"\[ITEM_ID\s*:\s*([\w_.-]+)\s*\]", ai_text, re.IGNORECASE)
    if item_match:
        outcome["item_id"] = item_match.group(1)
        ai_text = ai_text.replace(item_match.group(0), "").strip()

    enemy_match = re.search(r"\[ENEMY_ID\s*:\s*([\w_.-]+)\s*\]", ai_text, re.IGNORECASE)
    if enemy_match:
        outcome["enemy_id"] = enemy_match.group(1)
        ai_text = ai_text.replace(enemy_match.group(0), "").strip()

    npc_match = re.search(r"\[NPC_ID\s*:\s*([\w_.-]+)\s*\]", ai_text, re.IGNORECASE)
    if npc_match:
        outcome["npc_id"] = npc_match.group(1)
        ai_text = ai_text.replace(npc_match.group(0), "").strip()
        
    outcome["description"] = ai_text.replace("[]", "").strip() # Clean up empty brackets
    
    # If description becomes empty after stripping tags, create a generic one
    if not outcome["description"]:
        if outcome["item_id"]: outcome["description"] = f"You focus on what seems to be an item..."
        elif outcome["enemy_id"]: outcome["description"] = f"Your attention is drawn to a creature..."
        elif outcome["npc_id"]: outcome["description"] = f"You notice a person..."
        else: outcome["description"] = "You take a moment to observe your surroundings."
    return outcome

# --- Helper function to get a random enemy from location's encounter groups ---
def get_random_enemy_for_location(location_id, specific_group=None):
    current_location_data = locations.LOCATIONS.get(location_id)
    if not current_location_data:
        return None

    encounter_group_names_for_location = current_location_data.get('encounter_groups', [])
    if not encounter_group_names_for_location:
        return None # No encounter groups defined for this location

    chosen_group_name = None
    if specific_group and specific_group in encounter_group_names_for_location:
        # If a specific, valid group is requested for this location, use it
        chosen_group_name = specific_group
    elif specific_group: # A specific group was asked for, but it's not valid for this location
        if config.DEBUG_MODE: print(f"DEBUG: Requested specific_group '{specific_group}' not valid for location '{location_id}'. Falling back.")
        # Fallback to random choice if specific group isn't valid for the location
        chosen_group_name = random.choice(encounter_group_names_for_location) if encounter_group_names_for_location else None
    else:
        # Pick one of the location's encounter groups randomly if no specific group requested
        chosen_group_name = random.choice(encounter_group_names_for_location) if encounter_group_names_for_location else None
    
    if not chosen_group_name:
        return None # Could not determine an encounter group

    encounter_list = locations.ENCOUNTER_GROUPS.get(chosen_group_name, [])
    
    if not encounter_list:
        return None # Chosen group is empty or not found

    # Weighted random choice from the encounter list
    total_weight = sum(entry.get("weight", 0) for entry in encounter_list)
    if total_weight == 0: # Avoid division by zero if all weights are 0
        # Fallback to uniform random choice if weights are problematic
        return random.choice(encounter_list).get("enemy_id") if encounter_list else None

    random_pick = random.uniform(0, total_weight)
    current_sum = 0
    for entry in encounter_list:
        current_sum += entry.get("weight", 0)
        if random_pick <= current_sum:
            return entry.get("enemy_id")
    return None # Should not be reached if weights are positive

# --- New Helper: Process POI Loot Table ---
def process_poi_loot(loot_table_ids):
    found_items = [] # List of item_ids
    if not loot_table_ids: return found_items
    for table_id in loot_table_ids:
        table = locations.POI_LOOT_TABLES.get(table_id, [])
        for loot_entry in table:
            if random.random() <= loot_entry.get("chance", 0):
                qty = random.randint(loot_entry.get("min_qty", 1), loot_entry.get("max_qty", 1))
                for _ in range(qty):
                    found_items.append(loot_entry["item_id"])
    return found_items

def game():
    player = None
    saveload.ensure_save_directory()

    print("Welcome to The Silent Symphony - Main Menu")
    menu_options = ["Start New Game", "Load Game"]
    available_saves = saveload.list_save_files()
    if not available_saves: 
        print("(No save files found to load)")
    
    initial_choice = ui.get_numbered_choice("What would you like to do?", menu_options)

    if initial_choice == "Load Game":
        if available_saves:
            print("\nAvailable save games:")
            load_options = available_saves + ["[Back to Main Menu]"] 
            chosen_save_name = ui.get_numbered_choice("Select a game to load:", load_options)
            
            if chosen_save_name == "[Back to Main Menu]":
                print("Returning to main menu options...")
                if "Start New Game" in menu_options: 
                    initial_choice = "Start New Game"
                else: 
                    print("Error: Cannot go back to new game. Exiting.")
                    return
            else:
                loaded_player_data = saveload.load_game_state(chosen_save_name)
                if loaded_player_data:
                    player = loaded_player_data
                    if player.get('location') not in locations.LOCATIONS:
                        print(f"Warning: Loaded location '{player.get('location')}' unknown. Resetting to start.")
                        player['location'] = "beach_starting"
                        player['last_described_location'] = None
                    print(f"Game '{chosen_save_name}' loaded successfully!")
                else:
                    print("Failed to load game. Starting a new game instead.")
                    initial_choice = "Start New Game" 
        else:
            print("No save games found to load. Starting a new game.")
            initial_choice = "Start New Game"

    if initial_choice == "Start New Game" and player is None: 
        player = character.character_creation()
    
    if not player: 
        print("No character loaded or created. Exiting game.")
        return

    game_over = False
    print("\n--- Game Start ---")
    main_game_actions = {
        "1": "Explore this area",
        "2": "Move to another area",
        "3": "Manage Inventory", 
        "4": "View character stats",
        "5": "Save Game",
        "6": "Quit game"
    }
    
    current_location_id = player['location']
    current_location_data = locations.LOCATIONS.get(current_location_id)

    if not current_location_data:
        print(f"ERROR: Current location ID '{current_location_id}' not found in locations.py! Exiting.")
        return

    if player.get('last_described_location') != current_location_id:
        description_prompt = current_location_data.get('description_first_visit_prompt', f"You are at {current_location_data.get('name', current_location_id)}.")
        ai_response_obj = ai_utils.get_ai_model_response(description_prompt)
        desc_text = f"You arrive at {current_location_data.get('name', 'this new area')}."
        
        try:
            if isinstance(ai_response_obj, dict) and ai_response_obj.get("error_message"):
                if config.DEBUG_MODE: print(f"DEBUG: AI error for initial loc desc: {ai_response_obj.get('error_message')}")
                desc_text = f"{desc_text} You take a moment to get your bearings. (AI communication issue)"
            elif config.AI_PROVIDER == "GEMINI":
                if hasattr(ai_response_obj, 'candidates') and ai_response_obj.candidates and \
                   hasattr(ai_response_obj.candidates[0], 'content') and hasattr(ai_response_obj.candidates[0].content, 'parts') and \
                   ai_response_obj.candidates[0].content.parts:
                    processed_for_initial_desc = False
                    for part in ai_response_obj.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            if part.function_call.name == "narrative_outcome":
                                desc_text = part.function_call.args.get('narrative_text', desc_text)
                            else:
                                if config.DEBUG_MODE: print(f"DEBUG: Gemini AI attempted unexpected function '{part.function_call.name}' for initial loc desc.")
                            processed_for_initial_desc = True; break
                    if not processed_for_initial_desc and ai_response_obj.candidates[0].content.parts:
                        desc_text = get_text_from_part(ai_response_obj.candidates[0].content.parts[0]) or desc_text
            elif config.AI_PROVIDER == "OPENAI":
                if hasattr(ai_response_obj, 'choices') and ai_response_obj.choices and \
                   hasattr(ai_response_obj.choices[0], 'message'):
                    message = ai_response_obj.choices[0].message
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            if tool_call.function.name == "narrative_outcome":
                                args = json.loads(tool_call.function.arguments)
                                desc_text = args.get('narrative_text', desc_text)
                                break # Assuming one function call for initial description
                            else:
                                if config.DEBUG_MODE: print(f"DEBUG: OpenAI AI attempted unexpected function '{tool_call.function.name}' for initial loc desc.")
                    elif message.content:
                        desc_text = message.content
            
            if not desc_text.strip() or "[AI Fallback" in desc_text or "[AI Error" in desc_text or "[AI prompt blocked" in desc_text:
                fallback_message = f"Having just arrived at {current_location_data.get('name', 'this new area')}, you take a moment to get your bearings."
                display_message = desc_text if ('[AI Fallback' in desc_text or '[AI Error' in desc_text or '[AI prompt blocked' in desc_text) else fallback_message
                print(f"\n{display_message}")
                if config.DEBUG_MODE and desc_text.strip() and desc_text != display_message: 
                    print(f"DEBUG: AI issue for initial loc desc. Fallback used. Original AI text: '{desc_text}'")
            else:
                print(f"\n{desc_text}")
        except Exception as e:
            print(f"Error processing initial location AI response: {e}")
            if config.DEBUG_MODE: import traceback; traceback.print_exc()
            print(f"\nHaving just arrived at {current_location_data.get('name', 'this new area')}, you take a moment to get your bearings. (Exception during AI processing)")
        player['last_described_location'] = current_location_id

    while not game_over:
        current_location_id = player['location']
        current_location_data = locations.LOCATIONS.get(current_location_id)
        if not current_location_data: 
            print(f"ERROR: Location '{current_location_id}' is invalid! Resetting to start.")
            player['location'] = "beach_starting"; player['last_described_location'] = None; continue 

        print(f"\n--- Current Location: {current_location_data.get('name', current_location_id)} ---")
        print("\nWhat would you like to do?")
        action_choices_display = [f"{key}. {value}" for key, value in main_game_actions.items()]
        for option_display in action_choices_display:
            print(option_display)
        choice_key = input("> ").strip()

        if choice_key in main_game_actions:
            selected_action = main_game_actions[choice_key]
            
            if selected_action == 'Explore this area':
                print("\nYou decide to look around more closely...")
                
                # --- Stage 1: Select POIs from Location Definition ---
                defined_pois_for_location = current_location_data.get('defined_pois', [])
                available_pois_to_present = []
                if defined_pois_for_location:
                    # Select a subset of POIs to present to the player (e.g., 2 to 4)
                    num_pois_to_offer = min(len(defined_pois_for_location), random.randint(2, 4))
                    available_pois_to_present = random.sample(defined_pois_for_location, num_pois_to_offer)
                
                if not available_pois_to_present:
                    print("You scan the area intently, but nothing specific catches your eye for closer investigation right now.")
                    # Optional: Generic small item find even if no POIs presented
                    if random.random() < 0.1: 
                        generic_finds = current_location_data.get('items_common_find', ["pebble_shiny"])
                        if generic_finds:
                            found_item_id = random.choice(generic_finds)
                            if found_item_id in items.ITEM_DB:
                                player['inventory'].append(found_item_id)
                                print(f"However, you idly pick up a {items.ITEM_DB[found_item_id]['name']}! Added to inventory.")
                    continue

                # --- Stage 2: Player Chooses a POI ---
                print("\nYou notice:")
                poi_display_texts = [poi.get('display_text_for_player_choice', "An unknown point of interest.") for poi in available_pois_to_present]
                options_for_choice = poi_display_texts + ["Ignore these and look around generally"]
                chosen_poi_display_text = ui.get_numbered_choice("What do you want to investigate further?", options_for_choice)

                # --- Stage 3: Resolve Investigation ---
                outcome_prompt = ""
                determined_item_ids_to_give = []
                determined_enemy_id_to_spawn = None
                # Default to narrative_outcome, specific POI logic might change this
                expected_function_call_name = "narrative_outcome" 
                ai_narrative_context = ""

                if chosen_poi_display_text == "Ignore these and look around generally":
                    ai_narrative_context = "The player chose to look around generally." 
                    if random.random() < 0.25: 
                        common_items = current_location_data.get('items_common_find', [])
                        if common_items:
                            determined_item_ids_to_give.append(random.choice(common_items))
                            expected_function_call_name = "player_discovers_item"
                            ai_narrative_context = f"While looking around generally in '{current_location_data.get('name')}', the player stumbles upon an item."
                    # Temporarily force this path for testing:
                    # elif random.random() < 0.15: 
                    elif True: # FORCED ENEMY ENCOUNTER TEST for 'look around generally'
                        print("DEBUG: Attempting 'look around generally' enemy encounter (chance forced to 100%).") 
                        generic_enemy_groups = current_location_data.get('encounter_groups', ["generic_weak_creatures"])
                        if generic_enemy_groups:
                            group_to_use = random.choice(generic_enemy_groups)
                            print(f"DEBUG: Chosen enemy group for general look around: {group_to_use}") 
                            determined_enemy_id_to_spawn = get_random_enemy_for_location(current_location_id, specific_group=group_to_use)
                            print(f"DEBUG: Determined enemy to spawn from general look around: {determined_enemy_id_to_spawn}") 
                            if determined_enemy_id_to_spawn:
                                expected_function_call_name = "player_encounters_enemy"
                                ai_narrative_context = f"While looking around generally in '{current_location_data.get('name')}', the player is surprised by an enemy."
                            else:
                                print("DEBUG: get_random_enemy_for_location returned None for 'look around generally' despite forced attempt.")
                                # Fallback to narrative if no enemy could be spawned from group
                                ai_narrative_context = f"Player {player['name']} is in '{current_location_data.get('name')}' and looks around generally, finding nothing out of the ordinary."
                                expected_function_call_name = "narrative_outcome"
                    if not determined_item_ids_to_give and not determined_enemy_id_to_spawn: # Ensure it still defaults to narrative if forced paths fail
                        ai_narrative_context = f"Player {player['name']} is in '{current_location_data.get('name')}' and looks around generally, finding nothing out of the ordinary."
                        expected_function_call_name = "narrative_outcome"
                else:
                    chosen_poi_def = next((poi for poi in available_pois_to_present if poi.get('display_text_for_player_choice') == chosen_poi_display_text), None)
                    if chosen_poi_def:
                        poi_type = chosen_poi_def.get('type')
                        ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai', f"The player investigates '{chosen_poi_display_text}'.")
                        if poi_type == "loot_container":
                            is_locked = chosen_poi_def.get('locked', False)
                            # TODO: Implement actual can_unlock logic. For trap testing, assume true.
                            can_unlock = True 
                            is_trapped = random.random() < chosen_poi_def.get('trapped_chance', 0) 
                            if config.DEBUG_MODE: print(f"DEBUG: POI loot_container. Locked: {is_locked}, Can Unlock (temp): {can_unlock}, Trapped Roll: {is_trapped} (Chance: {chosen_poi_def.get('trapped_chance', 0)})")

                            if is_locked and not can_unlock:
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_if_locked', "It's locked.")
                                expected_function_call_name = "narrative_outcome"
                            elif is_trapped:
                                print("DEBUG: Trap sprung on POI!") 
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_if_trap_sprung', "A trap springs!")
                                determined_enemy_id_to_spawn = chosen_poi_def.get('trap_enemy_id')
                                print(f"DEBUG: Trap enemy ID determined: {determined_enemy_id_to_spawn}") 
                                expected_function_call_name = "player_encounters_enemy"
                            else: 
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_on_open', "The player opens it.")
                                determined_item_ids_to_give = process_poi_loot(chosen_poi_def.get('loot_table_ids', []))
                                if determined_item_ids_to_give:
                                    expected_function_call_name = "player_discovers_item"
                                else:
                                    ai_narrative_context += " It appears to be empty."
                                    expected_function_call_name = "narrative_outcome"
                        
                        elif poi_type == "loot_scatter":
                            if random.random() < chosen_poi_def.get('success_chance', 1.0):
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_on_success', "They succeed!")
                                item_to_yield = chosen_poi_def.get('item_id_to_yield')
                                if item_to_yield: determined_item_ids_to_give.append(item_to_yield)
                                if determined_item_ids_to_give:
                                     expected_function_call_name = "player_discovers_item"
                                else: # Success but somehow no item defined
                                     expected_function_call_name = "narrative_outcome"
                            else:
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_on_fail', "They fail.")
                                expected_function_call_name = "narrative_outcome"

                        elif poi_type == "clue_object" or poi_type == "simple_description" or poi_type == "navigation_hint":
                            # These primarily result in narrative outcomes
                            # Game logic for revealing exits or updating quest flags would go here if applicable
                            if poi_type == "navigation_hint" and config.DEBUG_MODE:
                                print(f"DEBUG: Navigation hint POI investigated, reveals: {chosen_poi_def.get('reveals_exit_to')}")
                            expected_function_call_name = "narrative_outcome"
                            # ai_narrative_context is already set from POI def
                        else:
                             expected_function_call_name = "narrative_outcome" # Default for unknown POI types
                    else:
                        ai_narrative_context = f"The player looks at the '{chosen_poi_display_text}' but isn't sure what to make of it."
                        expected_function_call_name = "narrative_outcome"

                # Construct the AI prompt for Stage 3
                if expected_function_call_name == "player_discovers_item":
                    # If multiple items, AI should narrate finding them. We pass first item for tagging guidance.
                    item_id_for_ai_prompt = determined_item_ids_to_give[0] if determined_item_ids_to_give else "some_treasure"
                    item_name_for_ai_prompt = items.ITEM_DB.get(item_id_for_ai_prompt, {}).get("name", item_id_for_ai_prompt.replace("_"," "))
                    outcome_prompt = f"{ai_narrative_context} The player finds {len(determined_item_ids_to_give)} item(s). Craft a short narrative for this discovery and call 'player_discovers_item' with item_id='{item_id_for_ai_prompt}' (if multiple items, this is just one example ID for the function call) and your discovery_narrative."
                elif expected_function_call_name == "player_encounters_enemy":
                    enemy_name_for_ai_prompt = entities.ENEMY_TEMPLATES.get(determined_enemy_id_to_spawn, {}).get("name", "a creature")
                    outcome_prompt = f"{ai_narrative_context} An enemy ({enemy_name_for_ai_prompt}) appears! Craft a short narrative for this encounter and call 'player_encounters_enemy' with enemy_id='{determined_enemy_id_to_spawn}' and your encounter_narrative."
                else: # narrative_outcome
                    outcome_prompt = f"{ai_narrative_context} Describe this scene or outcome. Call 'narrative_outcome' with your narrative_text."

                if config.DEBUG_MODE: print(f"DEBUG (Stage 3 AI Prompt): {outcome_prompt}")
                ai_response_stage3 = ai_utils.get_ai_model_response(outcome_prompt)
                function_called_successfully = False
                try:
                    # ... (Provider-aware response parsing as before) ...
                    # --- GEMINI PATH ---
                    if config.AI_PROVIDER == "GEMINI":
                        if hasattr(ai_response_stage3, 'candidates') and ai_response_stage3.candidates and hasattr(ai_response_stage3.candidates[0], 'content') and hasattr(ai_response_stage3.candidates[0].content, 'parts'):
                            for part in ai_response_stage3.candidates[0].content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    function_call = part.function_call
                                    if config.DEBUG_MODE: print(f"DEBUG: Gemini AI call: {function_call.name}, Args: {function_call.args}")
                                    
                                    if function_call.name == "player_discovers_item":
                                        narrative = function_call.args.get('discovery_narrative', "You find something.")
                                        print(f"\n{narrative}")
                                        if determined_item_ids_to_give: # Use game-determined items
                                            for item_id in determined_item_ids_to_give:
                                                if item_id in items.ITEM_DB:
                                                    player['inventory'].append(item_id)
                                                    print(f"You obtained: {items.ITEM_DB[item_id]['name']}! Added to inventory.")
                                                elif config.DEBUG_MODE: print(f"DEBUG: Game logic provided unknown item_id: {item_id}")
                                        else: # AI called discover but game logic found nothing (should be rare with new flow)
                                            if config.DEBUG_MODE: print(f"DEBUG: AI called discover_item but game logic had no items.")
                                            print("It seemed valuable, but crumbled to dust.")
                                        function_called_successfully = True; break
                                    
                                    elif function_call.name == "player_encounters_enemy":
                                        narrative = function_call.args.get('encounter_narrative', "Danger appears!")
                                        print(f"\n{narrative}")
                                        if determined_enemy_id_to_spawn: # Use game-determined enemy
                                            enemy_instance = entities.get_enemy_instance(determined_enemy_id_to_spawn)
                                            if enemy_instance: combat_result = combat.combat(player, enemy_instance); game_over = True if combat_result == "lost" else game_over
                                            else: print("A menacing presence fades.")
                                        else: # AI called encounter but game logic had no enemy (should be rare)
                                            if config.DEBUG_MODE: print(f"DEBUG: AI called encounter_enemy but game logic had no enemy.")
                                            print("You sense danger, but it quickly passes.")
                                        function_called_successfully = True; break
                                    
                                    elif function_call.name == "narrative_outcome":
                                        narrative = function_call.args.get('narrative_text', "You observe your surroundings quietly."); print(f"\n{narrative}");
                                        function_called_successfully = True; break
                                    else: print("\nA strange feeling washes over you..."); function_called_successfully = True; break
                    # --- OPENAI PATH ---
                    elif config.AI_PROVIDER == "OPENAI":
                        if hasattr(ai_response_stage3, 'choices') and ai_response_stage3.choices and hasattr(ai_response_stage3.choices[0],'message') and ai_response_stage3.choices[0].message.tool_calls:
                            for tool_call in ai_response_stage3.choices[0].message.tool_calls:
                                function_name = tool_call.function.name
                                try: args = json.loads(tool_call.function.arguments)
                                except json.JSONDecodeError: args = {}
                                if config.DEBUG_MODE: print(f"DEBUG: OpenAI AI call: {function_name}, Args: {args}")

                                if function_name == "player_discovers_item":
                                    narrative = args.get('discovery_narrative', "You find something.")
                                    print(f"\n{narrative}")
                                    if determined_item_ids_to_give:
                                        for item_id in determined_item_ids_to_give:
                                            if item_id in items.ITEM_DB: player['inventory'].append(item_id); print(f"You obtained: {items.ITEM_DB[item_id]['name']}! Added to inventory.")
                                            elif config.DEBUG_MODE: print(f"DEBUG: Game logic provided unknown item_id: {item_id}")
                                    else: print("It seemed valuable, but crumbled to dust.")
                                    function_called_successfully = True; break
                                
                                elif function_name == "player_encounters_enemy":
                                    narrative = args.get('encounter_narrative', "Danger appears!")
                                    print(f"\n{narrative}")
                                    if determined_enemy_id_to_spawn:
                                        enemy_instance = entities.get_enemy_instance(determined_enemy_id_to_spawn)
                                        if enemy_instance: combat_result = combat.combat(player, enemy_instance); game_over = True if combat_result == "lost" else game_over
                                        else: print("A menacing presence fades.")
                                    else: print("You sense danger, but it quickly passes.")
                                    function_called_successfully = True; break
                                
                                elif function_name == "narrative_outcome":
                                    narrative = args.get('narrative_text', "You observe your surroundings quietly."); print(f"\n{narrative}");
                                    function_called_successfully = True; break
                                else: print("\nA strange feeling washes over you..."); function_called_successfully = True; break
                    
                    if not function_called_successfully: 
                        # ... (fallback if AI didn't make a valid function call at all in Stage 3)
                        desc_text = "You investigate, but nothing definitive happens."
                        # (Simplified fallback text extraction)
                        print(f"\n{desc_text}")
                except Exception as e_stage3:
                    # ... (exception handling)
                    print(f"Error processing exploration outcome: {e_stage3}")
                    if config.DEBUG_MODE: import traceback; traceback.print_exc()
                    print("\nThe world seems to momentarily warp around your focus, then settles.")
            elif selected_action == 'Move to another area':
                print("\nWhere would you like to go?")
                available_exits = current_location_data.get('exits', {})
                if not available_exits:
                    print("There are no obvious exits from this area.")
                    continue
                exit_options = []
                exit_destinations = [] 
                for direction, destination_id in available_exits.items():
                    destination_name = locations.LOCATIONS.get(destination_id, {}).get('name', destination_id)
                    exit_options.append(f"{direction.capitalize()} (to {destination_name})")
                    exit_destinations.append(destination_id)
                exit_options.append("[Stay Here]")
                chosen_exit_display = ui.get_numbered_choice("Choose a direction:", exit_options)
                if chosen_exit_display != "[Stay Here]":
                    chosen_index = exit_options.index(chosen_exit_display)
                    new_location_id = exit_destinations[chosen_index]
                    player['location'] = new_location_id
                    player['last_described_location'] = None 
                    new_location_data = locations.LOCATIONS.get(new_location_id)
                    if new_location_data:
                        desc_prompt_key = 'description_first_visit_prompt' 
                        description_prompt = new_location_data.get(desc_prompt_key, f"You arrive at {new_location_data.get('name')}.")
                        print(f"\nMoving to {new_location_data.get('name')}...")
                        ai_loc_resp = ai_utils.get_ai_model_response(description_prompt)
                        loc_desc_text = f"You arrive at {new_location_data.get('name', 'the new area')}."
                        if isinstance(ai_loc_resp, dict) and ai_loc_resp.get("error_message"):
                            if config.DEBUG_MODE: print(f"DEBUG: AI error for new loc desc: {ai_loc_resp.get('error_message')}")
                        elif config.AI_PROVIDER == "GEMINI":
                            if hasattr(ai_loc_resp, 'candidates') and ai_loc_resp.candidates and hasattr(ai_loc_resp.candidates[0],'content') and hasattr(ai_loc_resp.candidates[0].content, 'parts'):
                                try:
                                    processed_loc_desc = False
                                    for part in ai_loc_resp.candidates[0].content.parts:
                                        if hasattr(part, 'function_call') and part.function_call:
                                            called_fn = part.function_call
                                            if called_fn.name == "narrative_outcome": loc_desc_text = called_fn.args.get('narrative_text', loc_desc_text)
                                            else: pass # Ignore other functions for loc desc
                                            processed_loc_desc = True; break
                                    if not processed_loc_desc and ai_loc_resp.candidates[0].content.parts: 
                                        loc_desc_text = get_text_from_part(ai_loc_resp.candidates[0].content.parts[0]) or loc_desc_text
                                except Exception as e_loc_parse: print(f"Error parsing new Gemini loc AI response parts: {e_loc_parse}")
                        elif config.AI_PROVIDER == "OPENAI":
                             if hasattr(ai_loc_resp, 'choices') and ai_loc_resp.choices and hasattr(ai_loc_resp.choices[0],'message'):
                                message = ai_loc_resp.choices[0].message
                                if message.tool_calls:
                                    for tool_call in message.tool_calls:
                                        if tool_call.function.name == "narrative_outcome":
                                            try: args = json.loads(tool_call.function.arguments); loc_desc_text = args.get('narrative_text', loc_desc_text); break
                                            except json.JSONDecodeError: pass # Ignore malformed args
                                elif message.content: loc_desc_text = message.content
                        print(f"\n{loc_desc_text}")
                        player['last_described_location'] = new_location_id
                    else:
                        print(f"Error: Could not find data for location {new_location_id}.")
            elif selected_action == 'Manage Inventory': manage_inventory(player)
            elif selected_action == 'View character stats':
                print("\n--- Character Stats ---")
                print(f"Name: {player['name']}")
                print(f"Race: {player['race']}")
                print(f"Origin: {player['origin']}")
                print(f"Star Sign: {player['star_sign']}")
                print(f"Health: {player['health']}/{player['max_health']}")
                print(f"Level: {player['level']}")
                print(f"XP: {player['xp']}/{player['xp_to_next_level']}")
                equipped_weapon_name = items.ITEM_DB[player['equipped_weapon']]['name'] if player['equipped_weapon'] else "None"
                equipped_armor_name = items.ITEM_DB[player['equipped_armor']]['name'] if player['equipped_armor'] else "None"
                equipped_shield_name = items.ITEM_DB[player['equipped_shield']]['name'] if player['equipped_shield'] else "None"
                print(f"Equipped Weapon: {equipped_weapon_name}")
                print(f"Equipped Armor: {equipped_armor_name}")
                print(f"Equipped Shield: {equipped_shield_name}")
            elif selected_action == 'Save Game':
                save_name = input("Enter a name for your save game: ").strip()
                if save_name:
                    saveload.save_game_state(player, save_name)
                else:
                    print("Save name cannot be empty. Game not saved.")
            elif selected_action == 'Quit game':
                print("Thank you for playing The Silent Symphony!")
                game_over = True
        else:
            print("Invalid choice. Please try again.")
        
        if player['health'] <= 0 and not game_over: 
            print("\nYou have succumbed to your wounds. Your journey ends.")
            game_over = True

# --- Inventory Management Function (Curses Version) ---
def curses_inventory_screen(stdscr, player, items_module, config_module): # Add modules to params
    # This function is now primarily a caller for the detailed UI function
    ui.display_curses_inventory(stdscr, player, items_module, config_module)

def manage_inventory(player):
    try:
        # Pass the required modules to the curses_inventory_screen
        curses.wrapper(curses_inventory_screen, player, items, config)
    except curses.error as e:
        print("Curses error occurred. Terminal might be in an odd state.")
        print(f"Error: {e}")
        print("If the display is messed up, try resizing your terminal or restarting it.")
    except Exception as e:
        # Catch any other unexpected error during inventory management
        print(f"An unexpected error occurred in inventory: {e}")
        # Potentially log e for debugging
    finally:
        # curses.wrapper should handle terminal cleanup (curses.endwin()).
        # If not using wrapper, you'd call curses.endwin() here.
        # This space can be used for any additional cleanup if needed after inventory closes.
        pass 

if __name__ == "__main__":
    game() 