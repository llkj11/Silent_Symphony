import os
import json
import ui  # Import for numbered choice functionality

SAVEGAME_DIR = "savegames"
MAX_SAVE_GAMES = 10

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
    """Saves the player_data to a JSON file with save limit checking."""
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
    
    # Check if this is a new save (not overwriting existing)
    is_new_save = not os.path.exists(filepath)
    existing_saves = list_save_files()
    
    # Check save limit for new saves
    if is_new_save and len(existing_saves) >= MAX_SAVE_GAMES:
        print(f"\n⚠️  Save Limit Reached! ⚠️")
        print(f"You already have {len(existing_saves)} save games (maximum: {MAX_SAVE_GAMES}).")
        print("You need to delete an existing save game before creating a new one.")
        
        # Offer to manage saves
        choice = ui.get_numbered_choice("What would you like to do?", [
            "Delete an existing save to make room",
            "Overwrite an existing save",
            "Cancel saving"
        ])
        
        if choice == "Delete an existing save to make room":
            if manage_save_deletion():
                # After successful deletion, proceed with save
                pass
            else:
                return False
        elif choice == "Overwrite an existing save":
            print("\nSelect a save to overwrite:")
            save_options = existing_saves + ["Cancel"]
            chosen_save = ui.get_numbered_choice("Choose save to overwrite:", save_options)
            if chosen_save == "Cancel":
                return False
            safe_filename = chosen_save  # Use the chosen save name
            filepath = os.path.join(SAVEGAME_DIR, f"{safe_filename}.json")
        else:  # Cancel saving
            return False
    
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

def delete_save_game(filename):
    """Deletes a save game file."""
    if filename.endswith(".json"):
        actual_filename = filename
    else:
        actual_filename = f"{filename}.json"
        
    filepath = os.path.join(SAVEGAME_DIR, actual_filename)
    
    if not os.path.exists(filepath):
        print(f"Save file not found: {actual_filename}")
        return False
    
    try:
        os.remove(filepath)
        print(f"Save game '{filename}' deleted successfully.")
        return True
    except OSError as e:
        print(f"Error deleting save file {filepath}: {e}")
        return False

def manage_save_deletion():
    """Interactive save deletion menu."""
    existing_saves = list_save_files()
    
    if not existing_saves:
        print("No save games found to delete.")
        return False
    
    print(f"\n--- Save Game Management ---")
    print(f"Current saves: {len(existing_saves)}/{MAX_SAVE_GAMES}")
    
    # Show save files with details if possible
    save_options = []
    for save_name in existing_saves:
        filepath = os.path.join(SAVEGAME_DIR, f"{save_name}.json")
        try:
            # Get file modification time for display
            import time
            mod_time = os.path.getmtime(filepath)
            formatted_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
            
            # Try to get character info from save
            with open(filepath, 'r') as f:
                save_data = json.load(f)
            char_info = f"Level {save_data.get('level', 1)} {save_data.get('race', 'Unknown')} {save_data.get('name', 'Unnamed')}"
            
            save_options.append(f"{save_name} - {char_info} (Saved: {formatted_time})")
        except (OSError, json.JSONDecodeError, KeyError):
            save_options.append(f"{save_name} - (Unable to read save data)")
    
    save_options.append("Cancel deletion")
    
    chosen_save_display = ui.get_numbered_choice("Choose a save game to DELETE:", save_options)
    
    if chosen_save_display == "Cancel deletion":
        return False
    
    # Extract the actual save name from the display text
    chosen_save_name = chosen_save_display.split(" - ")[0]
    
    # Confirm deletion
    confirm = ui.get_numbered_choice(
        f"Are you sure you want to DELETE '{chosen_save_name}'? This cannot be undone!", 
        ["Yes, delete it", "No, cancel"]
    )
    
    if confirm == "Yes, delete it":
        return delete_save_game(chosen_save_name)
    else:
        print("Deletion cancelled.")
        return False

def save_game_menu(player_data):
    """Enhanced save game menu with save management."""
    existing_saves = list_save_files()
    
    print(f"\n--- Save Game Menu ---")
    print(f"Current saves: {len(existing_saves)}/{MAX_SAVE_GAMES}")
    
    if len(existing_saves) >= MAX_SAVE_GAMES:
        print("⚠️  Save limit reached! You must delete a save or overwrite an existing one.")
    
    menu_options = ["Create new save game"]
    
    if existing_saves:
        menu_options.append("Overwrite existing save")
        menu_options.append("Delete save games")
    
    menu_options.append("Cancel")
    
    choice = ui.get_numbered_choice("What would you like to do?", menu_options)
    
    if choice == "Create new save game":
        if len(existing_saves) >= MAX_SAVE_GAMES:
            # This will trigger the limit handling in save_game_state
            save_name = input("Enter a name for your save game: ").strip()
            if save_name:
                return save_game_state(player_data, save_name)
            else:
                print("Save name cannot be empty.")
                return False
        else:
            save_name = input("Enter a name for your save game: ").strip()
            if save_name:
                return save_game_state(player_data, save_name)
            else:
                print("Save name cannot be empty.")
                return False
    
    elif choice == "Overwrite existing save":
        save_options = existing_saves + ["Cancel"]
        chosen_save = ui.get_numbered_choice("Choose save to overwrite:", save_options)
        if chosen_save != "Cancel":
            return save_game_state(player_data, chosen_save)
        return False
    
    elif choice == "Delete save games":
        manage_save_deletion()
        return False  # Return to main menu after deletion
    
    return False  # Cancel

def load_game_state(filename):
    """Loads player_data from a JSON file."""
    # Ensure filename does not already contain .json for consistency with list_save_files
    if filename.endswith(".json"):
        actual_filename = filename
    else:
        actual_filename = f"{filename}.json"
        
    filepath = os.path.join(SAVEGAME_DIR, actual_filename)
    if not os.path.exists(filepath):
        print(f"Save file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            player_data = json.load(f)
        # Ensure 'completed_pois' exists for compatibility with older saves
        player_data.setdefault('completed_pois', {})
        # Ensure 'completed_pois' values are sets for older saves that might have them as lists
        for location_id, poi_ids in player_data['completed_pois'].items():
            if isinstance(poi_ids, list): # Compatibility for potential old format
                player_data['completed_pois'][location_id] = set(poi_ids)
        
        # Add default spell/mana attributes for older saves
        player_data.setdefault('known_spells', ['minor_heal'])
        player_data.setdefault('max_mana', 10)
        # Ensure mana is set, defaults to max_mana if missing, and doesn't exceed current max_mana
        current_max_mana = player_data.get('max_mana', 10)
        player_data.setdefault('mana', current_max_mana)
        if player_data['mana'] > current_max_mana:
            player_data['mana'] = current_max_mana
            
        print(f"Game loaded from '{actual_filename}'.") # Use actual_filename for user message
        return player_data
    except IOError as e:
        print(f"Error loading game from {filepath}: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding save file (corrupted?) {filepath}: {e}")
    return None

def list_save_files():
    """Returns a list of available save game filenames (without .json extension)."""
    if not ensure_save_directory(): # Ensure directory exists before listing
        return []
    try:
        files = [f[:-5] for f in os.listdir(SAVEGAME_DIR) if f.endswith(".json")]
        return sorted(files)
    except OSError as e:
        print(f"Error listing save files: {e}")
        return [] 