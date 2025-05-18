import random
import os 
import json 
import curses # Import curses for the wrapper
import re # For parsing AI responses

import config
import items
import ai_utils
import game_data 
import ui # ui.py now contains display_curses_menu and get_numbered_choice
import character
import combat
import saveload
import entities
import locations # Import the new locations module

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
def get_random_enemy_for_location(location_id):
    current_location_data = locations.LOCATIONS.get(location_id)
    if not current_location_data or not current_location_data.get('encounter_groups'):
        return None # No encounter groups defined or location not found

    # Pick one of the location's encounter groups randomly
    # (If a location has multiple groups listed, e.g., ["group_A", "group_B"])
    chosen_group_name = random.choice(current_location_data['encounter_groups'])
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
                    # Ensure player location is valid after loading, default if not
                    if player.get('location') not in locations.LOCATIONS:
                        print(f"Warning: Loaded location '{player.get('location')}' unknown. Resetting to start.")
                        player['location'] = "beach_starting"
                        player['last_described_location'] = None # Force redescription
                    print(f"Game '{chosen_save_name}' loaded successfully!")
                else:
                    print("Failed to load game. Starting a new game instead.")
                    initial_choice = "Start New Game" 
        else:
            print("No save games found to load. Starting a new game.")
            initial_choice = "Start New Game"

    if initial_choice == "Start New Game" and player is None: 
        player = character.character_creation() # This now sets location to "beach_starting"
    
    if not player: 
        print("No character loaded or created. Exiting game.")
        return

    game_over = False
    print("\n--- Game Start ---")
    main_game_actions = {
        "1": "Explore this area", # Renamed for clarity
        "2": "Move to another area",
        "3": "Manage Inventory", 
        "4": "View character stats",
        "5": "Save Game",
        "6": "Quit game" # Adjusted numbering
    }
    
    # Initial location description
    current_location_id = player['location']
    current_location_data = locations.LOCATIONS.get(current_location_id)

    if not current_location_data:
        print(f"ERROR: Current location ID '{current_location_id}' not found in locations.py! Exiting.")
        return

    if player.get('last_described_location') != current_location_id:
        description_prompt = current_location_data.get('description_first_visit_prompt', f"You are at {current_location_data.get('name', current_location_id)}.")
        ai_generated_desc = ai_utils.get_ai_description(description_prompt)
        
        if "[AI response had no text" in ai_generated_desc or "[AI Error" in ai_generated_desc or "[AI prompt blocked" in ai_generated_desc:
            print(f"\nHaving just arrived at {current_location_data.get('name', 'this new area')}, you take a moment to get your bearings.")
            if config.DEBUG_MODE:
                print(f"DEBUG: AI failed to provide initial location description. Fallback used. Original error: {ai_generated_desc}")
        else:
            print(f"\n{ai_generated_desc}")
        player['last_described_location'] = current_location_id

    while not game_over:
        current_location_id = player['location'] # Ensure it's fresh each loop turn
        current_location_data = locations.LOCATIONS.get(current_location_id)
        if not current_location_data: # Should be caught on game start, but as a safeguard
            print(f"ERROR: Location '{current_location_id}' is invalid! Resetting to start.")
            player['location'] = "beach_starting"
            player['last_described_location'] = None
            continue 

        print(f"\n--- Current Location: {current_location_data.get('name', current_location_id)} ---")
        
        print("\nWhat would you like to do?")
        action_choices_display = [f"{key}. {value}" for key, value in main_game_actions.items()]
        for option_display in action_choices_display:
            print(option_display)
        
        choice_key = input("> ").strip()

        if choice_key in main_game_actions:
            selected_action = main_game_actions[choice_key]
            
            if selected_action == 'Explore this area':
                print("\nYou decide to explore this area more closely...")
                poi_keywords = current_location_data.get('poi_keywords', ["something interesting", "a minor detail", "a common feature of the area"])
                # Select a few keywords randomly to make the prompt more varied
                num_keywords_to_use = min(len(poi_keywords), 3) # Use up to 3 keywords
                sampled_keywords = random.sample(poi_keywords, num_keywords_to_use) if poi_keywords else []
                
                observation_prompt = f"Player {player['name']} is exploring '{current_location_data.get('name')}'. Based on these potential points of interest or themes ({', '.join(sampled_keywords)}), describe 2-4 distinct, concise observations they might notice. Number them (e.g., '1. A ...'). Keep observations to one sentence."
                raw_observations_text = ai_utils.get_ai_description(observation_prompt)
                
                if config.DEBUG_MODE: print(f"DEBUG (Observations Raw): '{raw_observations_text}'")
                observations = parse_observations(raw_observations_text)

                if not observations or (len(observations) == 1 and "nothing specific" in observations[0].lower()):
                    print(observations[0]) 
                    if random.random() < 0.20: # Chance for generic find
                        generic_finds = current_location_data.get('items_common_find', ["pebble_shiny"])
                        if generic_finds:
                            found_item_id = random.choice(generic_finds)
                            if found_item_id in items.ITEM_DB:
                                item_name = items.ITEM_DB[found_item_id]['name']
                                player['inventory'].append(found_item_id)
                                print(f"While looking around idly, you find a {item_name}! Added to inventory.")
                    continue

                print("\nYou notice a few things:")
                options_for_choice = observations + ["Look around generally (ignore these specifics)"]
                chosen_observation_text = ui.get_numbered_choice("What do you want to investigate further?", options_for_choice)

                outcome_text = ""
                if chosen_observation_text == "Look around generally (ignore these specifics)":
                    default_items = current_location_data.get('items_common_find', ["pebble_shiny"])
                    default_enemy_group = current_location_data.get('encounter_groups',["generic_weak_creatures"])[0] # pick first group for generic enemy
                    default_enemy_id = locations.ENCOUNTER_GROUPS.get(default_enemy_group, [{}])[0].get('enemy_id', 'giant_rat') # pick first enemy from group
                    outcome_prompt = f"Player {player['name']} is in '{current_location_data.get('name')}' and chose to look around generally. Describe a brief, common occurrence. Maybe they find a very common item like [ITEM_ID:{random.choice(default_items)}] or encounter a common creature for this area like [ENEMY_ID:{default_enemy_id}]. Keep it concise and use the [TAGS]."
                    outcome_text = ai_utils.get_ai_description(outcome_prompt)
                else:
                    # Stage 2: Get outcome for the chosen observation
                    outcome_prompt = f"In '{current_location_data.get('name')}', player {player['name']} chose to investigate: '{chosen_observation_text}'. Describe what happens in detail. If an item is found, IMMEDIATELY follow its name or description with its tag [ITEM_ID:item_id_here]. If an NPC is encountered, use [NPC_ID:npc_id_here]. If combat starts, use [ENEMY_ID:enemy_id_here]. Be descriptive but ensure tags are present if applicable."
                    outcome_text = ai_utils.get_ai_description(outcome_prompt)
                
                if config.DEBUG_MODE: print(f"DEBUG (Outcome Raw): '{outcome_text}'")
                parsed_outcome = parse_outcome(outcome_text)
                print(f"\n{parsed_outcome['description']}")

                if parsed_outcome['item_id']:
                    item_id = parsed_outcome['item_id']
                    if item_id in items.ITEM_DB:
                        item_name = items.ITEM_DB[item_id]['name']
                        player['inventory'].append(item_id)
                        print(f"You found a {item_name}! Added to inventory.")
                    elif config.DEBUG_MODE:
                        print(f"DEBUG: AI mentioned item ID '{item_id}' not in ITEM_DB.")
                
                if parsed_outcome['enemy_id']:
                    enemy_id_to_spawn = parsed_outcome['enemy_id']
                    enemy_instance = entities.get_enemy_instance(enemy_id_to_spawn)
                    if enemy_instance:
                        print(f"\nWatch out! A {enemy_instance['name']} appears!")
                        combat_result = combat.combat(player, enemy_instance)
                        if combat_result == "lost": game_over = True
                    elif config.DEBUG_MODE:
                        print(f"DEBUG: AI mentioned enemy ID '{enemy_id_to_spawn}' not in ENEMY_TEMPLATES.")
                elif not parsed_outcome['item_id'] and not parsed_outcome['npc_id'] and random.random() < 0.25: # Chance of random encounter if POI was just flavor
                    enemy_id_to_spawn = get_random_enemy_for_location(current_location_id)
                    if enemy_id_to_spawn:
                        enemy_instance = entities.get_enemy_instance(enemy_id_to_spawn)
                        if enemy_instance:
                            print(f"\nSuddenly, a wild {enemy_instance['name']} appears!")
                            combat_result = combat.combat(player, enemy_instance)
                            if combat_result == "lost": game_over = True
                
                if parsed_outcome['npc_id']:
                    npc_id = parsed_outcome['npc_id']
                    if npc_id in entities.NPC_TEMPLATES:
                        npc_data = entities.NPC_TEMPLATES[npc_id]
                        print(f"You encounter {npc_data['name']}.")
                        print(f"\"{npc_data.get('dialogue_start', 'They look at you expectantly.')}\"")
                    elif config.DEBUG_MODE:
                        print(f"DEBUG: AI mentioned NPC ID '{npc_id}' not in NPC_TEMPLATES.")

            elif selected_action == 'Move to another area':
                print("\nWhere would you like to go?")
                available_exits = current_location_data.get('exits', {})
                if not available_exits:
                    print("There are no obvious exits from this area.")
                    continue

                exit_options = []
                exit_destinations = [] # Parallel list to store destination IDs
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
                    player['last_described_location'] = None # Force re-description of new area
                    
                    # Display new location description immediately after moving
                    new_location_data = locations.LOCATIONS.get(new_location_id)
                    if new_location_data:
                        desc_prompt_key = 'description_first_visit_prompt' # Simple way to always get full desc for now
                        # Could add logic to check if player has 'visited_locations' list for revisit_prompt
                        description_prompt = new_location_data.get(desc_prompt_key, f"You arrive at {new_location_data.get('name')}.")
                        print(f"\nMoving to {new_location_data.get('name')}...")
                        print(f"\n{ai_utils.get_ai_description(description_prompt)}")
                        player['last_described_location'] = new_location_id # Mark as described
                    else:
                        print(f"Error: Could not find data for location {new_location_id}.") # Should not happen
            
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