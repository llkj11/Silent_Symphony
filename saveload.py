import os
import json

import game_data

SAVEGAME_DIR = "savegames"

PLAYER_FIELD_DEFAULTS = {
    "mana": 10,
    "max_mana": 10,
    "stamina": 10,
    "max_stamina": 10,
    "effects": list,
    "known_abilities": list,
    "world_state": dict,
    "event_history": list,
    "quests": dict,
    "item_uses": dict,
    "gold": 0,
    "equipped_head": None,
    "equipped_chest": None,
    "equipped_legs": None,
    "equipped_hands": None,
    "equipped_feet": None,
}


def migrate_player(player_data):
    """Fill in fields added after a save was written so old saves still load."""
    if not isinstance(player_data, dict):
        return player_data
    # Legacy single-slot armor → chest slot.
    if 'equipped_armor' in player_data:
        legacy = player_data.pop('equipped_armor')
        if legacy and not player_data.get('equipped_chest'):
            player_data['equipped_chest'] = legacy
    for field, default in PLAYER_FIELD_DEFAULTS.items():
        if field not in player_data:
            player_data[field] = default() if callable(default) else default
    # Back-fill race_trait from race for saves written before traits existed.
    if 'race_trait' not in player_data:
        race = player_data.get('race')
        player_data['race_trait'] = game_data.RACE_TRAITS.get(race, {}).get('trait')
    # Legacy event history: plain strings → {text, significance} dicts.
    history = player_data.get('event_history')
    if isinstance(history, list):
        player_data['event_history'] = [
            e if isinstance(e, dict) else {"text": str(e), "significance": "normal"}
            for e in history
        ]
    return player_data

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
        player_data = migrate_player(player_data)
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