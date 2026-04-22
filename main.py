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
import effects
import world
import ai_context
import npcs
import quests

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
def get_random_enemy_for_location(location_id, specific_group=None, player=None):
    current_location_data = locations.LOCATIONS.get(location_id)
    if not current_location_data:
        return None

    encounter_group_names_for_location = current_location_data.get('encounter_groups', [])
    if not encounter_group_names_for_location:
        return None

    if specific_group and specific_group in encounter_group_names_for_location:
        chosen_group_name = specific_group
    elif specific_group:
        if config.DEBUG_MODE: print(f"DEBUG: Requested specific_group '{specific_group}' not valid for location '{location_id}'. Falling back.")
        chosen_group_name = random.choice(encounter_group_names_for_location) if encounter_group_names_for_location else None
    else:
        chosen_group_name = random.choice(encounter_group_names_for_location) if encounter_group_names_for_location else None

    if not chosen_group_name:
        return None

    encounter_list = locations.ENCOUNTER_GROUPS.get(chosen_group_name, [])
    if not encounter_list:
        return None

    # Drop already-slain unique enemies so named bosses don't respawn.
    if player is not None:
        encounter_list = [
            entry for entry in encounter_list
            if not (
                entities.ENEMY_TEMPLATES.get(entry.get("enemy_id"), {}).get("unique")
                and world.is_enemy_slain(player, entry.get("enemy_id"))
            )
        ]
        if not encounter_list:
            return None

    total_weight = sum(entry.get("weight", 0) for entry in encounter_list)
    if total_weight == 0:
        return random.choice(encounter_list).get("enemy_id") if encounter_list else None

    random_pick = random.uniform(0, total_weight)
    current_sum = 0
    for entry in encounter_list:
        current_sum += entry.get("weight", 0)
        if random_pick <= current_sum:
            return entry.get("enemy_id")
    return None

# --- AI prompt + handler helpers ---
def _prompt_with_context(player, location_id, base_prompt):
    prefix = ai_context.build_context_prefix(player, location_id, locations.LOCATIONS, items.ITEM_DB)
    return prefix + base_prompt


def _handle_offer_choice(setup_narrative, choices):
    """AI-generated branching choice. Prints setup, asks player, prints chosen outcome."""
    if setup_narrative:
        print(f"\n{setup_narrative}")
    normalized = []
    for c in choices or []:
        label = c.get("label") if hasattr(c, "get") else None
        outcome = c.get("outcome_narrative") if hasattr(c, "get") else None
        if label and outcome:
            normalized.append((label, outcome))
    if not normalized:
        print("You pause, then decide it does not matter and move on.")
        return
    labels = [label for label, _ in normalized]
    chosen_label = ui.get_numbered_choice("How do you proceed?", labels)
    outcome_text = dict(normalized)[chosen_label]
    print(f"\n{outcome_text}")


def _npc_pois_for(location_id):
    """Build ephemeral POI entries for every NPC present in the location."""
    out = []
    for npc in npcs.npcs_at(location_id):
        out.append({
            "poi_id": f"_npc_{npc['id']}",
            "type": "npc",
            "npc_id": npc["id"],
            "ephemeral": True,
            "display_text_for_player_choice": f"{npc['name']}, a {npc.get('title','stranger')}.",
        })
    return out


def _interact_with_npc(player, npc_id):
    npc = npcs.get(npc_id)
    if not npc:
        print("They look at you blankly and turn away.")
        return
    print(f"\n{npc['name']}: {npc.get('greeting','')}")
    ai_context.log_event(player, f"Met {npc['name']} at {npc.get('location','?')}.", significance="significant")

    quests.on_event(player, "npc_interacted", npc_id=npc_id)

    role = npc.get("role")
    while True:
        options = []
        if role == "merchant":
            options.append("Trade")
        elif role == "healer":
            options.append("Heal")
        options.append("Leave")
        chosen = ui.get_numbered_choice(f"What do you want to do with {npc['name']}?", options)
        if chosen == "Leave":
            print(f"\n{npc['name']}: {npc.get('farewell','...')}")
            break
        if chosen == "Trade":
            _merchant_loop(player, npc)
        elif chosen == "Heal":
            _healer_loop(player, npc)


