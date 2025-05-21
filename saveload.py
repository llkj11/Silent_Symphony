import os
import json

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