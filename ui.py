import curses # Import the curses library
import textwrap

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

# New helper function for curses-based menu selection
def display_curses_menu(stdscr, title, options_list):
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(0)   # Make getch() blocking
    stdscr.timeout(-1)  # Wait indefinitely for input

    current_row_idx = 0
    max_rows, max_cols = stdscr.getmaxyx()

    # Basic color setup (can be expanded)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) # Highlighted item
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK) # Normal item

    while True:
        stdscr.clear()
        
        # Display title
        title_y = 1
        title_x = max(1, (max_cols - len(title)) // 2)
        stdscr.addstr(title_y, title_x, title, curses.A_BOLD)

        # Display options
        # Calculate start_y to roughly center the menu items if there are few
        menu_height = len(options_list)
        start_y = max(title_y + 2, (max_rows - menu_height) // 2)

        for i, option in enumerate(options_list):
            x = max(2, (max_cols - len(option)) // 2)
            y = start_y + i

            if y >= max_rows -1 : # Ensure it doesn't write off screen
                break 

            if i == current_row_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.color_pair(2))
        
        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP:
            current_row_idx = (current_row_idx - 1) % len(options_list)
        elif key == curses.KEY_DOWN:
            current_row_idx = (current_row_idx + 1) % len(options_list)
        elif key == curses.KEY_ENTER or key in [10, 13]:
            stdscr.clear() # Clear before returning to avoid leftover text
            return options_list[current_row_idx]
        elif key == 27: # ESC key to go back/cancel (convention)
            stdscr.clear()
            return None # Or a specific value like "[BACK]" if defined in options 

# New 3-Pane Curses Inventory UI
def display_curses_inventory(stdscr, player, items_module, config_module):
    curses.curs_set(0)
    stdscr.nodelay(0)
    stdscr.timeout(-1)

    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlighted
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Info Text / Titles
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Category Title

    # Updated categories based on user request
    categories = ["All Items", "Weapons", "Armor", "Shields", "Consumables", "Scrolls", "Junk"]
    category_to_type = {
        "Weapons": ["weapon"],
        "Armor": ["armor"], # Body armor, helmets, gloves, boots etc.
        "Shields": ["shield"],
        "Consumables": ["consumable"], # Potions, food etc.
        "Scrolls": ["scroll"], # Magical scrolls
        "Junk": ["junk", "valuable", "trade_good", "crafting_material", "alchemy_ingredient", "reagent", "tool", "quest_item", "book", "trinket"]
        # "All Items" is special case
        # Other item types like valuable, tool, quest_item, book, trinket will now fall into "Junk" 
        # or a new more generic "Miscellaneous" category could be made if preferred.
        # For now, per user request, only the specified categories are distinct. Other specific types are grouped into Junk for browsing.
    }

    active_pane = "categories" 
    current_category_idx = 0
    current_item_idx = 0
    
    cat_pane_w_pct = 0.20
    item_pane_w_pct = 0.35 # Slightly wider for potentially longer item names + markers

    while True:
        stdscr.clear()
        max_rows, max_cols = stdscr.getmaxyx()

        cat_pane_width = int(max_cols * cat_pane_w_pct)
        item_pane_width = int(max_cols * item_pane_w_pct)
        info_pane_start_x = cat_pane_width + item_pane_width + 2 
        info_pane_width = max_cols - info_pane_start_x -1

        # --- 1. Draw Category Pane (Left) ---
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 1, "Categories".center(cat_pane_width - 2))
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        for i, cat_name in enumerate(categories):
            style = curses.color_pair(1) if i == current_category_idx and active_pane == "categories" else curses.color_pair(2)
            stdscr.addstr(3 + i, 1, cat_name.ljust(cat_pane_width - 2)[:cat_pane_width-2], style)

        # --- 2. Filter and Draw Item List Pane (Middle) ---
        selected_category_name = categories[current_category_idx]
        filtered_inventory_ids = []
        if selected_category_name == "All Items":
            filtered_inventory_ids = list(player['inventory'])
        else:
            target_types = category_to_type.get(selected_category_name, [])
            for item_id in player['inventory']:
                item_data = items_module.ITEM_DB.get(item_id, {})
                if item_data.get('type') in target_types:
                    filtered_inventory_ids.append(item_id)
        
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, cat_pane_width + 1, selected_category_name.center(item_pane_width -2))
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)

        if not player['inventory']:
             stdscr.addstr(3, cat_pane_width + 1, "Inventory is empty.")
        elif not filtered_inventory_ids:
            stdscr.addstr(3, cat_pane_width + 1, f"No items in '{selected_category_name}'.")
        else:
            for i, item_id in enumerate(filtered_inventory_ids):
                item_data = items_module.ITEM_DB.get(item_id, {})
                item_name = item_data.get("name", "Unknown")
                marker = ""
                if player.get('equipped_weapon') == item_id: marker = " (W)"
                elif player.get('equipped_armor') == item_id: marker = " (A)"
                elif player.get('equipped_shield') == item_id: marker = " (S)" # Shield marker
                display_name = f"{item_name}{marker}"[:item_pane_width-2]
                style = curses.color_pair(1) if i == current_item_idx and active_pane == "items" else curses.color_pair(2)
                stdscr.addstr(3 + i, cat_pane_width + 1, display_name.ljust(item_pane_width -2), style)
                if 3 + i >= max_rows - 4: break

        # --- 3. Draw Item Info Pane (Right) ---
        highlighted_item_id_from_list = None
        if active_pane == "items" and filtered_inventory_ids and 0 <= current_item_idx < len(filtered_inventory_ids):
            highlighted_item_id_from_list = filtered_inventory_ids[current_item_idx]
        
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        info_title = "--- Item Details ---" 
        if highlighted_item_id_from_list:
            info_title = f"--- {items_module.ITEM_DB.get(highlighted_item_id_from_list, {}).get('name', 'Details')} ---"
        stdscr.addstr(1, info_pane_start_x, info_title.center(info_pane_width-1))
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        if highlighted_item_id_from_list:
            item_data = items_module.ITEM_DB.get(highlighted_item_id_from_list, {})
            pane_y = 3
            desc_lines = textwrap.wrap(item_data.get('description', 'N/A'), info_pane_width - 2)
            for line in desc_lines:
                if pane_y >= max_rows - 6: break
                stdscr.addstr(pane_y, info_pane_start_x, line); pane_y += 1
            pane_y += 1
            props = [
                f"Type: {item_data.get('type', 'N/A')}",
                f"Value: {item_data.get('value', 0)}"
            ]
            if item_data.get('type') == 'weapon': props.append(f"Damage: +{item_data.get('damage_bonus', 0)}")
            # Armor and Shields both provide defense bonus
            if item_data.get('type') == 'armor' or item_data.get('type') == 'shield': 
                props.append(f"Defense: +{item_data.get('defense_bonus', 0)}")
            if item_data.get('effect', {}).get('heal'): props.append(f"Heals: {item_data['effect']['heal']}")
            if item_data.get('effect', {}).get('cast_spell'): props.append(f"Spell: {item_data['effect']['cast_spell']}")
            
            for prop_line in props:
                if pane_y >= max_rows - 4: break
                stdscr.addstr(pane_y, info_pane_start_x, prop_line); pane_y += 1
        
        # --- 4. Draw Action Hints ---
        hints_y = max_rows - 2
        hints = "[ESC] Exit | [Arrows] Navigate Panes/Items"
        if active_pane == "items" and highlighted_item_id_from_list:
            item_type = items_module.ITEM_DB.get(highlighted_item_id_from_list, {}).get('type')
            if item_type == 'consumable' or item_type == 'scroll': 
                hints += " | [U] Use"
            elif item_type in ['weapon', 'armor', 'shield']: 
                hints += " | [E] Equip/Unequip"
        stdscr.addstr(hints_y, 1, hints.ljust(max_cols -2))

        stdscr.refresh()
        key = stdscr.getch()
        action_performed_message = None

        # --- 5. Handle Input ---
        if active_pane == "categories":
            if key == curses.KEY_UP:
                current_category_idx = (current_category_idx - 1) % len(categories)
                current_item_idx = 0 
            elif key == curses.KEY_DOWN:
                current_category_idx = (current_category_idx + 1) % len(categories)
                current_item_idx = 0 
            elif key == curses.KEY_RIGHT or key == curses.KEY_ENTER or key in [10, 13]:
                if player['inventory']: active_pane = "items"
                current_item_idx = 0 
            elif key == 27: 
                return
        elif active_pane == "items":
            if key == curses.KEY_UP:
                if filtered_inventory_ids: current_item_idx = (current_item_idx - 1) % len(filtered_inventory_ids)
            elif key == curses.KEY_DOWN:
                if filtered_inventory_ids: current_item_idx = (current_item_idx + 1) % len(filtered_inventory_ids)
            elif key == curses.KEY_LEFT:
                active_pane = "categories"
            elif key == 27: 
                 active_pane = "categories"
            elif (key == ord('u') or key == ord('U')) and highlighted_item_id_from_list:
                item_data = items_module.ITEM_DB.get(highlighted_item_id_from_list)
                item_type = item_data.get('type')
                if item_type == 'consumable' or item_type == 'scroll':
                    # Basic use logic for consumables and scrolls
                    # For scrolls, actual spell casting logic would be more complex
                    # For now, just acknowledge use and remove if it's a one-time use item
                    action_performed_message = f"Used {item_data['name']}."
                    if item_data.get('effect',{}).get('heal'): # Example: simple heal effect
                         player['health'] = min(player['max_health'], player['health'] + item_data['effect']['heal'])
                         action_performed_message += f" Healed {item_data['effect']['heal']} HP."
                    
                    # Assume scrolls are consumed on use for now
                    if item_type == 'scroll' or item_data.get("type") == "consumable": 
                        player['inventory'].remove(highlighted_item_id_from_list)
                        current_item_idx = max(0, current_item_idx -1) if len(filtered_inventory_ids) == 1 else current_item_idx
                        if not player['inventory']: active_pane = "categories"
                else: action_performed_message = "Cannot use this item type."
            elif (key == ord('e') or key == ord('E')) and highlighted_item_id_from_list:
                item_data = items_module.ITEM_DB.get(highlighted_item_id_from_list)
                item_type = item_data.get('type')
                equip_message_parts = []
                if item_type == 'weapon':
                    if player['equipped_weapon'] == highlighted_item_id_from_list: 
                        player['equipped_weapon'] = None; equip_message_parts.append(f"Unequipped {item_data['name']}.")
                    else: 
                        if player['equipped_weapon']: equip_message_parts.append(f"Unequipped {items_module.ITEM_DB[player['equipped_weapon']]['name']}.")
                        player['equipped_weapon'] = highlighted_item_id_from_list; equip_message_parts.append(f"Equipped {item_data['name']}.")
                elif item_type == 'armor':
                    if player['equipped_armor'] == highlighted_item_id_from_list: 
                        player['equipped_armor'] = None; equip_message_parts.append(f"Unequipped {item_data['name']}.")
                    else: 
                        if player['equipped_armor']: equip_message_parts.append(f"Unequipped {items_module.ITEM_DB[player['equipped_armor']]['name']}.")
                        player['equipped_armor'] = highlighted_item_id_from_list; equip_message_parts.append(f"Equipped {item_data['name']}.")
                elif item_type == 'shield':
                    if player['equipped_shield'] == highlighted_item_id_from_list: 
                        player['equipped_shield'] = None; equip_message_parts.append(f"Unequipped {item_data['name']}.")
                    else: 
                        if player['equipped_shield']: equip_message_parts.append(f"Unequipped {items_module.ITEM_DB[player['equipped_shield']]['name']}.")
                        player['equipped_shield'] = highlighted_item_id_from_list; equip_message_parts.append(f"Equipped {item_data['name']}.")
                else: equip_message_parts.append("Cannot equip this item type.")
                action_performed_message = " ".join(equip_message_parts)

        if action_performed_message:
            stdscr.clear() 
            stdscr.addstr(max_rows // 2, (max_cols - len(action_performed_message)) // 2 if max_cols > len(action_performed_message) else 1, action_performed_message)
            stdscr.addstr(max_rows // 2 + 1, (max_cols - 28) // 2 if max_cols > 28 else 1, "Press any key to continue...")
            stdscr.refresh()
            stdscr.getch()
            if not player['inventory']:
                active_pane = "categories" 
                current_item_idx = 0 