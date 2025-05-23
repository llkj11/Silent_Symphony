import random
import os 
import json 
import curses # Import curses for the wrapper
import re # For parsing AI responses
import time # For time-based events
import datetime # For logging timestamps

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

# === CLI GUI Enhancement Options ===
# For better presentation, consider these libraries:
# 1. Rich - Beautiful terminal formatting and layout
# 2. Textual - Full TUI framework with widgets
# 3. blessed - Terminal positioning and colors
# 4. prompt_toolkit - Advanced input with auto-completion
# Current: Basic terminal with scroll management

# Uncomment to enable Rich formatting (requires: pip install rich)
# from rich.console import Console
# from rich.panel import Panel
# from rich.progress import Progress, BarColumn, TextColumn
# from rich.table import Table
# from rich.text import Text
# USE_RICH = False  # Set to True to enable Rich formatting

def clear_screen():
    """Clear the terminal screen for better presentation."""
    os.system('cls' if os.name == 'nt' else 'clear')

def pause_for_reading():
    """Pause to let player read content before continuing."""
    input("\nPress Enter to continue...")

def print_section_header(title):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def print_with_pause(text, pause_duration=0.03):
    """Print text with a slight delay for better readability."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(pause_duration)
    print()  # New line at the end

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
    if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: Called with location_id='{location_id}', specific_group='{specific_group}'")
    current_location_data = locations.LOCATIONS.get(location_id)
    if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: current_location_data: {current_location_data is not None}")

    if not current_location_data:
        if config.DEBUG_MODE: print("DEBUG get_random_enemy_for_location: Returning None - current_location_data is None.")
        return None

    encounter_group_names_for_location = current_location_data.get('encounter_groups', [])
    if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: encounter_group_names_for_location: {encounter_group_names_for_location}")

    if not encounter_group_names_for_location:
        if config.DEBUG_MODE: print("DEBUG get_random_enemy_for_location: Returning None - encounter_group_names_for_location is empty.")
        return None # No encounter groups defined for this location

    chosen_group_name = None
    if specific_group and specific_group in encounter_group_names_for_location:
        chosen_group_name = specific_group
    elif specific_group: 
        if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: specific_group '{specific_group}' not valid for location '{location_id}'. Falling back to random.")
        chosen_group_name = random.choice(encounter_group_names_for_location) if encounter_group_names_for_location else None
    else:
        chosen_group_name = random.choice(encounter_group_names_for_location) if encounter_group_names_for_location else None
    
    if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: chosen_group_name: {chosen_group_name}")

    if not chosen_group_name:
        if config.DEBUG_MODE: print("DEBUG get_random_enemy_for_location: Returning None - chosen_group_name is None.")
        return None 

    encounter_list = locations.ENCOUNTER_GROUPS.get(chosen_group_name, [])
    if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: encounter_list for group '{chosen_group_name}': {encounter_list}")
    
    if not encounter_list:
        if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: Returning None - encounter_list is empty for group '{chosen_group_name}'.")
        return None 

    # Weighted random choice from the encounter list
    total_weight = sum(entry.get("weight", 0) for entry in encounter_list if isinstance(entry, dict)) # Ensure entry is a dict
    if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: total_weight: {total_weight}")

    if total_weight == 0: 
        # Fallback to uniform random choice if weights are problematic or all 0
        if config.DEBUG_MODE: print("DEBUG get_random_enemy_for_location: total_weight is 0. Attempting uniform random choice.")
        if encounter_list: # Check if list is not empty before choosing
            # Ensure entries in encounter_list are dicts and have 'enemy_id'
            valid_entries = [e for e in encounter_list if isinstance(e, dict) and "enemy_id" in e]
            if valid_entries:
                selected_entry = random.choice(valid_entries)
                if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: Uniform choice selected: {selected_entry.get('enemy_id')}")
                return selected_entry.get("enemy_id")
            else:
                if config.DEBUG_MODE: print("DEBUG get_random_enemy_for_location: Returning None - total_weight is 0 and no valid entries with 'enemy_id' in encounter_list.")
                return None
        else: # This case should ideally be caught by 'if not encounter_list:' above
            if config.DEBUG_MODE: print("DEBUG get_random_enemy_for_location: Returning None - total_weight is 0 and encounter_list is also empty.")
            return None

    random_pick = random.uniform(0, total_weight)
    current_sum = 0
    for entry in encounter_list:
        if not isinstance(entry, dict): # Skip malformed entries
            if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: Skipping malformed entry in encounter_list: {entry}")
            continue
        current_sum += entry.get("weight", 0)
        if random_pick <= current_sum:
            enemy_id = entry.get("enemy_id")
            if config.DEBUG_MODE: print(f"DEBUG get_random_enemy_for_location: Weighted choice selected: {enemy_id}")
            return enemy_id
            
    if config.DEBUG_MODE: print("DEBUG get_random_enemy_for_location: Returning None - loop completed without selection (should be rare if weights > 0).")
    return None

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

# --- Enhanced Exploration System ---
def generate_dynamic_exploration_event(player_character, location_data):
    """Generate dynamic exploration events based on location and character skills"""
    events = []
    
    # Check for dynamic events in location
    dynamic_events = location_data.get('dynamic_events', [])
    for dyn_event in dynamic_events:
        if random.random() < dyn_event.get('trigger_chance', 0):
            log_game_event("DYNAMIC_EVENT_TRIGGER", f"Triggered: {dyn_event.get('event_id', 'unknown')}", player_character.get('name'))
            return dyn_event
    
    # Weather and environmental events
    weather_events = [
        {
            "name": "Sudden Breeze",
            "description": "A sudden gust of wind reveals something previously hidden.",
            "effect": "discovery_bonus",
            "chance": 0.15
        },
        {
            "name": "Shifting Shadows",
            "description": "The changing light reveals details you missed before.",
            "effect": "perception_bonus",
            "chance": 0.12
        },
        {
            "name": "Distant Thunder",
            "description": "Ominous clouds gather on the horizon, creating an atmosphere of urgency.",
            "effect": "tension",
            "chance": 0.08
        }
    ]
    
    # Skill-based discoveries
    player_level = player_character.get('level', 1)
    if player_level >= 3:
        events.append({
            "name": "Experienced Eye",
            "description": "Your growing experience allows you to notice subtle details others might miss.",
            "effect": "skill_discovery",
            "chance": 0.2
        })
    
    # Location-specific events
    location_type = location_data.get('type', 'unknown')
    if location_type == 'coastal':
        events.extend([
            {
                "name": "Tide Pool Discovery",
                "description": "The receding tide reveals a small tide pool teeming with life.",
                "effect": "coastal_find",
                "chance": 0.25
            },
            {
                "name": "Driftwood Cache",
                "description": "You spot an unusual piece of driftwood that might hide something.",
                "effect": "driftwood_search",
                "chance": 0.18
            }
        ])
    elif location_type == 'desert':
        events.extend([
            {
                "name": "Desert Mirage",
                "description": "A shimmering mirage dances in the heat, but is it real?",
                "effect": "mirage_encounter",
                "chance": 0.2
            },
            {
                "name": "Sand Pattern",
                "description": "The wind reveals ancient patterns in the sand.",
                "effect": "pattern_discovery",
                "chance": 0.15
            }
        ])
    elif location_type == 'forest':
        events.extend([
            {
                "name": "Foraging Opportunity",
                "description": "You notice edible plants and herbs growing nearby.",
                "effect": "foraging",
                "chance": 0.3
            },
            {
                "name": "Animal Tracks",
                "description": "Fresh animal tracks lead off in an interesting direction.",
                "effect": "tracking",
                "chance": 0.2
            }
        ])
    
    # Add general events
    events.extend(weather_events)
    
    # Select event based on chance
    for event in events:
        if random.random() < event["chance"]:
            log_game_event("EXPLORATION_EVENT", f"Generated: {event['name']}", player_character.get('name'))
            return event
    
    return None

def execute_exploration_event(event, player_character, location_data):
    """Execute a dynamic exploration event"""
    if not event:
        return False
    
    # Handle location-specific dynamic events
    if event.get('weather_change'):
        handle_weather_change(event['weather_change'], player_character)
        
    if event.get('npc_encounter'):
        handle_npc_encounter(event['npc_encounter'], player_character, location_data)
        return True
        
    print(f"\n🌟 {event['name']} 🌟")
    print(event['description'])
    log_game_event("EVENT_DESCRIPTION", f"{event['name']}: {event['description']}", player_character.get('name'))
    
    effect = event.get('effect', '')
    
    if effect == "discovery_bonus":
        # Chance to find a common item
        common_items = location_data.get('items_common_find', [])
        if common_items and random.random() < 0.6:
            found_item = random.choice(common_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"You discovered: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_DISCOVERED", f"Found: {items.ITEM_DB[found_item]['name']}", player_character.get('name'))
        else:
            print("Unfortunately, nothing comes of this moment.")
            log_game_event("DISCOVERY_FAILED", "No items found", player_character.get('name'))
            
    elif effect == "coastal_find":
        coastal_items = ["broken_shell", "seaweed_clump", "pearl_small", "crab_chitin_fragment"]
        found_item = random.choice(coastal_items)
        if found_item in items.ITEM_DB:
            player_character['inventory'].append(found_item)
            print(f"You carefully extract: {items.ITEM_DB[found_item]['name']}!")
            log_game_event("COASTAL_FIND", f"Extracted: {items.ITEM_DB[found_item]['name']}", player_character.get('name'))
            
    elif effect == "mirage_encounter":
        print("The mirage shimmers and shifts...")
        if random.random() < 0.3:
            print("It was real! A hidden path reveals itself.")
            log_game_event("MIRAGE_SUCCESS", "Hidden path revealed", player_character.get('name'))
            # Could unlock a hidden exit here
        else:
            print("The vision fades, leaving only hot sand.")
            log_game_event("MIRAGE_FAILED", "Vision faded", player_character.get('name'))
            
    elif effect == "pattern_discovery":
        print("The sand patterns seem to hold meaning...")
        if 'ancient_compass' in player_character.get('inventory', []):
            print("Your ancient compass resonates with the patterns!")
            discover_lore_fragment("ancient_prophecy_1", player_character)
        else:
            print("You sense there's more here, but lack the means to understand it.")
            log_game_event("PATTERN_INCOMPLETE", "Missing required item", player_character.get('name'))
            
    elif effect == "foraging":
        forage_items = ["berries_wild", "sunpetal_leaf", "moonbloom_flower", "herbal_poultice"]
        found_item = random.choice(forage_items)
        if found_item in items.ITEM_DB:
            player_character['inventory'].append(found_item)
            print(f"You successfully forage: {items.ITEM_DB[found_item]['name']}!")
            log_game_event("FORAGING_SUCCESS", f"Found: {items.ITEM_DB[found_item]['name']}", player_character.get('name'))
            
    elif effect == "skill_discovery":
        # Higher level characters find better items
        if player_character.get('level', 1) >= 5:
            rare_items = ["healing_potion_lesser", "mana_potion_minor", "crystal_shard_mundane"]
            found_item = random.choice(rare_items)
        else:
            found_item = random.choice(["healing_salve_minor", "antidote_simple"])
        
        if found_item in items.ITEM_DB:
            player_character['inventory'].append(found_item)
            print(f"Your experience pays off! You find: {items.ITEM_DB[found_item]['name']}!")
            log_game_event("SKILL_DISCOVERY", f"Experience rewarded: {items.ITEM_DB[found_item]['name']}", player_character.get('name'))
            
    elif effect == "driftwood_search":
        if random.random() < 0.7:
            driftwood_items = ["timber_rough", "rope_hempen_10ft", "fishing_rod_basic", "string_piece"]
            found_item = random.choice(driftwood_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"Hidden within the driftwood: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("DRIFTWOOD_FIND", f"Found: {items.ITEM_DB[found_item]['name']}", player_character.get('name'))
        else:
            print("The driftwood crumbles apart, revealing nothing useful.")
            log_game_event("DRIFTWOOD_EMPTY", "Nothing found", player_character.get('name'))
            
    elif effect == "tracking":
        print("The tracks lead to...")
        log_game_event("TRACKING_START", "Following tracks", player_character.get('name'))
        if random.random() < 0.3:
            print("A small cache of supplies left by another traveler!")
            cache_items = ["ration_pack_basic", "empty_waterskin", "tinderbox"]
            found_item = random.choice(cache_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"You find: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("CACHE_FOUND", f"Discovered cache with: {items.ITEM_DB[found_item]['name']}", player_character.get('name'))
        else:
            print("The tracks fade away, but you gained valuable tracking experience.")
            log_game_event("TRACKING_EXPERIENCE", "Gained tracking experience", player_character.get('name'))
            # Could award small XP bonus here
            
    elif effect == "perception_bonus":
        print("Your heightened awareness reveals...")
        if random.random() < 0.4:
            print("A hidden detail you can investigate further next time you explore!")
            log_game_event("PERCEPTION_SUCCESS", "Hidden detail noticed", player_character.get('name'))
            # Could add a temporary bonus to next exploration
        else:
            log_game_event("PERCEPTION_NEUTRAL", "No immediate discoveries", player_character.get('name'))
            
    return True

# --- New Weather System ---
def handle_weather_change(weather_type, player_character):
    """Handle weather changes and their effects"""
    weather = locations.WEATHER_TYPES.get(weather_type, {})
    if not weather:
        return
        
    print(f"\n🌤️ Weather Change: {weather['name']} 🌤️")
    print(weather['description'])
    log_game_event("WEATHER_CHANGE", f"{weather['name']}: {weather['description']}", player_character.get('name'))
    
    # Apply weather effects
    effects = weather.get('effects', {})
    if effects.get('perception_bonus'):
        print(f"Perception {'increased' if effects['perception_bonus'] > 0 else 'decreased'} by {abs(effects['perception_bonus'])}!")
    if effects.get('stealth_bonus'):
        print(f"The conditions favor stealth (+{effects['stealth_bonus']} to stealth).")
    if effects.get('tension'):
        print("The atmosphere grows tense...")
        
    # Store current weather in player data
    if 'game_state' not in player_character:
        player_character['game_state'] = {}
    player_character['game_state']['current_weather'] = weather_type
    log_game_event("WEATHER_SET", f"Current weather: {weather_type}", player_character.get('name'))

# --- New NPC Encounter System ---
def handle_npc_encounter(npc_id, player_character, location_data):
    """Handle non-combat NPC encounters"""
    npc = locations.NPC_ENCOUNTERS.get(npc_id, {})
    if not npc:
        return
        
    print(f"\n👤 Encounter: {npc['name']} 👤")
    print(npc['description'])
    log_game_event("NPC_ENCOUNTER", f"Met: {npc['name']}", player_character.get('name'))
    
    # Display dialogue options
    dialogue_options = npc.get('dialogue_options', [])
    print("\nWhat would you like to do?")
    for i, option in enumerate(dialogue_options, 1):
        print(f"{i}. {option}")
    print(f"{len(dialogue_options) + 1}. Walk away")
    
    try:
        choice = int(input("Your choice: "))
        log_game_event("DIALOGUE_CHOICE", f"Selected: {dialogue_options[choice-1] if choice <= len(dialogue_options) else 'Walk away'}", player_character.get('name'))
        
        if choice <= len(dialogue_options):
            handle_npc_dialogue(npc_id, dialogue_options[choice-1], player_character)
        else:
            print("You politely excuse yourself and continue on your way.")
            log_game_event("NPC_LEAVE", "Walked away from encounter", player_character.get('name'))
    except:
        print("You hesitate, unsure what to say.")
        log_game_event("DIALOGUE_ERROR", "Invalid choice", player_character.get('name'))

def handle_npc_dialogue(npc_id, choice, player_character):
    """Handle specific NPC dialogue choices"""
    npc = locations.NPC_ENCOUNTERS.get(npc_id, {})
    
    if "trade" in choice.lower() and npc.get('can_trade'):
        print("\nThe figure shows you their wares...")
        log_game_event("TRADE_INITIATED", f"Trading with {npc['name']}", player_character.get('name'))
        # Could implement trading system here
        print("(Trading system not yet implemented)")
        
    elif "guidance" in choice.lower() or "wisdom" in choice.lower():
        if random.random() < npc.get('wisdom_chance', 0.5):
            wisdom_messages = [
                "The path forward is often found by looking back.",
                "What seems like sand may be more solid than stone.",
                "The Silent Symphony awaits those who know how to listen.",
                "Three keys open the way, but only one is made of metal."
            ]
            message = random.choice(wisdom_messages)
            print(f"\nThe {npc['name']} speaks: '{message}'")
            log_game_event("WISDOM_RECEIVED", f"Wisdom: {message}", player_character.get('name'))
        else:
            print("\nThey seem lost in thought and don't respond.")
            log_game_event("WISDOM_FAILED", "No response", player_character.get('name'))
            
    elif "stories" in choice.lower() or "tale" in choice.lower():
        if random.random() < npc.get('lore_chance', 0.5):
            discover_lore_fragment(random.choice(list(locations.LORE_FRAGMENTS.keys())), player_character)
        else:
            print("\nThey share a pleasant but unremarkable story.")
            log_game_event("STORY_GENERIC", "Heard unremarkable story", player_character.get('name'))

# --- New Lore Discovery System ---
def discover_lore_fragment(fragment_id, player_character):
    """Discover and display a lore fragment"""
    fragment = locations.LORE_FRAGMENTS.get(fragment_id)
    if not fragment:
        return
        
    print(f"\n📜 {fragment['title']} 📜")
    print(f"({fragment['discovery_context']})")
    print(f"\n'{fragment['text']}'")
    
    # Track discovered lore
    if 'discovered_lore' not in player_character:
        player_character['discovered_lore'] = []
    if fragment_id not in player_character['discovered_lore']:
        player_character['discovered_lore'].append(fragment_id)
        print("\n[This lore has been added to your journal]")
        
    log_game_event("LORE_DISCOVERED", f"{fragment['title']}: {fragment['text']}", player_character.get('name'))

def get_environmental_interactions(location_data, player_character):
    """Get available environmental interactions for current location"""
    interactions = []
    
    # Universal interactions
    interactions.append({
        "name": "Rest and Recover",
        "description": "Take time to rest and regain your strength",
        "action": "rest"
    })
    
    interactions.append({
        "name": "Observe Surroundings",
        "description": "Take a moment to really study your environment",
        "action": "observe"
    })
    
    # Location-specific interactions
    location_type = location_data.get('type', 'unknown')
    
    if location_type == 'coastal':
        interactions.extend([
            {
                "name": "Search Tide Pools",
                "description": "Look for interesting creatures and materials in tide pools",
                "action": "tide_pool_search"
            },
            {
                "name": "Collect Driftwood",
                "description": "Gather useful pieces of driftwood washed ashore",
                "action": "collect_driftwood"
            }
        ])
    
    elif location_type == 'forest':
        interactions.extend([
            {
                "name": "Forage for Food",
                "description": "Search for edible plants, berries, and herbs",
                "action": "forage"
            },
            {
                "name": "Track Wildlife",
                "description": "Follow animal tracks to see where they lead",
                "action": "track_animals"
            }
        ])
    
    elif location_type == 'rocky':
        interactions.extend([
            {
                "name": "Search Rock Crevices",
                "description": "Look for items hidden in rocky cracks and caves",
                "action": "search_rocks"
            },
            {
                "name": "Gather Minerals",
                "description": "Look for useful stones and mineral deposits",
                "action": "gather_minerals"
            }
        ])
    
    # Skill-based interactions
    if player_character.get('level', 1) >= 3:
        interactions.append({
            "name": "Use Experience",
            "description": "Apply your growing knowledge to find hidden opportunities",
            "action": "experience_search"
        })
    
    # Crafting hint if player has materials
    available_recipes = get_available_recipes(player_character)
    if available_recipes:
        interactions.append({
            "name": "Crafting Opportunity",
            "description": f"You have materials to craft {len(available_recipes)} item(s)!",
            "action": "show_crafting"
        })
    
    return interactions

def execute_environmental_interaction(interaction, player_character, location_data):
    """Execute an environmental interaction"""
    action = interaction['action']
    
    print(f"\n{interaction['description']}...")
    log_game_event("EXPLORATION_ACTION", f"Executing: {interaction['name']}", player_character.get('name'))
    
    if action == "rest":
        # Restore some health and mana
        old_health = player_character['health']
        old_mana = player_character['mana']
        
        health_restore = min(5, player_character['max_health'] - player_character['health'])
        mana_restore = min(3, player_character['max_mana'] - player_character['mana'])
        
        player_character['health'] += health_restore
        player_character['mana'] += mana_restore
        
        print(f"You feel refreshed! Restored {health_restore} HP and {mana_restore} MP.")
        log_game_event("REST", f"Restored {health_restore} HP and {mana_restore} MP", player_character.get('name'))
        if health_restore == 0 and mana_restore == 0:
            print("You're already at full strength, but the rest was pleasant.")
            
    elif action == "observe":
        print("You take time to carefully study your surroundings...")
        # Generate a detailed observation
        observations = [
            "You notice subtle wind patterns that speak of weather changes to come.",
            "The way light falls here suggests this place has significance.",
            "Small details in the landscape hint at paths others have taken.",
            "You feel a deeper connection to this place and its history.",
            "Your awareness sharpens, and you feel more attuned to hidden dangers."
        ]
        chosen_observation = random.choice(observations)
        print(chosen_observation)
        log_game_event("OBSERVATION", f"Observed: {chosen_observation}", player_character.get('name'))
        
        # Small chance of finding something
        if random.random() < 0.15:
            common_items = location_data.get('items_common_find', ["pebble_shiny"])
            if common_items:
                found_item = random.choice(common_items)
                if found_item in items.ITEM_DB:
                    player_character['inventory'].append(found_item)
                    print(f"Your careful observation reveals: {items.ITEM_DB[found_item]['name']}!")
                    log_game_event("ITEM_FOUND", f"Observation revealed: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            log_game_event("OBSERVATION_RESULT", "No items found during observation", player_character.get('name'), always_log=True)
            
    elif action == "tide_pool_search":
        success_chance = 0.6
        log_game_event("EXPLORATION_ACTION", f"Searching tide pools (success chance: {success_chance})", player_character.get('name'), always_log=True)
        if random.random() < success_chance:
            tide_items = ["broken_shell", "crab_chitin_fragment", "seaweed_clump", "pearl_small"]
            found_item = random.choice(tide_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"You carefully extract from a tide pool: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_FOUND", f"Tide pool search success: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            print("The tide pools are mostly empty, but you enjoy watching the small creatures.")
            log_game_event("EXPLORATION_RESULT", "Tide pool search failed - pools empty", player_character.get('name'), always_log=True)
            
    elif action == "collect_driftwood":
        success_chance = 0.5
        log_game_event("EXPLORATION_ACTION", f"Collecting driftwood (success chance: {success_chance})", player_character.get('name'), always_log=True)
        if random.random() < success_chance:
            wood_items = ["timber_rough", "rope_hempen_10ft", "torch_unlit"]
            found_item = random.choice(wood_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"You find useful driftwood: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_FOUND", f"Driftwood collection success: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            print("Most of the driftwood is too waterlogged or damaged to be useful.")
            log_game_event("EXPLORATION_RESULT", "Driftwood collection failed - too damaged", player_character.get('name'), always_log=True)
            
    elif action == "forage":
        success_chance = 0.7
        log_game_event("EXPLORATION_ACTION", f"Foraging for food (success chance: {success_chance})", player_character.get('name'), always_log=True)
        if random.random() < success_chance:
            forage_items = ["berries_wild", "sunpetal_leaf", "moonbloom_flower", "herbal_poultice"]
            found_item = random.choice(forage_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"You successfully forage: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_FOUND", f"Foraging success: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            print("You don't find anything edible, but you learn about the local plant life.")
            log_game_event("EXPLORATION_RESULT", "Foraging failed - no edible plants found", player_character.get('name'), always_log=True)
            
    elif action == "search_rocks":
        success_chance = 0.4
        log_game_event("EXPLORATION_ACTION", f"Searching rock crevices (success chance: {success_chance})", player_character.get('name'), always_log=True)
        if random.random() < success_chance:
            rock_items = ["iron_ore", "copper_ore", "crystal_shard_mundane", "flint_sharp", "obsidian_shard"]
            found_item = random.choice(rock_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"Hidden in the rocks you discover: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_FOUND", f"Rock search success: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            print("The rocks yield no treasures, but you appreciate their ancient beauty.")
            log_game_event("EXPLORATION_RESULT", "Rock search failed - no treasures found", player_character.get('name'), always_log=True)
            
    elif action == "gather_minerals":
        success_chance = 0.3
        log_game_event("EXPLORATION_ACTION", f"Gathering minerals (success chance: {success_chance})", player_character.get('name'), always_log=True)
        if random.random() < success_chance:
            mineral_items = ["iron_ore", "copper_ore", "gem_amethyst_rough", "obsidian_shard"]
            found_item = random.choice(mineral_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"You gather a valuable mineral: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_FOUND", f"Mineral gathering success: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            print("No valuable minerals catch your eye this time.")
            log_game_event("EXPLORATION_RESULT", "Mineral gathering failed - no valuable minerals", player_character.get('name'), always_log=True)
            
    elif action == "experience_search":
        # Higher success rate for experienced characters
        success_chance = 0.5 + (player_character.get('level', 1) * 0.05)
        log_game_event("EXPLORATION_ACTION", f"Using experience to search (success chance: {success_chance:.2f}, level: {player_character.get('level', 1)})", player_character.get('name'), always_log=True)
        if random.random() < success_chance:
            rare_items = ["healing_potion_lesser", "mana_potion_minor", "antidote_simple", "crystal_shard_mundane"]
            found_item = random.choice(rare_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"Your experience pays off! You find: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_FOUND", f"Experience search success: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            print("Even with your experience, this area doesn't reveal its secrets easily.")
            log_game_event("EXPLORATION_RESULT", "Experience search failed - area keeps secrets", player_character.get('name'), always_log=True)
            
    elif action == "track_animals":
        log_game_event("EXPLORATION_ACTION", "Tracking animals", player_character.get('name'), always_log=True)
        if random.random() < 0.4:
            print("The tracks lead you to a small cache of natural materials!")
            track_items = ["animal_hide_small", "bone_fragment", "berries_wild", "herbal_poultice"]
            found_item = random.choice(track_items)
            if found_item in items.ITEM_DB:
                player_character['inventory'].append(found_item)
                print(f"Following the tracks, you find: {items.ITEM_DB[found_item]['name']}!")
                log_game_event("ITEM_FOUND", f"Animal tracking success: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        else:
            print("The tracks lead to a peaceful clearing, but you find nothing material.")
            print("Still, you feel more connected to the natural world.")
            log_game_event("EXPLORATION_RESULT", "Animal tracking failed - peaceful clearing found", player_character.get('name'), always_log=True)

    elif action == "show_crafting":
        print("You realize you have the materials needed to craft useful items!")
        log_game_event("CRAFTING_MENU", "Opened crafting menu from exploration", player_character.get('name'), always_log=True)
        crafting_menu(player_character)

def enhanced_exploration_menu(player_character, location_data):
    """Enhanced exploration menu with multiple options"""
    print(f"\n--- Enhanced Exploration Options ---")
    log_game_event("EXPLORATION_MENU", f"Displaying exploration options at {location_data.get('name')}", player_character.get('name'), always_log=True)
    
    # Get environmental interactions
    interactions = get_environmental_interactions(location_data, player_character)
    
    # Create menu options
    options = []
    for i, interaction in enumerate(interactions, 1):
        options.append(f"{interaction['name']} - {interaction['description']}")
    
    options.append("Look for Specific Points of Interest (Classic)")
    options.append("Wait and See What Happens")
    options.append("Return to Main Menu")
    
    choice = ui.get_numbered_choice("What would you like to do?", options)
    log_game_event("EXPLORATION_CHOICE", f"Player selected: {choice}", player_character.get('name'), always_log=True)
    
    # Handle choice
    if choice == "Return to Main Menu":
        log_game_event("EXPLORATION_RESULT", "Returned to main menu", player_character.get('name'), always_log=True)
        return "back"
    elif choice == "Look for Specific Points of Interest (Classic)":
        log_game_event("EXPLORATION_RESULT", "Selected classic POI exploration", player_character.get('name'), always_log=True)
        return "classic_poi"
    elif choice == "Wait and See What Happens":
        print(f"\nYou pause and observe your surroundings, letting the world reveal itself...")
        log_game_event("EXPLORATION_ACTION", "Wait and See What Happens - generating dynamic event", player_character.get('name'), always_log=True)
        
        # Generate and execute dynamic event
        event = generate_dynamic_exploration_event(player_character, location_data)
        if event:
            log_game_event("DYNAMIC_EVENT", f"Generated event: {event['name']} - {event['description']}", player_character.get('name'), always_log=True)
            execute_exploration_event(event, player_character, location_data)
        else:
            print("Time passes peacefully. Sometimes, quiet moments are just as valuable as grand discoveries.")
            log_game_event("DYNAMIC_EVENT", "No event generated - peaceful moment", player_character.get('name'), always_log=True)
            # Small chance of still finding something
            if random.random() < 0.1:
                common_items = location_data.get('items_common_find', [])
                if common_items:
                    found_item = random.choice(common_items)
                    if found_item in items.ITEM_DB:
                        player_character['inventory'].append(found_item)
                        print(f"As you wait, you notice: {items.ITEM_DB[found_item]['name']}!")
                        log_game_event("ITEM_FOUND", f"Peaceful wait revealed: {items.ITEM_DB[found_item]['name']}", player_character.get('name'), always_log=True)
        return "continue"
    else:
        # Find the selected interaction
        interaction_index = next(i for i, opt in enumerate(options) if opt == choice)
        if interaction_index < len(interactions):
            selected_interaction = interactions[interaction_index]
            log_game_event("EXPLORATION_SELECTION", f"Selected interaction: {selected_interaction['name']}", player_character.get('name'), always_log=True)
            execute_environmental_interaction(selected_interaction, player_character, location_data)
        return "continue"

def game():
    player = None
    saveload.ensure_save_directory()
    
    # Initialize game logging
    initialize_game_log()
    log_game_event("GAME_START", "Silent Symphony game session started", always_log=True)

    print("Welcome to The Silent Symphony - Main Menu")
    menu_options = ["Start New Game", "Load Game"]
    available_saves = saveload.list_save_files()
    if not available_saves: 
        print("(No save files found to load)")
    
    initial_choice = ui.get_numbered_choice("What would you like to do?", menu_options)
    log_game_event("MENU_CHOICE", f"Player selected: {initial_choice}", always_log=True)

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
                    log_game_event("LOAD_GAME", f"Successfully loaded save: {chosen_save_name}", player.get('name'))
                else:
                    print("Failed to load game. Starting a new game instead.")
                    log_game_event("LOAD_GAME", f"Failed to load save: {chosen_save_name}")
                    initial_choice = "Start New Game" 
        else:
            print("No save games found to load. Starting a new game.")
            initial_choice = "Start New Game"

    if initial_choice == "Start New Game" and player is None: 
        player = character.character_creation()
        if player:
            log_game_event("CHARACTER_CREATION", f"Created character: {player['name']} ({player['race']}, {player['origin']})", player['name'], always_log=True)
    
    if not player: 
        print("No character loaded or created. Exiting game.")
        log_game_event("GAME_END", "Game ended - no character created/loaded", always_log=True)
        return

    game_over = False
    print("\n--- Game Start ---")
    main_game_actions = {
        "1": "Explore this area",
        "2": "Move to another area",
        "3": "Manage Inventory", 
        "4": "View character stats",
        "5": "Character Development",
        "6": "Crafting",
        "7": "Save Game",
        "8": "Quit game"
    }
    
    current_location_id = player['location']
    current_location_data = locations.LOCATIONS.get(current_location_id)

    if not current_location_data:
        print(f"ERROR: Current location ID '{current_location_id}' not found in locations.py! Exiting.")
        log_game_event("ERROR", f"Location not found: {current_location_id}", player['name'])
        return

    # Initial location description with AI
    if player.get('last_described_location') != current_location_id:
        description_prompt = current_location_data.get('description_first_visit_prompt', f"You are at {current_location_data.get('name', current_location_id)}.")
        log_game_event("AI_REQUEST", f"Requesting location description for: {current_location_data.get('name')}", player['name'])
        
        ai_response_obj = ai_utils.get_ai_model_response(description_prompt)
        log_ai_response_full(ai_response_obj, f"Initial location description for {current_location_data.get('name')}", player['name'])
        desc_text = f"You arrive at {current_location_data.get('name', 'this new area')}."
        
        try:
            if isinstance(ai_response_obj, dict) and ai_response_obj.get("error_message"):
                if config.DEBUG_MODE: print(f"DEBUG: AI error for initial loc desc: {ai_response_obj.get('error_message')}")
                log_game_event("AI_ERROR", f"AI error for location description: {ai_response_obj.get('error_message')}", player['name'])
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
                                log_game_event("AI_RESPONSE", f"Gemini location description: {desc_text[:100]}...", player['name'])
                            else:
                                if config.DEBUG_MODE: print(f"DEBUG: Gemini AI attempted unexpected function '{part.function_call.name}' for initial loc desc.")
                                log_game_event("AI_WARNING", f"Unexpected Gemini function: {part.function_call.name}", player['name'])
                            processed_for_initial_desc = True; break
                    if not processed_for_initial_desc and ai_response_obj.candidates[0].content.parts:
                        desc_text = get_text_from_part(ai_response_obj.candidates[0].content.parts[0]) or desc_text
                        log_game_event("AI_RESPONSE", f"Gemini text response: {desc_text[:100]}...", player['name'])
            elif config.AI_PROVIDER == "OPENAI":
                if hasattr(ai_response_obj, 'choices') and ai_response_obj.choices and \
                   hasattr(ai_response_obj.choices[0], 'message'):
                    message = ai_response_obj.choices[0].message
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            if tool_call.function.name == "narrative_outcome":
                                args = json.loads(tool_call.function.arguments)
                                desc_text = args.get('narrative_text', desc_text)
                                log_game_event("AI_RESPONSE", f"OpenAI location description: {desc_text[:100]}...", player['name'])
                                break # Assuming one function call for initial description
                            else:
                                if config.DEBUG_MODE: print(f"DEBUG: OpenAI AI attempted unexpected function '{tool_call.function.name}' for initial loc desc.")
                                log_game_event("AI_WARNING", f"Unexpected OpenAI function: {tool_call.function.name}", player['name'])
                    elif message.content:
                        desc_text = message.content
                        log_game_event("AI_RESPONSE", f"OpenAI content response: {desc_text[:100]}...", player['name'])
            
            if not desc_text.strip() or "[AI Fallback" in desc_text or "[AI Error" in desc_text or "[AI prompt blocked" in desc_text:
                fallback_message = f"Having just arrived at {current_location_data.get('name', 'this new area')}, you take a moment to get your bearings."
                display_message = desc_text if ('[AI Fallback' in desc_text or '[AI Error' in desc_text or '[AI prompt blocked' in desc_text) else fallback_message
                print(f"\n{display_message}")
                log_game_event("AI_FALLBACK", f"Used fallback description: {display_message}", player['name'])
                if config.DEBUG_MODE and desc_text.strip() and desc_text != display_message: 
                    print(f"DEBUG: AI issue for initial loc desc. Fallback used. Original AI text: '{desc_text}'")
            else:
                print(f"\n{desc_text}")
        except Exception as e:
            print(f"Error processing initial location AI response: {e}")
            if config.DEBUG_MODE: import traceback; traceback.print_exc()
            log_game_event("AI_ERROR", f"Exception processing AI response: {str(e)}", player['name'])
            print(f"\nHaving just arrived at {current_location_data.get('name', 'this new area')}, you take a moment to get your bearings. (Exception during AI processing)")
        player['last_described_location'] = current_location_id
        
        # Add pause so player can read the location description
        pause_for_reading()

    while not game_over:
        current_location_id = player['location']
        current_location_data = locations.LOCATIONS.get(current_location_id)
        if not current_location_data: 
            print(f"ERROR: Location '{current_location_id}' is invalid! Resetting to start.")
            player['location'] = "beach_starting"; player['last_described_location'] = None; continue 

        clear_screen()  # Clear screen for better presentation
        print_section_header(f"Current Location: {current_location_data.get('name', current_location_id)}")
        
        # Show quick status
        print(f"🏃 {player['name']} | ❤️  {player['health']}/{player['max_health']} | 🔮 {player['mana']}/{player['max_mana']} | ⭐ Level {player['level']}")
        
        print(f"\nWhat would you like to do?")
        action_choices_display = [f"{key}. {value}" for key, value in main_game_actions.items()]
        for option_display in action_choices_display:
            print(option_display)
        choice_key = input("\n> ").strip()

        # Check for special commands first
        if choice_key.lower() == "/debug":
            config.DEBUG_MODE = not config.DEBUG_MODE
            print(f"Debug mode {'enabled' if config.DEBUG_MODE else 'disabled'}.")
            log_game_event("DEBUG_TOGGLE", f"Debug mode {'enabled' if config.DEBUG_MODE else 'disabled'}", player['name'])
            continue
        elif choice_key.lower() == "/help":
            print("\nSpecial Commands:")
            print("  /debug - Toggle debug mode on/off")
            print("  /help  - Show this help message")
            log_game_event("HELP", "Player accessed help", player['name'])
            continue

        if choice_key in main_game_actions:
            selected_action = main_game_actions[choice_key]
            log_game_event("PLAYER_ACTION", f"Selected action: {selected_action}", player['name'], always_log=True)
            
            if selected_action == 'Explore this area':
                print("\nYou decide to look around more closely...")
                log_game_event("EXPLORATION_START", f"Started exploring: {current_location_data.get('name')}", player['name'])
                
                # First, offer enhanced exploration options
                result = enhanced_exploration_menu(player, current_location_data)
                log_game_event("EXPLORATION_CHOICE", f"Exploration result: {result}", player['name'])
                
                if result == "back":
                    continue  # Return to main menu
                elif result == "continue":
                    # Add pause so player can read the results of their action
                    pause_for_reading()
                elif result == "classic_poi":
                    # Continue with classic POI exploration
                    pass
                else:
                    continue  # Unknown result, return to main menu
                
                # Classic POI exploration (only if selected or if it's the fallback)
                if result == "classic_poi":
                    print("\nYou focus on finding specific points of interest...")
                    pause_for_reading()  # Let player read before continuing
                    
                    # --- Stage 1: Select POIs from Location Definition ---
                    defined_pois_for_location = current_location_data.get('defined_pois', [])
                    
                    # --- Filter out completed POIs ---
                    completed_poi_ids_for_current_location = player['completed_pois'].get(current_location_id, set())
                    
                    if config.DEBUG_MODE:
                        defined_ids = [poi.get('poi_id', 'NO_ID') for poi in defined_pois_for_location]
                        print(f"DEBUG: POI Filter: All defined POI IDs for '{current_location_id}': {defined_ids}")
                        print(f"DEBUG: POI Filter: Completed POI IDs for '{current_location_id}': {completed_poi_ids_for_current_location}")

                    available_pois_for_selection = [
                        poi for poi in defined_pois_for_location 
                        if poi.get('poi_id') not in completed_poi_ids_for_current_location
                    ]
                    if config.DEBUG_MODE:
                        selected_ids = [poi.get('poi_id', 'NO_ID') for poi in available_pois_for_selection]
                        print(f"DEBUG: POI Filter: Available (pre-sample) POI IDs after filtering: {selected_ids}")
                        # Original debug messages, can be kept or removed if redundant with new ones
                        if len(defined_pois_for_location) != len(available_pois_for_selection):
                            print(f"DEBUG: Filtered POIs. Original count: {len(defined_pois_for_location)}, Available for selection count: {len(available_pois_for_selection)}")

                    available_pois_to_present = []
                    if available_pois_for_selection:
                        # Select a subset of POIs to present to the player (e.g., 2 to 4)
                        num_pois_to_offer = min(len(available_pois_for_selection), random.randint(2, 4))
                        available_pois_to_present = random.sample(available_pois_for_selection, num_pois_to_offer)
                        if config.DEBUG_MODE:
                            presented_ids = [poi.get('poi_id', 'NO_ID') for poi in available_pois_to_present]
                            print(f"DEBUG: POI Filter: POIs presented to player (post-sample): {presented_ids}")
                    
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

                    # --- Check if chosen POI was already completed (safeguard) ---
                    if chosen_poi_display_text != "Ignore these and look around generally":
                        # Find the chosen_poi_def again, as it's needed to get the poi_id
                        temp_chosen_poi_def = next((poi for poi in available_pois_to_present if poi.get('display_text_for_player_choice') == chosen_poi_display_text), None)
                        if temp_chosen_poi_def:
                            poi_id_to_check = temp_chosen_poi_def.get('poi_id')
                            if poi_id_to_check and poi_id_to_check in player['completed_pois'].get(current_location_id, set()):
                                print(f"\nYou have already investigated '{chosen_poi_display_text}'. There's nothing new to find there.")
                                if config.DEBUG_MODE: print(f"DEBUG: Player selected an already completed POI '{poi_id_to_check}'. Bypassing interaction.")
                                continue # Skip to the next iteration of the main game loop

                    # --- Stage 3: Resolve Investigation ---
                    outcome_prompt = ""
                    determined_item_ids_to_give = []
                    determined_enemy_id_to_spawn = None
                    # Default to narrative_outcome, specific POI logic might change this
                    expected_function_call_name = "narrative_outcome" 
                    ai_narrative_context = ""
                    chosen_poi_def = None # Initialize chosen_poi_def

                    if chosen_poi_display_text == "Ignore these and look around generally":
                        ai_narrative_context = f"Player {player['name']} is in '{current_location_data.get('name')}' and looks around generally."
                        
                        # Game logic decides the type of general encounter first.
                        # Let's have a chance for item, enemy, or just narrative.
                        rand_outcome = random.random()
                        
                        if rand_outcome < 0.20: # 20% chance to find a common item
                            common_items = current_location_data.get('items_common_find', [])
                            if common_items:
                                # Game determines the item internally. AI will narrate finding *something*.
                                determined_item_ids_to_give.append(random.choice(common_items))
                                expected_function_call_name = "player_discovers_item"
                                ai_narrative_context += " They stumble upon a minor item of interest."
                            else: # No common items defined for this location
                                expected_function_call_name = "narrative_outcome"
                                ai_narrative_context += " They find nothing out of the ordinary."
                        elif rand_outcome < 0.35: # Additional 15% chance for an enemy (total 20% item, 15% enemy)
                            generic_enemy_groups = current_location_data.get('encounter_groups', [])
                            if generic_enemy_groups:
                                group_to_use = random.choice(generic_enemy_groups)
                                determined_enemy_id_to_spawn = get_random_enemy_for_location(current_location_id, specific_group=group_to_use)
                                if determined_enemy_id_to_spawn:
                                    expected_function_call_name = "player_encounters_enemy"
                                    ai_narrative_context += " Suddenly, they are surprised by an enemy!"
                                else: # Failed to spawn an enemy from the group
                                    expected_function_call_name = "narrative_outcome"
                                    ai_narrative_context += " They thought they saw something, but it was just a shadow."
                            else: # No enemy groups defined
                                expected_function_call_name = "narrative_outcome"
                                ai_narrative_context += " The area seems quiet."
                        else: # Default to narrative outcome (65% chance)
                            expected_function_call_name = "narrative_outcome"
                            ai_narrative_context += " They find nothing particularly noteworthy."
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
                                
                            elif poi_type == "environmental_puzzle":
                                handle_environmental_puzzle(chosen_poi_def, player, current_location_data)
                                expected_function_call_name = "narrative_outcome"
                                
                            elif poi_type == "hidden_passage":
                                passage_result = handle_hidden_passage(chosen_poi_def, player, current_location_data)
                                if passage_result:
                                    # Player entered the passage, update location and skip normal flow
                                    current_location_data = locations.LOCATIONS.get(player['location'])
                                    player['last_described_location'] = None
                                    continue
                                expected_function_call_name = "narrative_outcome"
                                
                            elif poi_type == "lore_discovery":
                                handle_lore_discovery(chosen_poi_def, player, current_location_data)
                                expected_function_call_name = "narrative_outcome"
                                
                            elif poi_type == "meditation_spot":
                                handle_meditation_spot(chosen_poi_def, player, current_location_data)
                                expected_function_call_name = "narrative_outcome"
                                
                            elif poi_type == "healing_spring":
                                handle_healing_spring(chosen_poi_def, player, current_location_data)
                                expected_function_call_name = "narrative_outcome"
                                
                            elif poi_type == "shrine":
                                handle_shrine_interaction(chosen_poi_def, player, current_location_data)
                                expected_function_call_name = "narrative_outcome"
                                
                            elif poi_type == "npc_creature":
                                handle_npc_creature(chosen_poi_def, player, current_location_data)
                                expected_function_call_name = "narrative_outcome"
                                
                            else:
                                 expected_function_call_name = "narrative_outcome" # Default for unknown POI types
                        else:
                            ai_narrative_context = f"The player looks at the '{chosen_poi_display_text}' but isn't sure what to make of it."
                            expected_function_call_name = "narrative_outcome"

                    # Construct the AI prompt for Stage 3
                    if expected_function_call_name == "player_discovers_item":
                        # If multiple items, AI should narrate finding them. We pass first item for tagging guidance.
                        # For "look around generally", item_id_for_ai_prompt is now less critical as game picks the item.
                        item_id_for_ai_prompt = determined_item_ids_to_give[0] if determined_item_ids_to_give else "some_trinket"
                        item_name_for_ai_prompt = items.ITEM_DB.get(item_id_for_ai_prompt, {}).get("name", item_id_for_ai_prompt.replace("_"," "))
                        
                        if chosen_poi_display_text == "Ignore these and look around generally":
                            outcome_prompt = f"{ai_narrative_context} The game has determined the player finds a common item from this area. Craft a short narrative for this discovery and call 'player_discovers_item' with your discovery_narrative (the item_id you provide in the function call will be illustrative, the game uses its own). Example item_id: '{item_id_for_ai_prompt}'."
                        else: # Specific POI
                            outcome_prompt = f"{ai_narrative_context} The player finds {len(determined_item_ids_to_give)} item(s). Craft a short narrative for this discovery and call 'player_discovers_item' with item_id='{item_id_for_ai_prompt}' (if multiple items, this is one example ID for the function call) and your discovery_narrative."
                    elif expected_function_call_name == "player_encounters_enemy":
                        enemy_name_for_ai_prompt = entities.ENEMY_TEMPLATES.get(determined_enemy_id_to_spawn, {}).get("name", "a creature")
                        if chosen_poi_display_text == "Ignore these and look around generally":
                             outcome_prompt = f"{ai_narrative_context} The game has determined an enemy encounter from this area's typical inhabitants. Craft a short narrative for this encounter and call 'player_encounters_enemy' with enemy_id='{determined_enemy_id_to_spawn}' (this ID is game-determined) and your encounter_narrative."
                        else: # Specific POI trap
                            outcome_prompt = f"{ai_narrative_context} An enemy ({enemy_name_for_ai_prompt}) appears! Craft a short narrative for this encounter and call 'player_encounters_enemy' with enemy_id='{determined_enemy_id_to_spawn}' and your encounter_narrative."
                    else: # narrative_outcome
                        outcome_prompt = f"{ai_narrative_context} Describe this scene or outcome. Call 'narrative_outcome' with your narrative_text."

                    if config.DEBUG_MODE: print(f"DEBUG (Stage 3 AI Prompt): {outcome_prompt}")
                    ai_response_stage3 = ai_utils.get_ai_model_response(outcome_prompt)
                    function_called_successfully = False
                    combat_occurred_this_action = False # Flag for this "Explore this area" action

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
                                            if chosen_poi_display_text == "Ignore these and look around generally":
                                                # Game already determined the item(s) in determined_item_ids_to_give
                                                if determined_item_ids_to_give:
                                                    for item_id in determined_item_ids_to_give: # Should usually be one for this path
                                                        if item_id in items.ITEM_DB:
                                                            player['inventory'].append(item_id)
                                                            print(f"You obtained: {items.ITEM_DB[item_id]['name']}! Added to inventory.")
                                                        elif config.DEBUG_MODE: print(f"DEBUG: Game logic for 'general look around' provided unknown item_id: {item_id}")
                                                else: # Game logic decided item, but list was empty or error
                                                    if config.DEBUG_MODE: print(f"DEBUG: 'General look around' was to give item, but determined_item_ids_to_give is empty.")
                                                    print("...but it turns out to be nothing of consequence.")
                                            else: # Item discovery from a specific POI
                                                if determined_item_ids_to_give: # Use game-determined items
                                                    for item_id in determined_item_ids_to_give:
                                                        if item_id in items.ITEM_DB:
                                                            player['inventory'].append(item_id)
                                                            print(f"You obtained: {items.ITEM_DB[item_id]['name']}! Added to inventory.")
                                                        elif config.DEBUG_MODE: print(f"DEBUG: Game logic provided unknown item_id for POI: {item_id}")
                                                else: 
                                                    if config.DEBUG_MODE: print(f"DEBUG: POI AI called discover_item but game logic had no items.")
                                            function_called_successfully = True; break
                                        
                                        elif function_call.name == "player_encounters_enemy":
                                            narrative = function_call.args.get('encounter_narrative', "Danger appears!")
                                            print(f"\n{narrative}")
                                            # Combat will be initiated AFTER the try/except block based on determined_enemy_id_to_spawn
                                            function_called_successfully = True; break
                                        
                                        elif function_call.name == "narrative_outcome":
                                            narrative = function_call.args.get('narrative_text', "You observe your surroundings quietly."); print(f"\n{narrative}");
                                            function_called_successfully = True; break
                                        else: print("\nA strange feeling washes over you..."); function_called_successfully = True; break
                        
                        # --- Mark POI as completed after successful interaction ---
                        if function_called_successfully and chosen_poi_def and chosen_poi_def != "Ignore these and look around generally":
                            poi_id_to_complete = chosen_poi_def.get('poi_id')
                            poi_type = chosen_poi_def.get('type')
                            if poi_id_to_complete:
                                # Conditions for marking as completed:
                                # - loot_container: if opened (looted/empty) or trap sprung. Not if locked and failed.
                                # - loot_scatter: if success or fail (opportunity gone).
                                # - clue_object, simple_description, navigation_hint: after first interaction.
                                mark_completed = False
                                if poi_type == "loot_container":
                                    # Assuming 'is_locked' and 'can_unlock' were determined earlier
                                    # We need to infer if it was successfully opened or trap sprung
                                    # This part might need refinement based on actual game flow variables
                                    # For now, assume if function_called_successfully, it means it was resolved.
                                    # A more robust way would be to check specific outcomes.
                                    # Let's assume if it's not "It's locked." narrative, it's resolved.
                                    # This is a placeholder for more precise logic later if needed.
                                    is_locked_and_failed = chosen_poi_def.get('locked', False) and not True # Replace True with actual can_unlock status if available
                                    if not is_locked_and_failed:
                                        mark_completed = True
                                elif poi_type == "loot_scatter":
                                    mark_completed = True # Always completed after attempt
                                elif poi_type in ["clue_object", "simple_description", "navigation_hint"]:
                                    mark_completed = True
                                
                                if mark_completed:
                                    player['completed_pois'].setdefault(current_location_id, set()).add(poi_id_to_complete)
                                    if config.DEBUG_MODE: print(f"DEBUG: Marked POI '{poi_id_to_complete}' in '{current_location_id}' as completed.")
                        # This block should be outside the AI-specific path or called reliably.
                        # Let's move the POI completion marking to after the try-except for AI response handling.
                                
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
                                        if chosen_poi_display_text == "Ignore these and look around generally":
                                            # Game already determined the item(s) in determined_item_ids_to_give
                                            if determined_item_ids_to_give:
                                                for item_id in determined_item_ids_to_give: # Should usually be one for this path
                                                    if item_id in items.ITEM_DB:
                                                        player['inventory'].append(item_id)
                                                        print(f"You obtained: {items.ITEM_DB[item_id]['name']}! Added to inventory.")
                                                    elif config.DEBUG_MODE: print(f"DEBUG: Game logic for 'general look around' (OpenAI) provided unknown item_id: {item_id}")
                                            else: # Game logic decided item, but list was empty or error
                                                if config.DEBUG_MODE: print(f"DEBUG: 'General look around' (OpenAI) was to give item, but determined_item_ids_to_give is empty.")
                                                print("...but it turns out to be nothing of consequence.")
                                        else: # Item discovery from a specific POI
                                            if determined_item_ids_to_give:
                                                for item_id in determined_item_ids_to_give:
                                                    if item_id in items.ITEM_DB: player['inventory'].append(item_id); print(f"You obtained: {items.ITEM_DB[item_id]['name']}! Added to inventory.")
                                                    elif config.DEBUG_MODE: print(f"DEBUG: Game logic provided unknown item_id for POI (OpenAI): {item_id}")
                                            else: print("It seemed valuable, but crumbled to dust.")
                                        function_called_successfully = True; break
                                    
                                    elif function_name == "player_encounters_enemy":
                                        narrative = args.get('encounter_narrative', "Danger appears!")
                                        print(f"\n{narrative}")
                                        # Combat will be initiated AFTER the try/except block based on determined_enemy_id_to_spawn
                                        function_called_successfully = True; break
                                    
                                    elif function_name == "narrative_outcome":
                                        narrative = args.get('narrative_text', "You observe your surroundings quietly."); print(f"\n{narrative}");
                                        function_called_successfully = True; break
                                    else: print("\nA strange feeling washes over you..."); function_called_successfully = True; break

                                # --- Mark POI as completed after successful interaction (OpenAI path) ---
                                if function_called_successfully and chosen_poi_def and chosen_poi_def != "Ignore these and look around generally":
                                    poi_id_to_complete = chosen_poi_def.get('poi_id')
                                    poi_type = chosen_poi_def.get('type')
                                    if poi_id_to_complete:
                                        mark_completed = False
                                        if poi_type == "loot_container":
                                            is_locked_and_failed = chosen_poi_def.get('locked', False) and not True # Placeholder for can_unlock
                                            if not is_locked_and_failed:
                                                mark_completed = True
                                        elif poi_type == "loot_scatter":
                                            mark_completed = True
                                        elif poi_type in ["clue_object", "simple_description", "navigation_hint"]:
                                            mark_completed = True
                                        
                                        if mark_completed:
                                            player['completed_pois'].setdefault(current_location_id, set()).add(poi_id_to_complete)
                                            if config.DEBUG_MODE: print(f"DEBUG: Marked POI '{poi_id_to_complete}' in '{current_location_id}' as completed (OpenAI path).")
                        # This block should be outside the AI-specific path or called reliably.
                        # Let's move the POI completion marking to after the try-except for AI response handling.

                        if not function_called_successfully: 
                            # ... (fallback if AI didn't make a valid function call at all in Stage 3)
                            # (Simplified fallback text extraction)
                            # Try to get text from AI response if it exists and is simple text
                            fallback_narrative = "You investigate, but nothing definitive happens."
                            if config.AI_PROVIDER == "GEMINI":
                                if hasattr(ai_response_stage3, 'candidates') and ai_response_stage3.candidates and \
                                hasattr(ai_response_stage3.candidates[0], 'content') and hasattr(ai_response_stage3.candidates[0].content, 'parts') and \
                                ai_response_stage3.candidates[0].content.parts and not hasattr(ai_response_stage3.candidates[0].content.parts[0], 'function_call'):
                                    fallback_narrative = get_text_from_part(ai_response_stage3.candidates[0].content.parts[0]) or fallback_narrative
                            elif config.AI_PROVIDER == "OPENAI":
                                if hasattr(ai_response_stage3, 'choices') and ai_response_stage3.choices and \
                                hasattr(ai_response_stage3.choices[0], 'message') and ai_response_stage3.choices[0].message.content:
                                    fallback_narrative = ai_response_stage3.choices[0].message.content or fallback_narrative
                            # Only print fallback if a more specific narrative wasn't already printed by a successful function call
                            if not function_called_successfully: # Re-check, as successful calls print their own narrative
                               print(f"\n{fallback_narrative}")
                            if config.DEBUG_MODE: print(f"DEBUG: Stage 3 AI did not call a specific function or provide recognized output. Printed fallback or direct text if available.")

                    except Exception as e_stage3:
                        # ... (exception handling)
                        print(f"Error processing exploration outcome: {e_stage3}")
                        if config.DEBUG_MODE: import traceback; traceback.print_exc()
                        print("\nThe world seems to momentarily warp around your focus, then settles.")

                    # --- Initiate Combat if Determined by Game Logic (Moved from AI response handling) ---
                    if not combat_occurred_this_action and expected_function_call_name == "player_encounters_enemy" and determined_enemy_id_to_spawn:
                        if not function_called_successfully: # AI failed to narrate the encounter specifically
                            print("\nDanger erupts suddenly!") # Generic fallback encounter initiation narrative
                        
                        enemy_instance = entities.get_enemy_instance(determined_enemy_id_to_spawn)
                        if enemy_instance:
                            if config.DEBUG_MODE: print(f"DEBUG: Game logic initiating combat with {determined_enemy_id_to_spawn} (AI success: {function_called_successfully}).")
                            combat_result = combat.combat(player, enemy_instance)
                            game_over = True if combat_result == "lost" else game_over
                            combat_occurred_this_action = True
                        else:
                            if config.DEBUG_MODE: print(f"DEBUG: Game logic determined enemy '{determined_enemy_id_to_spawn}', but failed to get instance.")
                            if not function_called_successfully: print("The sense of danger fades as quickly as it came.")
                    
                    # --- Mark POI as completed (Moved and Revised Logic) ---
                    # Ensure chosen_poi_def is not None before trying to access its attributes
                    if chosen_poi_def is not None: 
                        # And ensure it's not the placeholder for "Ignore these..." if that could ever be an object
                        # However, chosen_poi_def is None if "Ignore these..." was selected.
                        poi_id_to_complete = chosen_poi_def.get('poi_id')
                        poi_type = chosen_poi_def.get('type')
                        if poi_id_to_complete:
                            mark_completed_flag = False # Renamed from mark_completed to avoid scope issues if any
                            
                            # Determine if POI interaction itself warrants completion
                            # This logic should use flags set during the POI resolution (before AI call)
                            # For now, we'll use the existing poi_type checks but make them more robust
                            # to the AI not succeeding.
                            
                            if poi_type == "loot_container":
                                is_locked = chosen_poi_def.get('locked', False)
                                # Placeholder for actual unlock check logic. For now, assuming it can be unlocked if attempted.
                                # This 'can_unlock_attempt_made_and_succeeded' would be set earlier in the POI interaction logic.
                                # For this fix, we'll rely on the trap or non-locked status.
                                # The key condition is that an interaction RESOLVED the POI.
                                
                                trap_sprung_for_this_poi = (chosen_poi_def.get('trap_enemy_id') and \
                                                            determined_enemy_id_to_spawn == chosen_poi_def.get('trap_enemy_id') and \
                                                            expected_function_call_name == "player_encounters_enemy") # Ensure this enemy spawn was for the POI trap

                                opened_without_trap_or_after_disarm = False
                                if not trap_sprung_for_this_poi: # Only consider opening if a trap didn't spring or doesn't exist
                                    if not is_locked: # Not locked
                                        opened_without_trap_or_after_disarm = True
                                    elif is_locked and True: # Locked, but can_unlock is currently True (placeholder)
                                        # This assumes the interaction attempt included trying to open it.
                                        # A more robust check would be if expected_function_call_name was 'player_discovers_item' for this POI
                                        # or a specific narrative for an empty container.
                                        # For now, if it wasn't a trap and it was "resolved" (AI called or fallback), assume opened.
                                        if expected_function_call_name != "player_encounters_enemy": # Avoid marking complete if it was locked and trap failed
                                            opened_without_trap_or_after_disarm = True
                                
                                if trap_sprung_for_this_poi or opened_without_trap_or_after_disarm:
                                    mark_completed_flag = True
                                    
                            elif poi_type == "loot_scatter":
                                mark_completed_flag = True # Always completed after attempt
                            elif poi_type in ["clue_object", "simple_description", "navigation_hint"]:
                                mark_completed_flag = True # Completed after first interaction
                            
                            if mark_completed_flag:
                                player['completed_pois'].setdefault(current_location_id, set()).add(poi_id_to_complete)
                                if config.DEBUG_MODE: print(f"DEBUG: Marked POI '{poi_id_to_complete}' in '{current_location_id}' as completed (Revised Location).")
                            
                    # --- General Random Encounter Chance (Post-Action) ---
                    if not game_over and not combat_occurred_this_action: # Only if player is alive and no combat happened yet this action
                        if random.random() < config.GENERAL_RANDOM_ENCOUNTER_CHANCE: # e.g. 0.20 for 20%
                            if config.DEBUG_MODE: print(f"DEBUG: General random encounter triggered (chance: {config.GENERAL_RANDOM_ENCOUNTER_CHANCE}).")
                            random_enemy_id = get_random_enemy_for_location(current_location_id)
                            if random_enemy_id:
                                enemy_instance = entities.get_enemy_instance(random_enemy_id)
                                if enemy_instance:
                                    # Simple lead-in narratives
                                    lead_in_narratives = [
                                        "Suddenly, you are ambushed!",
                                        "You hear a rustling nearby, and a wild creature appears!",
                                        "A shadow darts from the corner of your eye - an enemy attacks!",
                                        "The air grows cold... you are not alone!"
                                    ]
                                    print(f"\n{random.choice(lead_in_narratives)}")
                                    combat_result = combat.combat(player, enemy_instance)
                                    if combat_result == "lost":
                                        game_over = True
                                    # combat_occurred_this_action = True # Not strictly needed here as it's the end of the action
                                else:
                                    if config.DEBUG_MODE: print(f"DEBUG: General random encounter failed to spawn enemy instance for ID: {random_enemy_id}")
                            else:
                                if config.DEBUG_MODE: print(f"DEBUG: General random encounter triggered, but get_random_enemy_for_location returned None for location {current_location_id}.")
            
            elif selected_action == 'Move to another area':
                print("\nWhere would you like to go?")
                log_game_event("MOVEMENT_MENU", f"Displaying movement options from {current_location_data.get('name')}", player['name'], always_log=True)
                available_exits = current_location_data.get('exits', {})
                if not available_exits:
                    print("There are no obvious exits from this area.")
                    log_game_event("MOVEMENT_RESULT", "No exits available from current location", player['name'], always_log=True)
                    continue
                exit_options = []
                exit_destinations = [] 
                for direction, destination_id in available_exits.items():
                    destination_name = locations.LOCATIONS.get(destination_id, {}).get('name', destination_id)
                    exit_options.append(f"{direction.capitalize()} (to {destination_name})")
                    exit_destinations.append(destination_id)
                exit_options.append("[Stay Here]")
                chosen_exit_display = ui.get_numbered_choice("Choose a direction:", exit_options)
                log_game_event("MOVEMENT_CHOICE", f"Player selected: {chosen_exit_display}", player['name'], always_log=True)
                
                if chosen_exit_display != "[Stay Here]":
                    chosen_index = exit_options.index(chosen_exit_display)
                    new_location_id = exit_destinations[chosen_index]
                    old_location = current_location_data.get('name')
                    player['location'] = new_location_id
                    player['last_described_location'] = None 
                    new_location_data = locations.LOCATIONS.get(new_location_id)
                    
                    log_game_event("MOVEMENT", f"Moving from {old_location} to {new_location_data.get('name') if new_location_data else new_location_id}", player['name'], always_log=True)
                    
                    if new_location_data:
                        desc_prompt_key = 'description_first_visit_prompt' 
                        description_prompt = new_location_data.get(desc_prompt_key, f"You arrive at {new_location_data.get('name')}.")
                        print(f"\nMoving to {new_location_data.get('name')}...")
                        
                        log_game_event("AI_REQUEST", f"Requesting movement description for: {new_location_data.get('name')}", player['name'], always_log=True)
                        ai_loc_resp = ai_utils.get_ai_model_response(description_prompt)
                        log_ai_response_full(ai_loc_resp, f"Movement description for {new_location_data.get('name')}", player['name'])
                        loc_desc_text = f"You arrive at {new_location_data.get('name', 'the new area')}."
                        
                        if isinstance(ai_loc_resp, dict) and ai_loc_resp.get("error_message"):
                            if config.DEBUG_MODE: print(f"DEBUG: AI error for new loc desc: {ai_loc_resp.get('error_message')}")
                            log_game_event("AI_ERROR", f"AI error for movement description: {ai_loc_resp.get('error_message')}", player['name'], always_log=True)
                        elif config.AI_PROVIDER == "GEMINI":
                            if hasattr(ai_loc_resp, 'candidates') and ai_loc_resp.candidates and hasattr(ai_loc_resp.candidates[0],'content') and hasattr(ai_loc_resp.candidates[0].content, 'parts'):
                                try:
                                    processed_loc_desc = False
                                    for part in ai_loc_resp.candidates[0].content.parts:
                                        if hasattr(part, 'function_call') and part.function_call:
                                            called_fn = part.function_call
                                            if called_fn.name == "narrative_outcome": 
                                                loc_desc_text = called_fn.args.get('narrative_text', loc_desc_text)
                                                log_game_event("AI_RESPONSE", f"Gemini movement description: {loc_desc_text}", player['name'], always_log=True)
                                            else: pass # Ignore other functions for loc desc
                                            processed_loc_desc = True; break
                                    if not processed_loc_desc and ai_loc_resp.candidates[0].content.parts: 
                                        loc_desc_text = get_text_from_part(ai_loc_resp.candidates[0].content.parts[0]) or loc_desc_text
                                        log_game_event("AI_RESPONSE", f"Gemini text movement description: {loc_desc_text}", player['name'], always_log=True)
                                except Exception as e_loc_parse: 
                                    print(f"Error parsing new Gemini loc AI response parts: {e_loc_parse}")
                                    log_game_event("AI_ERROR", f"Error parsing Gemini movement response: {str(e_loc_parse)}", player['name'], always_log=True)
                        elif config.AI_PROVIDER == "OPENAI":
                             if hasattr(ai_loc_resp, 'choices') and ai_loc_resp.choices and hasattr(ai_loc_resp.choices[0],'message'):
                                message = ai_loc_resp.choices[0].message
                                if message.tool_calls:
                                    for tool_call in message.tool_calls:
                                        if tool_call.function.name == "narrative_outcome":
                                            try: 
                                                args = json.loads(tool_call.function.arguments)
                                                loc_desc_text = args.get('narrative_text', loc_desc_text)
                                                log_game_event("AI_RESPONSE", f"OpenAI movement description: {loc_desc_text}", player['name'], always_log=True)
                                                break
                                            except json.JSONDecodeError: pass # Ignore malformed args
                                elif message.content: 
                                    loc_desc_text = message.content
                                    log_game_event("AI_RESPONSE", f"OpenAI content movement description: {loc_desc_text}", player['name'], always_log=True)
                        print(f"\n{loc_desc_text}")
                        player['last_described_location'] = new_location_id
                    else:
                        print(f"Error: Could not find data for location {new_location_id}.")
                        log_game_event("ERROR", f"Could not find data for location: {new_location_id}", player['name'], always_log=True)
                else:
                    log_game_event("MOVEMENT_RESULT", "Player chose to stay in current location", player['name'], always_log=True)
                    
            elif selected_action == 'Manage Inventory': 
                log_game_event("INVENTORY_MENU", "Opening inventory management", player['name'], always_log=True)
                manage_inventory(player)
                
            elif selected_action == 'View character stats':
                log_game_event("CHARACTER_STATS", "Viewing character stats", player['name'], always_log=True)
                print("\n--- Character Stats ---")
                print(f"Name: {player['name']}")
                print(f"Race: {player['race']}")
                print(f"Origin: {player['origin']}")
                print(f"Star Sign: {player['star_sign']}")
                print(f"Health: {player['health']}/{player['max_health']}")
                print(f"Level: {player['level']}")
                print(f"XP: {player['xp']}/{player['xp_to_next_level']}")
                print(f"Mana: {player.get('mana', 0)}/{player.get('max_mana', 0)}")
                equipped_weapon_name = items.ITEM_DB[player['equipped_weapon']]['name'] if player['equipped_weapon'] else "None"
                equipped_armor_name = items.ITEM_DB[player['equipped_armor']]['name'] if player['equipped_armor'] else "None"
                equipped_shield_name = items.ITEM_DB[player['equipped_shield']]['name'] if player['equipped_shield'] else "None"
                print(f"Equipped Weapon: {equipped_weapon_name}")
                print(f"Equipped Armor: {equipped_armor_name}")
                print(f"Equipped Shield: {equipped_shield_name}")
                log_game_event("CHARACTER_STATS_DETAIL", f"Level {player['level']}, HP: {player['health']}/{player['max_health']}, XP: {player['xp']}/{player['xp_to_next_level']}, Weapon: {equipped_weapon_name}", player['name'], always_log=True)
                
            elif selected_action == 'Character Development':
                log_game_event("CHARACTER_DEV", "Opening character development", player['name'], always_log=True)
                character.character_development(player)
                
            elif selected_action == 'Crafting':
                log_game_event("CRAFTING_MENU", "Opening crafting menu", player['name'], always_log=True)
                crafting_menu(player)
                
            elif selected_action == 'Save Game':
                log_game_event("SAVE_MENU", "Opening save game menu", player['name'], always_log=True)
                saveload.save_game_menu(player)
                
            elif selected_action == 'Quit game':
                print("Thank you for playing The Silent Symphony!")
                log_game_event("GAME_END", "Player chose to quit game", player['name'], always_log=True)
                game_over = True
        else:
            print("Invalid choice. Please try again.")
            log_game_event("INVALID_CHOICE", f"Player entered invalid choice: '{choice_key}'", player['name'], always_log=True)
        
        if player['health'] <= 0 and not game_over: 
            print("\nYou have succumbed to your wounds. Your journey ends.")
            log_game_event("GAME_END", "Player died - health reached 0", player['name'], always_log=True)
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

# --- Simple Crafting System ---
CRAFTING_RECIPES = {
    "improvised_torch": {
        "name": "Improvised Torch",
        "description": "A basic torch for light and warmth",
        "result_item": "torch_unlit",
        "materials": [
            {"item_id": "timber_rough", "quantity": 1},
            {"item_id": "torn_rag", "quantity": 1}
        ],
        "skill_level": 1
    },
    "simple_bandage": {
        "name": "Simple Bandage", 
        "description": "Basic first aid from cloth scraps",
        "result_item": "herbal_poultice",
        "materials": [
            {"item_id": "torn_rag", "quantity": 2},
            {"item_id": "sunpetal_leaf", "quantity": 1}
        ],
        "skill_level": 1
    },
    "basic_rope": {
        "name": "Basic Rope",
        "description": "Useful rope twisted from plant fibers",
        "result_item": "rope_hempen_10ft", 
        "materials": [
            {"item_id": "spider_silk_strand", "quantity": 3},
            {"item_id": "string_piece", "quantity": 2}
        ],
        "skill_level": 2
    },
    "sharpened_tool": {
        "name": "Sharpened Tool",
        "description": "A crude but functional cutting implement",
        "result_item": "rusty_dagger",
        "materials": [
            {"item_id": "flint_sharp", "quantity": 1},
            {"item_id": "timber_rough", "quantity": 1},
            {"item_id": "string_piece", "quantity": 1}
        ],
        "skill_level": 2
    }
}

def get_available_recipes(player_character):
    """Get recipes the player can currently craft"""
    available = []
    player_level = player_character.get('level', 1)
    inventory = player_character.get('inventory', [])
    
    # Count items in inventory
    item_counts = {}
    for item_id in inventory:
        item_counts[item_id] = item_counts.get(item_id, 0) + 1
    
    for recipe_id, recipe in CRAFTING_RECIPES.items():
        # Check skill level
        if player_level < recipe.get('skill_level', 1):
            continue
            
        # Check materials
        can_craft = True
        for material in recipe['materials']:
            needed = material['quantity']
            available_count = item_counts.get(material['item_id'], 0)
            if available_count < needed:
                can_craft = False
                break
        
        if can_craft:
            available.append(recipe_id)
    
    return available

def craft_item(player_character, recipe_id):
    """Craft an item using a recipe"""
    if recipe_id not in CRAFTING_RECIPES:
        log_game_event("CRAFTING_ERROR", f"Invalid recipe ID: {recipe_id}", player_character.get('name'), always_log=True)
        return False
        
    recipe = CRAFTING_RECIPES[recipe_id]
    log_game_event("CRAFTING_START", f"Starting craft: {recipe['name']}", player_character.get('name'), always_log=True)
    
    # Log materials being consumed
    materials_consumed = []
    for material in recipe['materials']:
        for _ in range(material['quantity']):
            if material['item_id'] in player_character['inventory']:
                player_character['inventory'].remove(material['item_id'])
                materials_consumed.append(items.ITEM_DB.get(material['item_id'], {}).get('name', material['item_id']))
    
    log_game_event("CRAFTING_MATERIALS", f"Consumed materials: {', '.join(materials_consumed)}", player_character.get('name'), always_log=True)
    
    # Add crafted item
    result_item = recipe['result_item']
    player_character['inventory'].append(result_item)
    
    result_item_name = items.ITEM_DB.get(result_item, {}).get('name', result_item)
    print(f"You crafted: {result_item_name}!")
    log_game_event("CRAFTING_SUCCESS", f"Successfully crafted: {result_item_name}", player_character.get('name'), always_log=True)
    return True

def crafting_menu(player_character):
    """Interactive crafting menu"""
    log_game_event("CRAFTING_MENU", "Entered crafting menu", player_character.get('name'), always_log=True)
    available_recipes = get_available_recipes(player_character)
    
    if not available_recipes:
        print("You don't have the materials or skills to craft anything right now.")
        print("Gather more materials by exploring, or level up to unlock more recipes!")
        log_game_event("CRAFTING_RESULT", "No craftable recipes available", player_character.get('name'), always_log=True)
        return
    
    print(f"\n--- Crafting Menu ---")
    print("You can craft the following items:")
    log_game_event("CRAFTING_AVAILABLE", f"Available recipes: {len(available_recipes)} - {', '.join([CRAFTING_RECIPES[r]['name'] for r in available_recipes])}", player_character.get('name'), always_log=True)
    
    recipe_options = []
    for recipe_id in available_recipes:
        recipe = CRAFTING_RECIPES[recipe_id]
        materials_text = ", ".join([f"{mat['quantity']}x {items.ITEM_DB.get(mat['item_id'], {}).get('name', mat['item_id'])}" 
                                   for mat in recipe['materials']])
        recipe_options.append(f"{recipe['name']} - {recipe['description']} (Needs: {materials_text})")
    
    recipe_options.append("Cancel")
    
    choice = ui.get_numbered_choice("What would you like to craft?", recipe_options)
    log_game_event("CRAFTING_CHOICE", f"Player selected: {choice}", player_character.get('name'), always_log=True)
    
    if choice == "Cancel":
        log_game_event("CRAFTING_RESULT", "Player cancelled crafting", player_character.get('name'), always_log=True)
        return
    
    # Find the selected recipe
    chosen_index = recipe_options.index(choice)
    if chosen_index < len(available_recipes):
        chosen_recipe_id = available_recipes[chosen_index]
        log_game_event("CRAFTING_ATTEMPT", f"Attempting to craft: {CRAFTING_RECIPES[chosen_recipe_id]['name']}", player_character.get('name'), always_log=True)
        craft_item(player_character, chosen_recipe_id)

# --- New POI Interaction Handlers ---
def handle_environmental_puzzle(poi, player_character, location):
    """Handle environmental puzzle interactions"""
    puzzle_type = poi.get("puzzle_type")
    puzzle_def = locations.ENVIRONMENTAL_PUZZLES.get(puzzle_type, {})
    
    print(f"\n🧩 {puzzle_def.get('name', 'Environmental Puzzle')} 🧩")
    print(puzzle_def.get('description', 'A mysterious puzzle...'))
    log_game_event("PUZZLE_ENCOUNTERED", f"Found puzzle: {puzzle_type}", player_character.get('name'))
    
    # Allow skill checks for hints
    skill_checks = puzzle_def.get('skill_checks', [])
    for check in skill_checks:
        skill = check['skill']
        dc = check['dc']
        roll = random.randint(1, 20) + player_character.get(skill, 0) + player_character.get('level', 1)
        
        if roll >= dc:
            hint_idx = check['hint_revealed']
            hints = puzzle_def.get('solution_hints', [])
            if hint_idx < len(hints):
                print(f"\n💡 Insight: {hints[hint_idx]}")
                log_game_event("PUZZLE_HINT", f"Revealed hint: {hints[hint_idx]}", player_character.get('name'))
    
    # Check if player has required item or meets conditions
    success_reward = poi.get("success_reward")
    if success_reward:
        print("\nAttempt to solve the puzzle? (y/n)")
        if input().lower() == 'y':
            # Simplified puzzle solving - could be expanded
            if random.random() < 0.5:  # 50% base chance
                print("\nSuccess! The puzzle yields to your efforts.")
                if success_reward in items.ITEM_DB:
                    player_character['inventory'].append(success_reward)
                    print(f"You receive: {items.ITEM_DB[success_reward]['name']}!")
                    log_game_event("PUZZLE_SOLVED", f"Solved! Reward: {items.ITEM_DB[success_reward]['name']}", player_character.get('name'))
                    # Mark puzzle as solved
                    if 'solved_puzzles' not in player_character:
                        player_character['solved_puzzles'] = []
                    player_character['solved_puzzles'].append(poi.get('poi_id'))
            else:
                print("\nThe puzzle remains unsolved... for now.")
                log_game_event("PUZZLE_FAILED", "Failed to solve puzzle", player_character.get('name'))

def handle_hidden_passage(poi, player_character, location):
    """Handle hidden passage discovery"""
    requirements = poi.get("requirements", {})
    leads_to = poi.get("leads_to")
    
    # Check requirements
    can_access = True
    if requirements.get("perception"):
        perception_check = random.randint(1, 20) + player_character.get('perception', 0) + player_character.get('level', 1)
        if perception_check < requirements["perception"]:
            can_access = False
            print("You sense something here, but can't quite make it out...")
            log_game_event("HIDDEN_PASSAGE_FAILED", "Failed perception check", player_character.get('name'))
    
    if requirements.get("or_item") and requirements["or_item"] in player_character.get('inventory', []):
        can_access = True
        print(f"Your {items.ITEM_DB[requirements['or_item']]['name']} reveals the way!")
        log_game_event("HIDDEN_PASSAGE_ITEM", f"Used {requirements['or_item']} to reveal passage", player_character.get('name'))
    
    if can_access and leads_to:
        destination = locations.LOCATIONS.get(leads_to, {})
        print(f"\n✨ You've discovered a hidden passage to {destination.get('name', 'a mysterious place')}! ✨")
        log_game_event("HIDDEN_PASSAGE_FOUND", f"Discovered passage to: {leads_to}", player_character.get('name'))
        
        # Could add this as a new exit or allow immediate travel
        print("Enter the hidden passage? (y/n)")
        if input().lower() == 'y':
            player_character['location'] = leads_to
            log_game_event("HIDDEN_PASSAGE_ENTERED", f"Entered passage to: {leads_to}", player_character.get('name'))
            return True

def handle_lore_discovery(poi, player_character, location):
    """Handle lore fragment discoveries"""
    lore_fragments = poi.get("lore_fragments", [])
    search_dc = poi.get("search_dc", 10)
    
    print("\nYou carefully search the area...")
    log_game_event("LORE_SEARCH", f"Searching {poi.get('display_text_for_player_choice', 'area')}", player_character.get('name'))
    
    search_roll = random.randint(1, 20) + player_character.get('perception', 0) + player_character.get('level', 1)
    
    if search_roll >= search_dc:
        print("Your search is rewarded!")
        for fragment_id in lore_fragments:
            discover_lore_fragment(fragment_id, player_character)
    else:
        print("You find nothing of particular interest.")
        log_game_event("LORE_SEARCH_FAILED", "No lore discovered", player_character.get('name'))

def handle_meditation_spot(poi, player_character, location):
    """Handle meditation spot interactions"""
    benefits = poi.get("benefits", {})
    
    print("\nThis place emanates a peaceful energy. Meditate here? (y/n)")
    if input().lower() == 'y':
        print("\nYou sit and clear your mind, letting the energy of this place flow through you...")
        log_game_event("MEDITATION_START", f"Meditating at {poi.get('display_text_for_player_choice', 'spot')}", player_character.get('name'))
        
        # Apply benefits
        if benefits.get("mana_restore"):
            restored = min(benefits["mana_restore"], player_character['max_mana'] - player_character['mana'])
            player_character['mana'] += restored
            print(f"Restored {restored} mana points.")
            log_game_event("MEDITATION_MANA", f"Restored {restored} MP", player_character.get('name'))
        
        if benefits.get("wisdom_insight"):
            insights = [
                "You gain clarity about your path ahead.",
                "Ancient wisdom flows through your consciousness.",
                "The interconnectedness of all things becomes clearer.",
                "You feel more attuned to the world's hidden rhythms."
            ]
            insight = random.choice(insights)
            print(f"\n{insight}")
            log_game_event("MEDITATION_INSIGHT", insight, player_character.get('name'))

def handle_healing_spring(poi, player_character, location):
    """Handle healing spring interactions"""
    print("\nThe spring's waters sparkle with healing energy. Drink? (y/n)")
    if input().lower() == 'y':
        log_game_event("HEALING_SPRING_USE", "Drinking from healing spring", player_character.get('name'))
        
        if poi.get("full_restore"):
            player_character['health'] = player_character['max_health']
            player_character['mana'] = player_character['max_mana']
            print("\nThe magical waters fully restore your health and mana!")
            log_game_event("FULL_RESTORATION", "Fully restored HP and MP", player_character.get('name'))
        
        if poi.get("blessing_chance") and random.random() < poi["blessing_chance"]:
            print("\n✨ The spring bestows a blessing upon you! ✨")
            print("You feel invigorated and protected.")
            log_game_event("SPRING_BLESSING", "Received blessing from spring", player_character.get('name'))
            # Could add temporary buffs here

def handle_shrine_interaction(poi, player_character, location):
    """Handle shrine interactions"""
    deity = poi.get("deity", "unknown")
    offerings = poi.get("offerings_accepted", [])
    
    print(f"\nThe shrine seems dedicated to {deity}.")
    
    # Check if player has acceptable offerings
    player_inv = player_character.get('inventory', [])
    available_offerings = [item for item in offerings if item in player_inv]
    
    if available_offerings:
        print("\nYou have items that could be offered:")
        for i, item_id in enumerate(available_offerings, 1):
            print(f"{i}. {items.ITEM_DB[item_id]['name']}")
        print(f"{len(available_offerings) + 1}. Offer nothing")
        
        try:
            choice = int(input("Your choice: "))
            if choice <= len(available_offerings):
                offered_item = available_offerings[choice - 1]
                player_character['inventory'].remove(offered_item)
                print(f"\nYou offer the {items.ITEM_DB[offered_item]['name']} to the shrine.")
                log_game_event("SHRINE_OFFERING", f"Offered {items.ITEM_DB[offered_item]['name']} to {deity}", player_character.get('name'))
                
                # Grant blessing or reward
                print("\nThe shrine glows with approval!")
                if random.random() < 0.7:
                    rewards = ["healing_potion_lesser", "mana_potion_minor", "blessed_water"]
                    reward = random.choice(rewards)
                    if reward in items.ITEM_DB:
                        player_character['inventory'].append(reward)
                        print(f"You receive: {items.ITEM_DB[reward]['name']}!")
                        log_game_event("SHRINE_REWARD", f"Received: {items.ITEM_DB[reward]['name']}", player_character.get('name'))
        except:
            print("You decide not to make an offering.")
            log_game_event("SHRINE_NO_OFFERING", "Chose not to offer", player_character.get('name'))
    else:
        print("You have nothing suitable to offer.")
        log_game_event("SHRINE_EMPTY_HANDED", "No suitable offerings", player_character.get('name'))

def handle_npc_creature(poi, player_character, location):
    """Handle NPC creature interactions"""
    npc_id = poi.get("npc_id")
    peaceful = poi.get("peaceful", True)
    can_speak = poi.get("can_speak", False)
    
    prompt = poi.get("interaction_prompt_to_ai")
    if prompt:
        print(handle_flexible_ai_response(prompt, player_character, location))
    
    if can_speak:
        print("\nThe creature seems willing to communicate. Approach? (y/n)")
        if input().lower() == 'y':
            log_game_event("CREATURE_APPROACH", f"Approaching {npc_id}", player_character.get('name'))
            
            if npc_id == "ancient_turtle_sage":
                turtle_wisdom = [
                    "Time flows differently for those who know patience.",
                    "The deepest waters often hold the clearest reflections.",
                    "What was lost in sand may be found in stone.",
                    "Three paths converge where shadows dance at noon."
                ]
                wisdom = random.choice(turtle_wisdom)
                print(f"\nThe ancient turtle speaks slowly: '{wisdom}'")
                log_game_event("TURTLE_WISDOM", f"Wisdom: {wisdom}", player_character.get('name'))
                
                # Small chance of gift
                if random.random() < 0.2:
                    print("\nThe turtle gifts you something from its shell.")
                    gift = random.choice(["pearl_small", "ancient_shell", "turtle_blessing"])
                    if gift in items.ITEM_DB:
                        player_character['inventory'].append(gift)
                        print(f"You receive: {items.ITEM_DB[gift]['name']}!")
                        log_game_event("TURTLE_GIFT", f"Received: {items.ITEM_DB[gift]['name']}", player_character.get('name'))

# --- Resource Gathering System ---
def handle_resource_gathering(player_character, location_data):
    """Handle resource gathering at resource nodes"""
    resource_nodes = location_data.get('resource_nodes', [])
    
    if not resource_nodes:
        print("There are no gatherable resources here.")
        log_game_event("GATHERING_NONE", "No resources available", player_character.get('name'))
        return
    
    print("\nAvailable resources:")
    for i, node in enumerate(resource_nodes, 1):
        node_def = locations.RESOURCE_NODES.get(node['type'], {}).get(node['resource'], {})
        tool_req = node_def.get('tool_required', 'none')
        print(f"{i}. {node['resource']} ({node['type']}) - Requires: {tool_req}")
    
    try:
        choice = int(input("Gather which resource? (0 to cancel): "))
        if choice == 0:
            return
            
        node = resource_nodes[choice - 1]
        node_type = node['type']
        resource = node['resource']
        node_def = locations.RESOURCE_NODES.get(node_type, {}).get(resource, {})
        
        # Check tool requirement
        tool_required = node_def.get('tool_required')
        if tool_required and tool_required not in player_character.get('inventory', []):
            print(f"You need a {tool_required} to gather this resource.")
            log_game_event("GATHERING_NO_TOOL", f"Missing tool: {tool_required}", player_character.get('name'))
            return
        
        # Gather resources
        min_yield, max_yield = node_def.get('yield', [1, 1])
        gathered = random.randint(min_yield, max_yield)
        
        print(f"\nYou successfully gather {gathered} {resource}!")
        log_game_event("RESOURCE_GATHERED", f"Gathered {gathered} {resource}", player_character.get('name'))
        
        # Add to inventory (assuming resource items exist)
        for _ in range(gathered):
            if resource in items.ITEM_DB:
                player_character['inventory'].append(resource)
        
        # Award skill XP if applicable
        skill_xp = node_def.get('skill_xp', 0)
        if skill_xp > 0:
            print(f"Gained {skill_xp} {node['skill_required']} experience!")
            log_game_event("SKILL_XP_GAINED", f"+{skill_xp} {node['skill_required']} XP", player_character.get('name'))
            
    except (ValueError, IndexError):
        print("Invalid choice.")
        log_game_event("GATHERING_INVALID", "Invalid resource choice", player_character.get('name'))

# === Game Logging System ===
def log_ai_response_full(response_obj, context, player_name=None):
    """Log full AI response details for debugging"""
    if not config.DEBUG_MODE:
        return
        
    try:
        log_game_event("AI_RESPONSE_FULL", f"Context: {context}", player_name, always_log=False)
        
        if config.AI_PROVIDER == "GEMINI":
            if hasattr(response_obj, 'candidates') and response_obj.candidates:
                for i, candidate in enumerate(response_obj.candidates):
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for j, part in enumerate(candidate.content.parts):
                            if hasattr(part, 'text'):
                                log_game_event("AI_FULL_TEXT", f"Gemini candidate {i} part {j}: {part.text}", player_name, always_log=False)
                            elif hasattr(part, 'function_call'):
                                log_game_event("AI_FULL_FUNCTION", f"Gemini candidate {i} part {j} function: {part.function_call.name} with args: {part.function_call.args}", player_name, always_log=False)
        elif config.AI_PROVIDER == "OPENAI":
            if hasattr(response_obj, 'choices') and response_obj.choices:
                for i, choice in enumerate(response_obj.choices):
                    if hasattr(choice, 'message'):
                        message = choice.message
                        if message.content:
                            log_game_event("AI_FULL_TEXT", f"OpenAI choice {i} content: {message.content}", player_name, always_log=False)
                        if message.tool_calls:
                            for j, tool_call in enumerate(message.tool_calls):
                                log_game_event("AI_FULL_FUNCTION", f"OpenAI choice {i} tool {j}: {tool_call.function.name} with args: {tool_call.function.arguments}", player_name, always_log=False)
    except Exception as e:
        log_game_event("AI_LOG_ERROR", f"Failed to log full AI response: {str(e)}", player_name, always_log=False)

def log_game_event(event_type, message, player_name=None, always_log=False):
    """Log game events to gamelog.txt when debug mode is enabled or always_log is True"""
    if not config.DEBUG_MODE and not always_log:
        return
        
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        player_info = f"[{player_name}]" if player_name else "[SYSTEM]"
        log_entry = f"{timestamp} {player_info} [{event_type}] {message}\n"
        
        # Create full path to ensure we know where the file goes
        log_path = os.path.join(os.getcwd(), "gamelog.txt")
        
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
    except Exception as e:
        print(f"Failed to write to gamelog.txt: {e}")

def log_ai_interaction(context, prompt, response_text, player_name=None):
    """Log AI interactions with full context"""
    try:
        log_game_event("AI_PROMPT", f"Context: {context} | Prompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}", player_name, always_log=True)
        log_game_event("AI_RESPONSE", f"Response: {response_text}", player_name, always_log=True)
    except Exception as e:
        log_game_event("AI_LOG_ERROR", f"Failed to log AI interaction: {str(e)}", player_name, always_log=True)

def log_player_action(action, details, player_name=None):
    """Log player actions and choices"""
    try:
        log_game_event("PLAYER_ACTION", f"{action}: {details}", player_name, always_log=True)
    except Exception as e:
        log_game_event("ACTION_LOG_ERROR", f"Failed to log player action: {str(e)}", player_name, always_log=True)

def initialize_game_log():
    """Initialize/clear the game log file"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(os.getcwd(), "gamelog.txt")
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"=== SILENT SYMPHONY GAME LOG STARTED {timestamp} ===\n")
        if config.DEBUG_MODE:
            print(f"Game log initialized at: {log_path}")
    except Exception as e:
        print(f"Failed to initialize gamelog.txt: {e}")

if __name__ == "__main__":
    game() 