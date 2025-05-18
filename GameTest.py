import random
import json # For saving and loading game state
import os   # For directory and file operations

try:
    import google.genai as genai
    from google.genai import types
    print(f"SDK Version (GameTest.py): {genai.__version__}")
except ImportError:
    print("Google GenAI SDK (google-genai) not installed or module structure changed. Please ensure it is installed correctly: pip install google-genai")
    genai = None
    types = None

# --- Configuration ---
DEBUG_MODE = False # Set to True to enable debug prints for AI calls
# IMPORTANT: Replace 'YOUR_API_KEY' with your actual Google AI Studio API key.
# You can also set the GOOGLE_API_KEY environment variable.
API_KEY = 'AIzaSyDE6KqtzgaRjp_PppUDYbctJxpKbqmvrsw' 
AI_MODEL_NAME = "gemini-2.5-flash-preview-04-17" # Updated to specific 2.5 Flash preview model

# Initialize Google AI Client
global_ai_client = None 
global_generation_config = None 
# global_safety_settings = None 

if genai and types and API_KEY and API_KEY != 'YOUR_API_KEY':
    try:
        global_ai_client = genai.Client(api_key=API_KEY)
        
        # Use GenerateContentConfig
        # Increase max_output_tokens, temporarily remove automatic_function_calling for testing MAX_TOKENS issue
        global_generation_config = types.GenerateContentConfig(
            temperature=0.7, 
            max_output_tokens=1024  # Increased from 150
            # automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True) # Temporarily removed
        )
        print("Initialized GenerateContentConfig (temp=0.7, max_tokens=1024).")

        # global_safety_settings definition remains, but not passed to generate_content if problematic.
        # global_safety_settings = [
        #      types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        #      # ... other settings
        # ]

        print(f"Successfully initialized AI Client for model: {AI_MODEL_NAME}. Using updated GenerateContentConfig. Will use default thinking.")

    except AttributeError as ae: 
        print(f"Error initializing Google AI Client (AttributeError): {ae}")
        print("This might indicate an issue with the google-genai SDK version (e.g. GenerateContentConfig fields). AI features will use fallback.")
        global_ai_client = None
        global_generation_config = None 
    except Exception as e:
        print(f"Error initializing Google AI Client: {e}")
        global_ai_client = None
        global_generation_config = None 
elif not (genai and types):
    print("Skipping AI initialization as the SDK (google.genai or types) is not available.")
elif API_KEY == 'YOUR_API_KEY': 
    print("Skipping AI initialization. API_KEY is still the placeholder 'YOUR_API_KEY'.")

# --- Item Database ---
ITEM_DB = {
    "pebble_shiny": {
        "id": "pebble_shiny",
        "name": "Shiny Pebble",
        "description": "A smooth, glistening pebble. It catches the light beautifully.",
        "type": "junk", # Categories: junk, consumable, weapon, armor, quest_item, etc.
        "value": 1
    },
    "seaweed_clump": {
        "id": "seaweed_clump",
        "name": "Clump of Seaweed",
        "description": "A damp and slightly smelly clump of seaweed.",
        "type": "junk",
        "value": 0
    },
    "broken_shell": {
        "id": "broken_shell",
        "name": "Broken Shell Fragment",
        "description": "A sharp fragment from a larger seashell.",
        "type": "junk",
        "value": 0
    }
    # Add more items here later
}