def _healer_loop(player, npc):
    DOT_KINDS = ("poison", "bleeding", "burn")
    heal_per_hp = npc.get("heal_cost_per_hp", 1)
    cure_cost = npc.get("cure_cost", 8)
    rest_cost = npc.get("rest_cost", 15)
    while True:
        missing = player.get("max_health", 0) - player.get("health", 0)
        has_dots = any(e.get("kind") in DOT_KINDS for e in player.get("effects", []))
        full_heal_cost = missing * heal_per_hp
        print(f"\nYour gold: {player.get('gold', 0)}")
        options = []
        if missing > 0:
            options.append(f"Restore HP ({missing} HP for {full_heal_cost}g)")
        if has_dots:
            options.append(f"Cure ailments ({cure_cost}g)")
        options.append(f"Full rest — HP/mana/stamina + ailments ({rest_cost}g)")
        options.append("Back")
        chosen = ui.get_numbered_choice(f"{npc['name']} asks what you need.", options)
        if chosen == "Back":
            return
        if chosen.startswith("Restore HP"):
            if player.get("gold", 0) < full_heal_cost:
                print(f"{npc['name']}: \"I can't work miracles without coin.\"")
                continue
            player["gold"] -= full_heal_cost
            player["health"] = player["max_health"]
            print(f"{npc['name']} tends your wounds. HP restored to {player['health']}/{player['max_health']}. (Gold: {player['gold']})")
            ai_context.log_event(player, f"Healed by {npc['name']} for {full_heal_cost}g.", significance="normal")
        elif chosen.startswith("Cure ailments"):
            if player.get("gold", 0) < cure_cost:
                print(f"{npc['name']}: \"The herbs for that aren't free.\"")
                continue
            player["gold"] -= cure_cost
            cleared = [e["kind"] for e in player.get("effects", []) if e.get("kind") in DOT_KINDS]
            player["effects"] = [e for e in player.get("effects", []) if e.get("kind") not in DOT_KINDS]
            print(f"{npc['name']} presses poultices to your skin. Cleared: {', '.join(cleared) or 'nothing'}. (Gold: {player['gold']})")
            ai_context.log_event(player, f"Cured ailments by {npc['name']}.", significance="normal")
        elif chosen.startswith("Full rest"):
            if player.get("gold", 0) < rest_cost:
                print(f"{npc['name']}: \"Rest and food cost what they cost.\"")
                continue
            player["gold"] -= rest_cost
            player["health"] = player["max_health"]
            player["mana"] = player.get("max_mana", 0)
            player["stamina"] = player.get("max_stamina", 0)
            player["effects"] = [e for e in player.get("effects", []) if e.get("kind") not in DOT_KINDS]
            world.tick_turn(player, count=2)
            print(f"You rest under {npc['name']}'s watch. Fully restored. (Gold: {player['gold']})")
            ai_context.log_event(player, f"Rested under {npc['name']}'s care.", significance="normal")


def _merchant_loop(player, npc):
    while True:
        print(f"\nYour gold: {player.get('gold', 0)}")
        chosen = ui.get_numbered_choice("Trade what?", ["Buy", "Sell", "Back"])
        if chosen == "Back":
            return
        if chosen == "Buy":
            _merchant_buy(player, npc)
        elif chosen == "Sell":
            _merchant_sell(player, npc)


def _merchant_buy(player, npc):
    stock = [iid for iid in npc.get("shop_inventory", []) if iid in items.ITEM_DB]
    if not stock:
        print(f"{npc['name']} has nothing for sale.")
        return
    display = []
    for iid in stock:
        data = items.ITEM_DB[iid]
        price = npcs.buy_price(npc, data.get("value", 0))
        display.append(f"{data['name']} — {price}g ({data.get('type','item')})")
    display.append("[Back]")
    chosen = ui.get_numbered_choice("Buy which?", display)
    if chosen == "[Back]":
        return
    idx = display.index(chosen)
    item_id = stock[idx]
    data = items.ITEM_DB[item_id]
    price = npcs.buy_price(npc, data.get("value", 0))
    if player.get("gold", 0) < price:
        print(f"{npc['name']}: \"You haven't the coin for that.\"")
        return
    player["gold"] -= price
    player["inventory"].append(item_id)
    print(f"You buy {data['name']} for {price}g. (Gold left: {player['gold']})")
    ai_context.log_event(player, f"Bought {data['name']} from {npc['name']} for {price}g.", significance="normal")


