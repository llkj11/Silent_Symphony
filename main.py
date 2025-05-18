import random
import os 
import json 
import curses # Import curses for the wrapper

import config
import items
import ai_utils
import game_data 
import ui # ui.py now contains display_curses_menu and get_numbered_choice
import character
import combat
import saveload
import entities

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
        "1": "Explore further",
        "2": "Manage Inventory",
        "3": "View character stats",
        "4": "Save Game",
        "5": "Quit game"
    }

    while not game_over:
        print(f"\n--- Current Location: {player['location']} ---")
        
        if player['location'] != player.get('last_described_location'):
            location_prompt = f"Describe the area '{player['location']}'. The player is a {player['race']} named {player['name']}. Keep it brief, about 2-3 sentences, focusing on atmosphere and potential points of interest."
            print(ai_utils.get_ai_description(location_prompt))
            player['last_described_location'] = player['location']
        
        print("\nWhat would you like to do?")
        action_choices_display = [f"{key}. {value}" for key, value in main_game_actions.items()]
        for option_display in action_choices_display:
            print(option_display)
        
        choice_key = input("> ").strip()

        if choice_key in main_game_actions:
            selected_action = main_game_actions[choice_key]
            if selected_action == 'Explore further':
                print("\nYou decide to explore further...")
                encounter_chance = random.random()
                if encounter_chance < 0.1: 
                    print(ai_utils.get_ai_description(f"Describe a brief, uneventful moment of exploration for {player['name']} in {player['location']}."))
                elif encounter_chance < 0.7: 
                    possible_finds = ["pebble_shiny", "seaweed_clump", "broken_shell", "healing_salve_minor", "rusty_dagger", "leather_scraps"]
                    found_item_id = random.choice(possible_finds)
                    
                    if found_item_id in items.ITEM_DB:
                        found_item_name = items.ITEM_DB[found_item_id]["name"]
                        player['inventory'].append(found_item_id)
                        print(ai_utils.get_ai_description(f"{player['name']} finds a {found_item_name} while exploring {player['location']}. Describe this discovery briefly."))
                        print(f"You found a {found_item_name}! Added to inventory.")
                    else:
                        if config.DEBUG_MODE: 
                            print(f"DEBUG: Error - found_item_id '{found_item_id}' not in ITEM_DB!")
                        print("You found something, but it crumbled to dust...")
                else: 
                    # Select an enemy randomly from templates
                    enemy_id_to_spawn = random.choice(list(entities.ENEMY_TEMPLATES.keys()))
                    enemy_instance = entities.get_enemy_instance(enemy_id_to_spawn)
                    if enemy_instance:
                        print(f"\nSuddenly, a {enemy_instance['name']} appears! {enemy_instance['description']}")
                        combat_result = combat.combat(player, enemy_instance)
                        if combat_result == "lost":
                            print("\nYour journey ends here, for now.")
                            game_over = True
                        elif combat_result == "won":
                            print("You feel a surge of confidence after your victory!")
                            # Placeholder for loot drop based on enemy_instance['loot_table']
                            # For now, just a message
                            print(f"The {enemy_instance['name']} might have dropped something...") 
                    else:
                        print("A menacing shadow flickers, but then is gone...")
            elif selected_action == 'Manage Inventory':
                manage_inventory(player)
            elif selected_action == 'View character stats':
                print("\n--- Character Stats ---")
                print(f"Name: {player['name']}")
                print(f"Race: {player['race']}")
                print(f"Origin: {player['origin']}")
                print(f"Star Sign: {player['star_sign']}")
                print(f"Health: {player['health']}/{player['max_health']}")
                print(f"Level: {player['level']}")
                print(f"XP: {player['xp']}/{player['xp_to_next_level']}")
                # Display equipped items
                equipped_weapon_name = items.ITEM_DB[player['equipped_weapon']]['name'] if player['equipped_weapon'] else "None"
                equipped_armor_name = items.ITEM_DB[player['equipped_armor']]['name'] if player['equipped_armor'] else "None"
                print(f"Equipped Weapon: {equipped_weapon_name}")
                print(f"Equipped Armor: {equipped_armor_name}")
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