# --- Helper function for AI interaction ---
def get_ai_description(prompt_text):
    if not global_ai_client or not global_generation_config: 
        return f"[AI Fallback - Client or GenConfig not initialized. Original prompt: '{prompt_text}'] ... A generic description unfolds."
    
    if DEBUG_MODE:
        print(f"DEBUG: AI Prompt: {prompt_text[:100]}...")
    try:
        response = global_ai_client.models.generate_content(
            model=AI_MODEL_NAME, 
            contents=prompt_text,
            config=global_generation_config
        )

        if DEBUG_MODE:
            print(f"DEBUG: Raw AI Response object: {type(response)}")
            # Check for prompt feedback (blocking)
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason_message = response.prompt_feedback.block_reason_message or "No specific message."
                print(f"DEBUG: Warning: AI prompt was blocked. Reason: {response.prompt_feedback.block_reason}, Message: {block_reason_message}")
            # print(f"DEBUG: Full AI Response: {response}") # Usually too verbose
            if hasattr(response, 'candidates') and response.candidates:
                print(f"DEBUG: Finish Reason for first candidate: {response.candidates[0].finish_reason}")

        # Check for prompt feedback (blocking) - This check should happen regardless of DEBUG_MODE for actual blocking
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason_message = response.prompt_feedback.block_reason_message or "No specific message."
            # We already printed in debug, but for actual game flow:
            # print(f"Warning: AI prompt was blocked. Reason: {response.prompt_feedback.block_reason}, Message: {block_reason_message}") 
            return f"[AI prompt blocked: {response.prompt_feedback.block_reason}. Original prompt: '{prompt_text}']"

        text_output = None
        if response.text:
            text_output = response.text.strip()
            if DEBUG_MODE:
                print(f"DEBUG: response.text is available: '{text_output[:100]}...'")
        elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts and response.candidates[0].content.parts[0].text:
            text_output = response.candidates[0].content.parts[0].text.strip()
            if DEBUG_MODE:
                print(f"DEBUG: Text found in response.candidates: '{text_output[:100]}...'")
        else:
            if DEBUG_MODE:
                print("DEBUG: Warning: AI response seems to have no text content in expected fields (response.text or response.candidates).")
                print(f"DEBUG: Available candidates: {response.candidates if hasattr(response, 'candidates') else 'N/A'}")
            return f"[AI response had no text. Original prompt: '{prompt_text}']"
        
        if not text_output:
             if DEBUG_MODE:
                 print("DEBUG: Warning: AI response text_output is empty after processing.")
             return f"[AI response was empty. Original prompt: '{prompt_text}']"

        return text_output

    except AttributeError as ae:
        # Specifically catch if types.SafetySetting was the issue during the actual call
        if "SafetySetting" in str(ae) and "not found in types" in str(ae).lower(): # Heuristic check
             print(f"AI Call Error: types.SafetySetting seems to be unavailable or used incorrectly with SDK {genai.__version__ if genai else 'unknown'}. Please check SDK docs.")
        else:
             print(f"AI Call Error (AttributeError): {ae}")
        return f"[AI Error - AttributeError during call. Prompt: '{prompt_text}'] ... The details are unclear."
    except Exception as e:
        print(f"Error getting AI description: {e}")
        return f"[AI Error: Could not generate description for: '{prompt_text}'] ... The details are hazy."

# List of valid races and origins
valid_races = ["Human", "Orc", "Naiad", "Elf", "Dwarf", "Maithar", "Urthar"]
valid_origins = ["Lowborn", "Highborn", "Rural", "Marauder"]
valid_actions = ["Attack", "Flee"]
valid_star_signs = ["Aegis", "Seraph", "Eclipse", "Lumos", "Verdant", "Tempest", "Solstice", "Nexus", "Ember", "Astral"]