def _merchant_sell(player, npc):
    inventory = player.get("inventory", [])
    sellable = [iid for iid in inventory if iid in items.ITEM_DB and items.ITEM_DB[iid].get("value", 0) > 0]
    if not sellable:
        print(f"{npc['name']}: \"Nothing you've brought interests me.\"")
        return
    seen = set()
    choices = []
    for iid in sellable:
        if iid in seen:
            continue
        seen.add(iid)
        count = sellable.count(iid)
        data = items.ITEM_DB[iid]
        price = npcs.sell_price(npc, data.get("value", 0))
        name = data["name"]
        label = f"{name} x{count}" if count > 1 else name
        choices.append((iid, f"{label} — {price}g"))
    display = [label for _, label in choices] + ["[Back]"]
    chosen = ui.get_numbered_choice("Sell which?", display)
    if chosen == "[Back]":
        return
    item_id = choices[display.index(chosen)][0]
    data = items.ITEM_DB[item_id]
    price = npcs.sell_price(npc, data.get("value", 0))
    player["inventory"].remove(item_id)
    player["gold"] = player.get("gold", 0) + price
    print(f"You sell {data['name']} for {price}g. (Gold: {player['gold']})")
    ai_context.log_event(player, f"Sold {data['name']} to {npc['name']} for {price}g.", significance="normal")


def _handle_introduce_npc(player, location_id, npc_id, disposition, narrative):
    """AI-foregrounded NPC entry. Requires the NPC to already live at this location.
    Prints the narrative, logs the moment, and offers interaction."""
    npc = npcs.get(npc_id) if npc_id else None
    if not npc or npc.get("location") != location_id:
        # AI hallucinated an NPC or called them in the wrong place — refuse quietly.
        if config.DEBUG_MODE:
            print(f"DEBUG: introduce_npc refused for id={npc_id} at location={location_id}")
        if narrative:
            # Still show the narrative — it's just flavor at that point.
            print(f"\n{narrative}")
        return
    if narrative:
        print(f"\n{narrative}")
    mood = f" ({disposition})" if disposition else ""
    ai_context.log_event(
        player,
        f"{npc['name']} stepped into the scene{mood} at {location_id}.",
        significance="normal",
    )
    prompt = f"Engage with {npc['name']}?"
    chosen = ui.get_numbered_choice(prompt, ["Yes", "Not now"])
    if chosen == "Yes":
        _interact_with_npc(player, npc_id)


def _handle_set_world_flag(player, location_id, flag_name, scope, narrative):
    """AI-initiated persistent flag. Engine records, prints the narrative, logs as significant."""
    if not flag_name:
        return
    flag_name = str(flag_name).strip()
    if scope == "location":
        world.set_flag(player, flag_name, True, scope=location_id)
        scope_label = f"@{location_id}"
    else:
        world.set_flag(player, flag_name, True)
        scope_label = "global"
    if narrative:
        print(f"\n{narrative}")
    ai_context.log_event(player, f"Flag set: {flag_name} ({scope_label}).", significance="significant")


def _build_ephemeral_poi(display_text, narrative):
    if not display_text or not narrative:
        return None
    return {
        "poi_id": f"_flavor_{random.randint(10000, 99999)}",
        "type": "simple_description",
        "ephemeral": True,
        "display_text_for_player_choice": display_text.strip(),
        "_preresolved_narrative": narrative.strip(),
    }


def _parse_flavor_poi(resp):
    """Extract an add_flavor_poi call from an AI response; return ephemeral POI dict or None."""
    try:
        if config.AI_PROVIDER == "GEMINI":
            if hasattr(resp, 'candidates') and resp.candidates and \
               hasattr(resp.candidates[0], 'content') and hasattr(resp.candidates[0].content, 'parts'):
                for part in resp.candidates[0].content.parts:
                    fc = getattr(part, 'function_call', None)
                    if fc and fc.name == "add_flavor_poi":
                        a = fc.args
                        return _build_ephemeral_poi(a.get('display_text'), a.get('outcome_narrative'))
        elif config.AI_PROVIDER == "OPENAI":
            if hasattr(resp, 'choices') and resp.choices:
                msg = resp.choices[0].message
                if getattr(msg, 'tool_calls', None):
                    for tc in msg.tool_calls:
                        if tc.function.name == "add_flavor_poi":
                            a = json.loads(tc.function.arguments)
                            return _build_ephemeral_poi(a.get('display_text'), a.get('outcome_narrative'))
    except Exception as e:
        if config.DEBUG_MODE: print(f"DEBUG: flavor POI parse error: {e}")
    return None


def _maybe_generate_flavor_poi(player, location_id, existing_pois):
    """Ask the AI to contribute one ephemeral POI if it meaningfully adds to the scene.

    Gated so we don't spam extra AI calls: always try when engine POIs are exhausted,
    otherwise a small random chance.
    """
    if not config.global_ai_client:
        return None
    n_existing = len(existing_pois)
    if n_existing >= 3:
        return None
    if n_existing > 0 and random.random() > 0.35:
        return None

    loc_data = locations.LOCATIONS.get(location_id, {})
    loc_name = loc_data.get('name', location_id)
    existing_desc = "; ".join(p.get('display_text_for_player_choice', '?') for p in existing_pois)
    if not existing_desc:
        existing_desc = "(nothing else stands out right now)"

    prompt = (
        f"The player is exploring {loc_name}. Existing points of interest: {existing_desc}. "
        "If a fresh, specific, purely-atmospheric detail would enrich this moment, call `add_flavor_poi` "
        "with one short display_text and a 1–3 sentence outcome_narrative. "
        "If nothing better fits than what's already listed, call `narrative_outcome` with text 'none'. "
        "Do not repeat existing POIs. No items, enemies, or state changes."
    )
    resp = ai_utils.get_ai_model_response(_prompt_with_context(player, location_id, prompt))
    return _parse_flavor_poi(resp)


AMBIENT_MIN_GAP = 2     # turns since last ambient before it may fire again
AMBIENT_CHANCE = 0.30


def _maybe_show_ambient(player, location_id):
    """Occasional idle-flavor snippet when the player lingers in one place.

    Ticks off the world turn counter (advanced only by time-passing actions —
    explore / move / rest) so non-time actions like 'View Stats' don't count
    toward the dwell gate. Resets on location change.
    """
    turn_now = world.turn_counter(player)
    tracker = player.setdefault("_ambient", {"loc": None, "last_fire_turn": -99})
    if tracker.get("loc") != location_id:
        tracker["loc"] = location_id
        tracker["last_fire_turn"] = turn_now
        return
    if turn_now - tracker.get("last_fire_turn", -99) < AMBIENT_MIN_GAP:
        return
    if random.random() >= AMBIENT_CHANCE:
        return
    snippet = locations.random_ambient_for(location_id)
    if not snippet:
        return
    print(f"\n{snippet}")
    tracker["last_fire_turn"] = turn_now


def _log_combat_result(player, enemy_name, result):
    if result == "won":
        ai_context.log_event(player, f"Defeated a {enemy_name}.", significance="significant")
    elif result == "fled":
        ai_context.log_event(player, f"Fled from a {enemy_name}.", significance="significant")
    elif result == "lost":
        ai_context.log_event(player, f"Was defeated by a {enemy_name}.", significance="significant")