# Helper function for presenting numbered choices and getting valid input
def get_numbered_choice(prompt_text, options_list):
    print(prompt_text)
    for i, option in enumerate(options_list):
        print(f"  {i+1}. {option}")
    
    choice_num = -1
    while choice_num < 1 or choice_num > len(options_list):
        try:
            raw_input = input(f"Enter your choice (1-{len(options_list)}): ")
            choice_num = int(raw_input)
            if not (1 <= choice_num <= len(options_list)):
                print(f"Invalid number. Please enter a number between 1 and {len(options_list)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    return options_list[choice_num - 1]

# Character Creation Function with Validation
def character_creation():
    print("Welcome to The Silent Symphony!")
    player_character = {}

    quick_start_input = input("Quick Start character creation? (y/n): ").strip().lower()

    if quick_start_input == 'y':
        player_character['name'] = "Rynn"
        player_character['race'] = random.choice(valid_races)
        player_character['origin'] = random.choice(valid_origins)
        player_character['star_sign'] = random.choice(valid_star_signs)
        print(f"\nQuick Start selected! Your character is {player_character['name']}, a {player_character['race']} {player_character['origin']} born under the sign of {player_character['star_sign']}.")
    else:
        player_character['race'] = get_numbered_choice("\nChoose your race:", valid_races)
        player_character['origin'] = get_numbered_choice("\nChoose your origin:", valid_origins)
        player_character['star_sign'] = get_numbered_choice("\nChoose your star sign:", valid_star_signs)
        player_character['name'] = input("\nWhat is your character's name?: ").strip()
        while not player_character['name']:
            print("Name cannot be empty.")
            player_character['name'] = input("What is your character's name?: ").strip()

    backstory_template = f"""
    You awaken to the gentle lapping of waves, the caress of seafoam at your feet, a stark contrast to the tempest that raged just hours before. Your body lies heavy upon the wet sand, each breath a testament to your survival against the capricious wrath of the sea. As your eyes flutter open, the blurred edges of reality sharpen, revealing the sun-drenched shores of some land unknown to you, {player_character['name']}.

Memories flash like lightning across the firmament of your mind — the creaking of wood, the howl of the storm, the desperate cries of your companions now lost to the abyss. The details of your past voyage are as scattered as the flotsam strewn about the beach, but one thing is clear: you are far from home.

This land greets you with its wild, untamed beauty. Towering cliffs crowned with verdure rise to the east, and to the west, the ocean spans the horizon, a sapphire sheet etched with the gold of the dawning day. 

Now, as destiny's hand guides you forth from the shores of providence, you stand at the threshold of a new beginning. Here, amidst the echoes of a history both grand and cruel, you, a {player_character['race']} of {player_character['origin']} origin, born under the sign of {player_character['star_sign']}, will find your place in the stories yet unwritten. Your journey begins not with the remembrance of whence you came, but with the promise of what lies ahead.

With the salt on your lips and the horizon calling, you rise. The path before you is fraught with shadows and light, danger and opportunity. Every step is a story, and every choice carves the key to your future.

As you take your first steps into the unknown, you can't shake the feeling that your arrival was no mere accident. The threads of destiny are woven tight around your fate, and only time will reveal the role you are to play in this new world. 
    """
    print("\n--- Your Story Begins ---")
    print(backstory_template)
    
    print(f"\nWelcome, {player_character['name']} the {player_character['race']} {player_character['origin']}, born under the sign of {player_character['star_sign']}. Your journey begins now...")
    
    player_character['health'] = 30 
    player_character['max_health'] = 30
    player_character['inventory'] = []
    player_character['location'] = "Beach" 
    player_character['last_described_location'] = None

    return player_character

# Simple Combat Function
def combat(player_character):
    player_health = player_character['health']
    enemy_health = 20 
    enemy_name = "Generic Goblin" 
    print(f"\n--- Combat Initiated! ---")
    print(f"You've encountered a {enemy_name}!")

    combat_actions = ["Attack", "Flee"] # Define actions for combat here

    while player_health > 0 and enemy_health > 0:
        print(f"\nYour Health: {player_health}/{player_character['max_health']} | {enemy_name} Health: {enemy_health}")
        
        action = get_numbered_choice("Choose your action:", combat_actions)
        
        if action == 'Attack':
            damage = random.randint(1, 8)
            enemy_health -= damage
            print(f"You attacked the {enemy_name} for {damage} damage! Enemy health is now {enemy_health}.")
            
            if enemy_health > 0:
                enemy_attack = random.randint(1, 5)
                player_health -= enemy_attack
                print(f"The {enemy_name} attacks you back for {enemy_attack} damage! Your health is now {player_health}.")
        elif action == 'Flee':
            print("You managed to flee!")
            player_character['health'] = player_health 
            return "fled"
        
        if enemy_health <= 0:
            print(f"You defeated the {enemy_name}!")
            player_character['health'] = player_health
            return "won"
        elif player_health <= 0:
            print("You have been defeated!")
            player_character['health'] = 0
            return "lost"
    return "error"

# Main Game Loop
def game():
    player = None
    ensure_save_directory() # Ensure it exists before trying to list/load

    print("Welcome to The Silent Symphony - Main Menu")
    menu_options = ["Start New Game", "Load Game"]
    if not list_save_files(): # Disable load if no saves
        # menu_options.remove("Load Game") # Or just handle it in the choice logic
        print("(No save files found to load)")
    
    initial_choice = get_numbered_choice("What would you like to do?", menu_options)

    if initial_choice == "Load Game":
        saved_games = list_save_files()
        if saved_games:
            print("\nAvailable save games:")
            # Add an option to go back to main menu / start new game
            load_options = saved_games + ["[Back to Main Menu]"] 
            chosen_save_name = get_numbered_choice("Select a game to load:", load_options)
            
            if chosen_save_name == "[Back to Main Menu]":
                # This will effectively restart the game() call or we can loop here
                # For simplicity, let's just proceed to new game if they back out
                print("Returning to main menu options...")
                # Call game() again or structure a loop. For now, we'll let it fall through to new game if back is chosen here
                # A better way would be a loop around this menu section.
                # To avoid recursion or complex loop now, if they go back, we can just treat it as wanting a new game for this flow.
                # This is a simplification for now.
                if "Start New Game" in menu_options: # Check if it's a valid option (it always should be)
                    initial_choice = "Start New Game"
                else: # Should not happen
                    print("Error: Cannot go back to new game. Exiting.")
                    return
            else:
                loaded_player_data = load_game_state(chosen_save_name)
                if loaded_player_data:
                    player = loaded_player_data
                    print(f"Game '{chosen_save_name}' loaded successfully!")
                else:
                    print("Failed to load game. Starting a new game instead.")
                    initial_choice = "Start New Game" # Fallback to new game
        else:
            # This case is already handled by the print above, but as a fallback:
            print("No save games found to load. Starting a new game.")
            initial_choice = "Start New Game"

    if initial_choice == "Start New Game" and player is None: # Ensure player is None if load failed or wasn't chosen
        player = character_creation()
    
    if not player: # If player is still None (e.g. issue with load choice logic or backed out)
        print("No character loaded or created. Exiting game.")
        return

    game_over = False
    print("\n--- Game Start ---")
    main_game_actions = {
        "1": "Explore further",
        "2": "Check inventory",
        "3": "View character stats",
        "4": "Save Game",
        "5": "Quit game"
    }

    while not game_over:
        print(f"\n--- Current Location: {player['location']} ---")
        
        if player['location'] != player.get('last_described_location'):
            location_prompt = f"Describe the area '{player['location']}'. The player is a {player['race']} named {player['name']}. Keep it brief, about 2-3 sentences, focusing on atmosphere and potential points of interest."
            print(get_ai_description(location_prompt))
            player['last_described_location'] = player['location']
        
        print("\nWhat would you like to do?")
        for key, value in main_game_actions.items():
            print(f"{key}. {value}")

        choice = input("> ").strip()

        if choice in main_game_actions:
            selected_action = main_game_actions[choice]
            if selected_action == 'Explore further':
                print("\nYou decide to explore further...")
                encounter_chance = random.random()
                if encounter_chance < 0.1: # 10% chance for nothing
                    print(get_ai_description(f"Describe a brief, uneventful moment of exploration for {player['name']} in {player['location']}."))
                elif encounter_chance < 0.7: # Increased chance, 60% chance to find an item (0.1 to 0.7)
                    # Simple loot: pick a random item from a small predefined list of findable item IDs
                    possible_finds = ["pebble_shiny", "seaweed_clump", "broken_shell"]
                    found_item_id = random.choice(possible_finds)
                    
                    if found_item_id in ITEM_DB:
                        found_item_name = ITEM_DB[found_item_id]["name"]
                        player['inventory'].append(found_item_id) # Add item ID to inventory
                        print(get_ai_description(f"{player['name']} finds a {found_item_name} while exploring {player['location']}. Describe this discovery briefly."))
                        print(f"You found a {found_item_name}! Added to inventory.")
                    else:
                        if DEBUG_MODE:
                            print(f"DEBUG: Error - found_item_id '{found_item_id}' not in ITEM_DB!")
                        print("You found something, but it crumbled to dust...") # Fallback
                else: # 30% chance for combat (0.7 to 1.0)
                    combat_result = combat(player)
                    if combat_result == "lost":
                        print("\nYour journey ends here, for now.")
                        game_over = True
                    elif combat_result == "won":
                        print("You feel a surge of confidence after your victory!")
            elif selected_action == 'Check inventory':
                if player['inventory']:
                    print("\n--- Inventory ---")
                    for item_id in player['inventory']:
                        if item_id in ITEM_DB:
                            print(f"- {ITEM_DB[item_id]['name']} (ID: {item_id})") # Show name, optionally ID for debug
                        else:
                            print(f"- Unknown item (ID: {item_id})") # Should not happen if items added correctly
                else:
                    print("\nYour inventory is empty.")
            elif selected_action == 'View character stats':
                print("\n--- Character Stats ---")
                print(f"Name: {player['name']}")
                print(f"Race: {player['race']}")
                print(f"Origin: {player['origin']}")
                print(f"Star Sign: {player['star_sign']}")
                print(f"Health: {player['health']}/{player['max_health']}")
            elif selected_action == 'Save Game':
                save_name = input("Enter a name for your save game: ").strip()
                if save_name:
                    save_game_state(player, save_name)
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

SAVEGAME_DIR = "savegames"

# --- Save/Load Utility Functions ---
def ensure_save_directory():
    """Ensures the save game directory exists."""
    if not os.path.exists(SAVEGAME_DIR):
        try:
            os.makedirs(SAVEGAME_DIR)
            print(f"Created save game directory: {SAVEGAME_DIR}")
        except OSError as e:
            print(f"Error creating save game directory {SAVEGAME_DIR}: {e}")
            return False
    return True

def save_game_state(player_data, filename):
    """Saves the player_data to a JSON file."""
    if not ensure_save_directory():
        return False
    if not filename.strip():
        print("Save filename cannot be empty.")
        return False
    
    # Sanitize filename a bit (basic example, can be more robust)
    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
    if not safe_filename:
        print("Invalid characters in filename, or filename became empty after sanitization.")
        return False

    filepath = os.path.join(SAVEGAME_DIR, f"{safe_filename}.json")
    try:
        with open(filepath, 'w') as f:
            json.dump(player_data, f, indent=4)
        print(f"Game saved as '{safe_filename}.json' in '{SAVEGAME_DIR}' directory.")
        return True
    except IOError as e:
        print(f"Error saving game to {filepath}: {e}")
    except TypeError as e:
        print(f"Error serializing game data (TypeError): {e}")
    return False

def load_game_state(filename):
    """Loads player_data from a JSON file."""
    filepath = os.path.join(SAVEGAME_DIR, f"{filename}.json") # Assumes filename does not have .json yet
    if not os.path.exists(filepath):
        print(f"Save file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            player_data = json.load(f)
        print(f"Game loaded from '{filename}.json'.")
        return player_data
    except IOError as e:
        print(f"Error loading game from {filepath}: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding save file (corrupted?) {filepath}: {e}")
    return None

def list_save_files():
    """Returns a list of available save game filenames (without .json extension)."""
    if not os.path.exists(SAVEGAME_DIR):
        return []
    try:
        files = [f[:-5] for f in os.listdir(SAVEGAME_DIR) if f.endswith(".json")]
        return sorted(files)
    except OSError as e:
        print(f"Error listing save files: {e}")
        return []

if __name__ == "__main__":
    # ensure_save_directory() # Already called at the top level of the functions or implicitly by save_game_state
    # Call game() to start
    game()