def _handle_skill_check(difficulty, description, success_narrative, failure_narrative):
    """AI-authored gamble. Engine rolls 1d10; >= difficulty = success."""
    try:
        difficulty = int(difficulty)
    except (TypeError, ValueError):
        difficulty = 5
    difficulty = max(1, min(10, difficulty))
    roll = random.randint(1, 10)
    succeeded = roll >= difficulty
    print(f"\n[Skill check: {description or 'attempt'} — rolled {roll} vs difficulty {difficulty} → {'SUCCESS' if succeeded else 'FAILURE'}]")
    print(success_narrative if succeeded else failure_narrative)


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
        "5": "Rest",
        "6": "View Quest Log",
        "7": "Save Game",
        "8": "Quit game"
    }
    
    current_location_id = player['location']
    current_location_data = locations.LOCATIONS.get(current_location_id)

    if not current_location_data:
        print(f"ERROR: Current location ID '{current_location_id}' not found in locations.py! Exiting.")
        return

    if player.get('last_described_location') != current_location_id:
        visits_now = world.mark_visit(player, current_location_id)
        quests.on_event(player, "location_entered", location_id=current_location_id)
        prompt_key = 'description_first_visit_prompt' if visits_now <= 1 else 'description_revisit_prompt'
        description_prompt = current_location_data.get(prompt_key, f"You are at {current_location_data.get('name', current_location_id)}.")
        ai_response_obj = ai_utils.get_ai_model_response(_prompt_with_context(player, current_location_id, description_prompt))
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
        ai_context.log_event(player, f"Arrived at {current_location_data.get('name', current_location_id)}.")

    while not game_over:
        current_location_id = player['location']
        current_location_data = locations.LOCATIONS.get(current_location_id)
        if not current_location_data:
            print(f"ERROR: Location '{current_location_id}' is invalid! Resetting to start.")
            player['location'] = "beach_starting"; player['last_described_location'] = None; continue

        _maybe_show_ambient(player, current_location_id)

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
                world.tick_turn(player)

                # --- Stage 1: Select POIs from Location Definition (filter out already-resolved ones) ---
                defined_pois_for_location = current_location_data.get('defined_pois', [])
                available_pois_to_present = []
                if defined_pois_for_location:
                    active_pois = world.active_pois(player, current_location_id, defined_pois_for_location)
                    if active_pois:
                        num_pois_to_offer = min(len(active_pois), random.randint(2, 4))
                        available_pois_to_present = random.sample(active_pois, num_pois_to_offer)

                # --- Stage 1a: Optionally let the AI contribute one ephemeral flavor POI. ---
                flavor_poi = _maybe_generate_flavor_poi(player, current_location_id, available_pois_to_present)
                if flavor_poi:
                    available_pois_to_present.append(flavor_poi)

                # --- Stage 1b: Surface NPCs present in this location as always-available POIs. ---
                npc_pois = _npc_pois_for(current_location_id)
                if npc_pois:
                    available_pois_to_present = npc_pois + available_pois_to_present

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
                    elif random.random() < 0.15:
                        generic_enemy_groups = current_location_data.get('encounter_groups', ["generic_weak_creatures"])
                        if generic_enemy_groups:
                            group_to_use = random.choice(generic_enemy_groups)
                            determined_enemy_id_to_spawn = get_random_enemy_for_location(current_location_id, specific_group=group_to_use, player=player)
                            if determined_enemy_id_to_spawn:
                                expected_function_call_name = "player_encounters_enemy"
                                ai_narrative_context = f"While looking around generally in '{current_location_data.get('name')}', the player is surprised by an enemy."
                    if not determined_item_ids_to_give and not determined_enemy_id_to_spawn:
                        ai_narrative_context = f"Player {player['name']} is in '{current_location_data.get('name')}' and looks around generally, finding nothing out of the ordinary."
                        expected_function_call_name = "narrative_outcome"
                else:
                    chosen_poi_def = next((poi for poi in available_pois_to_present if poi.get('display_text_for_player_choice') == chosen_poi_display_text), None)
                    if chosen_poi_def and chosen_poi_def.get('type') == 'npc':
                        _interact_with_npc(player, chosen_poi_def['npc_id'])
                        continue
                    if chosen_poi_def and chosen_poi_def.get('ephemeral'):
                        # AI-authored flavor POI — pre-resolved narrative, no state mutation.
                        preresolved = chosen_poi_def.get('_preresolved_narrative', 'You take a closer look, but the moment passes.')
                        print(f"\n{preresolved}")
                        continue
                    if chosen_poi_def:
                        poi_type = chosen_poi_def.get('type')
                        ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai', f"The player investigates '{chosen_poi_display_text}'.")
                        poi_id = chosen_poi_def.get('poi_id')
                        if poi_type == "loot_container":
                            is_locked = chosen_poi_def.get('locked', False)
                            key_id = chosen_poi_def.get('key_id')
                            can_unlock = (not is_locked) or (key_id and key_id in player['inventory'])
                            is_trapped = random.random() < chosen_poi_def.get('trapped_chance', 0)
                            if config.DEBUG_MODE:
                                print(f"DEBUG: POI loot_container. Locked: {is_locked}, Can Unlock: {can_unlock}, Trapped Roll: {is_trapped} (Chance: {chosen_poi_def.get('trapped_chance', 0)})")

                            if is_locked and not can_unlock:
                                # Stays retryable — player may return with a key. No status mark.
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_if_locked', "It's locked.")
                                expected_function_call_name = "narrative_outcome"
                            elif is_trapped:
                                if config.DEBUG_MODE: print("DEBUG: Trap sprung on POI!")
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_if_trap_sprung', "A trap springs!")
                                determined_enemy_id_to_spawn = chosen_poi_def.get('trap_enemy_id')
                                if config.DEBUG_MODE: print(f"DEBUG: Trap enemy ID determined: {determined_enemy_id_to_spawn}")
                                expected_function_call_name = "player_encounters_enemy"
                                world.set_poi_state(player, current_location_id, poi_id, "sprung")
                                quests.on_event(player, "poi_resolved", location_id=current_location_id, poi_id=poi_id, status="sprung")
                            else:
                                if is_locked and can_unlock:
                                    ai_narrative_context = f"Using their {items.ITEM_DB.get(key_id, {}).get('name', 'key')}, "
                                else:
                                    ai_narrative_context = ""
                                ai_narrative_context += chosen_poi_def.get('interaction_prompt_to_ai_on_open', "The player opens it.")
                                determined_item_ids_to_give = process_poi_loot(chosen_poi_def.get('loot_table_ids', []))
                                if determined_item_ids_to_give:
                                    expected_function_call_name = "player_discovers_item"
                                else:
                                    ai_narrative_context += " It appears to be empty."
                                    expected_function_call_name = "narrative_outcome"
                                world.set_poi_state(player, current_location_id, poi_id, "looted")
                                quests.on_event(player, "poi_resolved", location_id=current_location_id, poi_id=poi_id, status="looted")

                        elif poi_type == "loot_scatter":
                            if random.random() < chosen_poi_def.get('success_chance', 1.0):
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_on_success', "They succeed!")
                                item_to_yield = chosen_poi_def.get('item_id_to_yield')
                                if item_to_yield: determined_item_ids_to_give.append(item_to_yield)
                                if determined_item_ids_to_give:
                                     expected_function_call_name = "player_discovers_item"
                                else:
                                     expected_function_call_name = "narrative_outcome"
                            else:
                                ai_narrative_context = chosen_poi_def.get('interaction_prompt_to_ai_on_fail', "They fail.")
                                expected_function_call_name = "narrative_outcome"
                            world.set_poi_state(player, current_location_id, poi_id, "exhausted")
                            quests.on_event(player, "poi_resolved", location_id=current_location_id, poi_id=poi_id, status="exhausted")

                        elif poi_type in ("clue_object", "simple_description", "navigation_hint"):
                            if poi_type == "navigation_hint" and config.DEBUG_MODE:
                                print(f"DEBUG: Navigation hint POI investigated, reveals: {chosen_poi_def.get('reveals_exit_to')}")
                            expected_function_call_name = "narrative_outcome"
                            status_for_type = {
                                "clue_object": "read",
                                "simple_description": "observed",
                                "navigation_hint": "revealed",
                            }[poi_type]
                            extra = {}
                            if poi_type == "navigation_hint" and chosen_poi_def.get('reveals_exit_to'):
                                extra['reveals_exit_to'] = chosen_poi_def['reveals_exit_to']
                            world.set_poi_state(player, current_location_id, poi_id, status_for_type, **extra)
                            quests.on_event(player, "poi_resolved", location_id=current_location_id, poi_id=poi_id, status=status_for_type)
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
                else: # narrative_outcome — let AI escalate to branch/roll if it makes the scene better
                    outcome_prompt = (
                        f"{ai_narrative_context} Describe this scene or outcome. Call ONE of: "
                        "'narrative_outcome' (pure description); "
                        "'offer_choice' (2–3 options with pre-authored outcomes, only if a meaningful branch naturally fits); "
                        "'skill_check' (difficulty + success/failure narratives, only if the result hinges on luck or skill); "
                        "'introduce_npc' (only if an NPC listed in the location's 'NPCs here' context would naturally step into this moment). "
                        "Prefer narrative_outcome unless branching, chance, or an NPC entrance clearly improves the moment."
                    )

                if chosen_poi_display_text != "Ignore these and look around generally":
                    chosen_poi_def_for_log = next((p for p in available_pois_to_present if p.get('display_text_for_player_choice') == chosen_poi_display_text), None)
                    if chosen_poi_def_for_log:
                        pstate = world.poi_state(player, current_location_id, chosen_poi_def_for_log.get('poi_id'))
                        if pstate and pstate.get('status'):
                            short_label = chosen_poi_display_text[:60]
                            sig = "significant" if pstate['status'] == "sprung" else "normal"
                            ai_context.log_event(player, f"Investigated '{short_label}' → {pstate['status']}.", significance=sig)

                if config.DEBUG_MODE: print(f"DEBUG (Stage 3 AI Prompt): {outcome_prompt}")
                ai_response_stage3 = ai_utils.get_ai_model_response(_prompt_with_context(player, current_location_id, outcome_prompt))
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
                                                    quests.on_event(player, "item_obtained", item_id=item_id)
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
                                            if enemy_instance:
                                                combat_result = combat.combat(player, enemy_instance)
                                                _log_combat_result(player, enemy_instance.get('name', determined_enemy_id_to_spawn), combat_result)
                                                if combat_result == "lost":
                                                    game_over = True
                                            else: print("A menacing presence fades.")
                                        else: # AI called encounter but game logic had no enemy (should be rare)
                                            if config.DEBUG_MODE: print(f"DEBUG: AI called encounter_enemy but game logic had no enemy.")
                                            print("You sense danger, but it quickly passes.")
                                        function_called_successfully = True; break
                                    
                                    elif function_call.name == "narrative_outcome":
                                        narrative = function_call.args.get('narrative_text', "You observe your surroundings quietly."); print(f"\n{narrative}");
                                        function_called_successfully = True; break

                                    elif function_call.name == "offer_choice":
                                        setup = function_call.args.get('setup_narrative', '')
                                        choices = list(function_call.args.get('choices', []) or [])
                                        _handle_offer_choice(setup, choices)
                                        function_called_successfully = True; break

                                    elif function_call.name == "skill_check":
                                        a = function_call.args
                                        _handle_skill_check(
                                            a.get('difficulty', 5),
                                            a.get('description', ''),
                                            a.get('success_narrative', ''),
                                            a.get('failure_narrative', ''),
                                        )
                                        function_called_successfully = True; break

                                    elif function_call.name == "set_world_flag":
                                        a = function_call.args
                                        _handle_set_world_flag(
                                            player, current_location_id,
                                            a.get('flag_name'),
                                            a.get('scope', 'global'),
                                            a.get('narrative', ''),
                                        )
                                        function_called_successfully = True; break

                                    elif function_call.name == "introduce_npc":
                                        a = function_call.args
                                        _handle_introduce_npc(
                                            player, current_location_id,
                                            a.get('npc_id'),
                                            a.get('disposition', ''),
                                            a.get('narrative', ''),
                                        )
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
                                            if item_id in items.ITEM_DB:
                                                player['inventory'].append(item_id)
                                                print(f"You obtained: {items.ITEM_DB[item_id]['name']}! Added to inventory.")
                                                quests.on_event(player, "item_obtained", item_id=item_id)
                                            elif config.DEBUG_MODE: print(f"DEBUG: Game logic provided unknown item_id: {item_id}")
                                    else: print("It seemed valuable, but crumbled to dust.")
                                    function_called_successfully = True; break
                                
                                elif function_name == "player_encounters_enemy":
                                    narrative = args.get('encounter_narrative', "Danger appears!")
                                    print(f"\n{narrative}")
                                    if determined_enemy_id_to_spawn:
                                        enemy_instance = entities.get_enemy_instance(determined_enemy_id_to_spawn)
                                        if enemy_instance:
                                            combat_result = combat.combat(player, enemy_instance)
                                            _log_combat_result(player, enemy_instance.get('name', determined_enemy_id_to_spawn), combat_result)
                                            if combat_result == "lost":
                                                game_over = True
                                        else: print("A menacing presence fades.")
                                    else: print("You sense danger, but it quickly passes.")
                                    function_called_successfully = True; break
                                
                                elif function_name == "narrative_outcome":
                                    narrative = args.get('narrative_text', "You observe your surroundings quietly."); print(f"\n{narrative}");
                                    function_called_successfully = True; break

                                elif function_name == "offer_choice":
                                    _handle_offer_choice(
                                        args.get('setup_narrative', ''),
                                        list(args.get('choices', []) or []),
                                    )
                                    function_called_successfully = True; break

                                elif function_name == "skill_check":
                                    _handle_skill_check(
                                        args.get('difficulty', 5),
                                        args.get('description', ''),
                                        args.get('success_narrative', ''),
                                        args.get('failure_narrative', ''),
                                    )
                                    function_called_successfully = True; break

                                elif function_name == "set_world_flag":
                                    _handle_set_world_flag(
                                        player, current_location_id,
                                        args.get('flag_name'),
                                        args.get('scope', 'global'),
                                        args.get('narrative', ''),
                                    )
                                    function_called_successfully = True; break

                                elif function_name == "introduce_npc":
                                    _handle_introduce_npc(
                                        player, current_location_id,
                                        args.get('npc_id'),
                                        args.get('disposition', ''),
                                        args.get('narrative', ''),
                                    )
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
                        world.tick_turn(player)
                        visits_now = world.mark_visit(player, new_location_id)
                        quests.on_event(player, "location_entered", location_id=new_location_id)
                        desc_prompt_key = 'description_first_visit_prompt' if visits_now <= 1 else 'description_revisit_prompt'
                        description_prompt = new_location_data.get(desc_prompt_key, f"You arrive at {new_location_data.get('name')}.")
                        print(f"\nMoving to {new_location_data.get('name')}...")
                        ai_loc_resp = ai_utils.get_ai_model_response(_prompt_with_context(player, new_location_id, description_prompt))
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
                        ai_context.log_event(player, f"Traveled to {new_location_data.get('name', new_location_id)}.")
                    else:
                        print(f"Error: Could not find data for location {new_location_id}.")
            elif selected_action == 'Manage Inventory': manage_inventory(player)
            elif selected_action == 'View character stats':
                print("\n--- Character Stats ---")
                print(f"Name: {player['name']}")
                race_trait_id = player.get('race_trait')
                race_trait_def = game_data.RACE_TRAITS.get(player['race'], {})
                race_trait_desc = race_trait_def.get('trait_description') if race_trait_id else ""
                trait_suffix = f" — {race_trait_desc}" if race_trait_desc else ""
                print(f"Race: {player['race']}{trait_suffix}")
                print(f"Origin: {player['origin']}")
                print(f"Star Sign: {player['star_sign']}")
                print(f"Health: {player['health']}/{player['max_health']}")
                print(f"Mana: {player.get('mana', 0)}/{player.get('max_mana', 0)}")
                print(f"Stamina: {player.get('stamina', 0)}/{player.get('max_stamina', 0)}")
                print(f"Level: {player['level']}")
                print(f"XP: {player['xp']}/{player['xp_to_next_level']}")
                print(f"Gold: {player.get('gold', 0)}")
                equipped_weapon_name = items.ITEM_DB[player['equipped_weapon']]['name'] if player.get('equipped_weapon') else "None"
                equipped_shield_name = items.ITEM_DB[player['equipped_shield']]['name'] if player.get('equipped_shield') else "None"
                print(f"Equipped Weapon: {equipped_weapon_name}")
                print(f"Equipped Shield: {equipped_shield_name}")
                for slot in character.ARMOR_SLOTS:
                    field = f'equipped_{slot}'
                    iid = player.get(field)
                    name = items.ITEM_DB[iid]['name'] if iid and iid in items.ITEM_DB else "None"
                    print(f"  {slot.capitalize()}: {name}")
                print(f"Total Armor: {character.armor_defense_total(player, items.ITEM_DB)} | Magic Resist: {character.magic_resistance_total(player, items.ITEM_DB)}")
                effect_summary = effects.active_effects_summary(player)
                if effect_summary:
                    print(f"Active effects: {effect_summary}")
                import abilities as _abilities
                if player.get('known_abilities'):
                    ability_names = []
                    for aid in player['known_abilities']:
                        a = _abilities.ABILITIES.get(aid)
                        if a:
                            ability_names.append(f"{a['name']} ({_abilities.format_cost(a)})")
                    if ability_names:
                        print(f"Abilities: {', '.join(ability_names)}")
            elif selected_action == 'Rest':
                is_safe = bool(current_location_data.get('safe'))
                world.tick_turn(player, count=4)
                if is_safe:
                    print("\nYou settle in and rest fully, shielded by the safety of this place.")
                    player['health'] = player['max_health']
                    player['mana'] = player.get('max_mana', 0)
                    player['stamina'] = player.get('max_stamina', 0)
                    cleared = [e['kind'] for e in player.get('effects', []) if e.get('kind') in ('poison', 'bleeding', 'burn')]
                    player['effects'] = [e for e in player.get('effects', []) if e.get('kind') not in ('poison', 'bleeding', 'burn')]
                    if cleared:
                        print(f"Your body recovers from: {', '.join(cleared)}.")
                    print(f"Fully restored: {player['health']}/{player['max_health']} HP, {player['mana']}/{player.get('max_mana',0)} Mana, {player['stamina']}/{player.get('max_stamina',0)} Stamina.")
                    ai_context.log_event(player, f"Rested safely at {current_location_data.get('name', current_location_id)}.", significance="minor")
                else:
                    print("\nYou snatch a wary rest in the open, ears keen for danger.")
                    if random.random() < 0.35:
                        enemy_id = get_random_enemy_for_location(current_location_id, player=player)
                        if enemy_id:
                            enemy_instance = entities.get_enemy_instance(enemy_id)
                            if enemy_instance:
                                print(f"\nYour rest is cut short — a {enemy_instance.get('name','creature')} is upon you!")
                                combat_result = combat.combat(player, enemy_instance)
                                _log_combat_result(player, enemy_instance.get('name', enemy_id), combat_result)
                                if combat_result == "lost":
                                    game_over = True
                                continue
                    heal_hp = max(1, player['max_health'] // 3)
                    heal_mana = max(1, player.get('max_mana', 0) // 2)
                    player['health'] = min(player['max_health'], player['health'] + heal_hp)
                    player['mana'] = min(player.get('max_mana', 0), player.get('mana', 0) + heal_mana)
                    player['stamina'] = player.get('max_stamina', 0)
                    print(f"Partial rest: HP +{heal_hp} ({player['health']}/{player['max_health']}), Mana +{heal_mana} ({player['mana']}/{player.get('max_mana',0)}), Stamina restored.")
                    ai_context.log_event(player, f"Rested uneasily in {current_location_data.get('name', current_location_id)}.", significance="minor")
            elif selected_action == 'View Quest Log':
                active = quests.active_quests(player)
                completed = quests.completed_quests(player)
                if not active and not completed:
                    print("\n(Your quest log is empty. Explore and talk to people to find purpose.)")
                else:
                    if active:
                        print("\n--- Active Quests ---")
                        for qid in active:
                            print()
                            print(quests.describe_quest(player, qid))
                    if completed:
                        print("\n--- Completed Quests ---")
                        for qid in completed:
                            print()
                            print(quests.describe_quest(player, qid))
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