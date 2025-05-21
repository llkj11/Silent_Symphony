import random
import ui
import items # Import items to access ITEM_DB for weapon stats
import character # Import character module to use gain_xp
import config # Make sure config is imported if DEBUG_MODE is used here
import entities # Import entities to access SHARED_LOOT_GROUPS
import spells # Import the spells module

# Simple Combat Function
def combat(player_character, enemy_instance):
    player_health = player_character['health']
    # Enemy stats from enemy_instance
    enemy_health = enemy_instance['health'] 
    enemy_name = enemy_instance['name']
    enemy_attack_min = enemy_instance['attack_min']
    enemy_attack_max = enemy_instance['attack_max']

    print(f"\n--- Combat Initiated! ---")
    # Description is now printed before calling combat in main.py
    # print(f"You've encountered a {enemy_name}! {enemy_instance['description']}") 

    combat_actions = ["Attack", "Cast Spell", "Use Item", "Flee"]

    while player_health > 0 and enemy_health > 0:
        print(f"\nYour Health: {player_health}/{player_character['max_health']} | {enemy_name} Health: {enemy_health}")
        
        action = ui.get_numbered_choice("Choose your action:", combat_actions)
        
        if action == 'Attack':
            base_damage = random.randint(1, 6)
            weapon_bonus = 0
            equipped_weapon_id = player_character.get('equipped_weapon')
            
            if equipped_weapon_id and equipped_weapon_id in items.ITEM_DB:
                weapon_data = items.ITEM_DB[equipped_weapon_id]
                if weapon_data.get('type') == 'weapon':
                    weapon_bonus = weapon_data.get('damage_bonus', 0)
                    print(f"You attack with your {weapon_data['name']}!")
                else: 
                    print("You attack with your bare hands.") 
            else:
                print("You attack with your bare hands.")
                
            total_damage = base_damage + weapon_bonus
            enemy_health -= total_damage
            print(f"You dealt {total_damage} damage to the {enemy_name}! Enemy health is now {enemy_health}.")
            
            if enemy_health > 0:
                enemy_raw_attack = random.randint(enemy_attack_min, enemy_attack_max)
                
                player_armor_defense = 0
                equipped_armor_id = player_character.get('equipped_armor')
                armor_name_display = ""
                if equipped_armor_id and equipped_armor_id in items.ITEM_DB:
                    armor_data = items.ITEM_DB[equipped_armor_id]
                    if armor_data.get('type') == 'armor':
                        player_armor_defense = armor_data.get('defense_bonus', 0)
                        armor_name_display = f" (defended by {armor_data['name']})"
                
                player_shield_defense = 0
                equipped_shield_id = player_character.get('equipped_shield')
                shield_name_display = ""
                if equipped_shield_id and equipped_shield_id in items.ITEM_DB:
                    shield_data = items.ITEM_DB[equipped_shield_id]
                    if shield_data.get('type') == 'shield':
                        player_shield_defense = shield_data.get('defense_bonus', 0)
                        shield_name_display = f" and {shield_data['name']}" if armor_name_display else f" (defended by {shield_data['name']})"

                total_player_defense = player_armor_defense + player_shield_defense
                defense_display = f"{armor_name_display}{shield_name_display}"

                actual_damage_taken = max(0, enemy_raw_attack - total_player_defense)
                player_health -= actual_damage_taken
                print(f"The {enemy_name} attacks you for {enemy_raw_attack} damage!{defense_display} You take {actual_damage_taken} damage. Your health is now {player_health}.")

        elif action == "Use Item":
            # Filter inventory for combat-usable items
            usable_items_in_inventory = {} # Dict to store item_id: count for display
            temp_inventory_for_display = list(player_character['inventory']) # Create a copy for iteration if removing

            for item_id in temp_inventory_for_display:
                if item_id in items.ITEM_DB:
                    item_def = items.ITEM_DB[item_id]
                    # Check for 'combat_usable' and the presence of 'effects' dictionary
                    if item_def.get('combat_usable') and isinstance(item_def.get('effects'), dict):
                        usable_items_in_inventory[item_id] = usable_items_in_inventory.get(item_id, 0) + 1
            
            if not usable_items_in_inventory:
                print("You have no items usable in combat right now.")
                # Turn is not consumed if no item could be selected/used
                continue # Skip to next player turn, back to action selection

            print("\nWhich item do you want to use?")
            item_choices_display = []
            item_ids_for_choice = [] # To map chosen number back to item_id
            
            for item_id, count in usable_items_in_inventory.items():
                item_name = items.ITEM_DB[item_id]['name']
                item_choices_display.append(f"{item_name} (x{count})")
                item_ids_for_choice.append(item_id)

            item_choices_display.append("[Cancel - Go Back]")
            chosen_item_display = ui.get_numbered_choice("Select an item:", item_choices_display)

            if chosen_item_display == "[Cancel - Go Back]":
                # Turn is not consumed if player cancels
                continue 

            # Determine the chosen item_id
            chosen_item_index = item_choices_display.index(chosen_item_display)
            chosen_item_id = item_ids_for_choice[chosen_item_index]
            item_to_use_def = items.ITEM_DB[chosen_item_id]

            # --- Step 3: Handle Item Selection and Effect Application ---
            item_effects = item_to_use_def.get('effects', {})
            effect_applied_message = f"You used {item_to_use_def['name']}."
            turn_consumed = False

            if "heal_hp" in item_effects:
                heal_amount = item_effects["heal_hp"]
                old_health = player_health
                player_health = min(player_character['max_health'], player_health + heal_amount)
                healed_for = player_health - old_health
                effect_applied_message += f" You restored {healed_for} HP."
                if player_health == old_health and old_health == player_character['max_health']:
                    effect_applied_message += " You are already at maximum health."
                print(effect_applied_message)
                turn_consumed = True
            
            # Add other effects like "restore_mana" here if needed in future
            # elif "restore_mana" in item_effects:
            #    ... similar logic for mana ...
            #    turn_consumed = True

            else: # Item had no recognized effect in combat or was purely narrative
                print(f"You use the {item_to_use_def['name']}, but it has no immediate combat effect.")
                # Decide if using an item with no recognized combat effect consumes a turn.
                # For now, let's assume it does if it was 'combat_usable'.
                turn_consumed = True 

            if turn_consumed:
                player_character['inventory'].remove(chosen_item_id) # Remove one instance
                print(f"{item_to_use_def['name']} removed from inventory.")
                
                # Enemy attacks player (as turn is consumed)
                if enemy_health > 0: 
                    enemy_raw_attack = random.randint(enemy_attack_min, enemy_attack_max)
                    player_armor_defense = 0
                    equipped_armor_id = player_character.get('equipped_armor')
                    armor_name_display = ""
                    if equipped_armor_id and equipped_armor_id in items.ITEM_DB:
                        armor_data = items.ITEM_DB[equipped_armor_id]
                        if armor_data.get('type') == 'armor':
                            player_armor_defense = armor_data.get('defense_bonus', 0)
                            armor_name_display = f" (defended by {armor_data['name']})"
                    
                    player_shield_defense = 0
                    equipped_shield_id = player_character.get('equipped_shield')
                    shield_name_display = ""
                    if equipped_shield_id and equipped_shield_id in items.ITEM_DB:
                        shield_data = items.ITEM_DB[equipped_shield_id]
                        if shield_data.get('type') == 'shield':
                            player_shield_defense = shield_data.get('defense_bonus', 0)
                            shield_name_display = f" and {shield_data['name']}" if armor_name_display else f" (defended by {shield_data['name']})"

                    total_player_defense = player_armor_defense + player_shield_defense
                    defense_display = f"{armor_name_display}{shield_name_display}"
                    actual_damage_taken = max(0, enemy_raw_attack - total_player_defense)
                    player_health -= actual_damage_taken
                    print(f"The {enemy_name} attacks you for {enemy_raw_attack} damage!{defense_display} You take {actual_damage_taken} damage. Your health is now {player_health}.")
            else: # if not turn_consumed (e.g. item had no recognized effect and we decide not to consume turn)
                pass # Or 'continue' if we want to re-prompt for action immediately

        elif action == "Cast Spell":
            known_spells = player_character.get('known_spells', [])
            if not known_spells:
                print("You don't know any spells.")
                # Turn is not consumed if no spell could be selected/used
                continue # Skip to next player turn, back to action selection

            available_spells_for_choice = []
            available_spell_ids = []

            for spell_id in known_spells:
                if spell_id in spells.SPELL_DB:
                    spell_data = spells.SPELL_DB[spell_id]
                    if player_character['mana'] >= spell_data['mana_cost']:
                        available_spells_for_choice.append(f"{spell_data['name']} (Cost: {spell_data['mana_cost']} MP)")
                        available_spell_ids.append(spell_id)
                else:
                    if config.DEBUG_MODE:
                        print(f"DEBUG: Unknown spell_id '{spell_id}' in player's known_spells.")
            
            if not available_spells_for_choice:
                print("You don't have enough mana to cast any of your known spells.")
                continue # Skip to next player turn

            available_spells_for_choice.append("[Cancel - Go Back]")
            chosen_spell_display_name = ui.get_numbered_choice("Choose a spell to cast:", available_spells_for_choice)

            if chosen_spell_display_name == "[Cancel - Go Back]":
                continue # Skip to next player turn

            chosen_spell_index = available_spells_for_choice.index(chosen_spell_display_name)
            chosen_spell_id = available_spell_ids[chosen_spell_index]
            spell_to_cast = spells.SPELL_DB[chosen_spell_id]

            player_character['mana'] -= spell_to_cast['mana_cost']
            print(f"You cast {spell_to_cast['name']}! (Mana: {player_character['mana']}/{player_character['max_mana']})")
            turn_consumed_by_spell = False

            # Apply spell effects
            if spell_to_cast['type'] == "OFFENSE" and spell_to_cast['target'] == "ENEMY":
                spell_damage = spell_to_cast.get('value', 0)
                # TODO: Consider spell accuracy, enemy resistances/vulnerabilities in the future
                enemy_health -= spell_damage
                print(f"Your {spell_to_cast['name']} hits the {enemy_name} for {spell_damage} damage! Enemy health is now {enemy_health}.")
                turn_consumed_by_spell = True
            elif spell_to_cast['type'] == "HEAL" and spell_to_cast['target'] == "SELF":
                heal_amount = spell_to_cast.get('value', 0)
                old_player_health = player_health
                player_health = min(player_character['max_health'], player_health + heal_amount)
                healed_for = player_health - old_player_health
                print(f"Your {spell_to_cast['name']} restores {healed_for} HP. Your health is now {player_health}/{player_character['max_health']}.")
                if healed_for == 0 and old_player_health == player_character['max_health']:
                    print("You are already at maximum health.")
                turn_consumed_by_spell = True
            elif spell_to_cast['type'] == "DEFENSE_BUFF" and spell_to_cast['target'] == "SELF":
                # TODO: Implement buff system (duration, stacking, display)
                # For now, let's imagine a temporary combat-only shield that absorbs some damage ONCE on next hit.
                # This is a simplification. A proper buff system is needed.
                temp_shield_value = spell_to_cast.get('value', 0)
                player_character['temporary_shield'] = player_character.get('temporary_shield', 0) + temp_shield_value
                print(f"Your {spell_to_cast['name']} grants you a temporary shield of {temp_shield_value} points (Current: {player_character['temporary_shield']}). It will absorb damage from the next hit.")
                turn_consumed_by_spell = True
            # Add other spell types (BUFF, DEBUFF, etc.) here
            else:
                print(f"The spell {spell_to_cast['name']} has an unrecognized type or target for combat right now.")
                # Decide if this consumes a turn. For now, yes, as mana was spent.
                turn_consumed_by_spell = True 

            # Enemy attacks if turn was consumed and enemy is still alive
            if turn_consumed_by_spell and enemy_health > 0:
                enemy_raw_attack = random.randint(enemy_attack_min, enemy_attack_max)
                
                # Apply temporary shield if present
                damage_after_shield = enemy_raw_attack
                if player_character.get('temporary_shield', 0) > 0:
                    absorbed_by_shield = min(player_character['temporary_shield'], enemy_raw_attack)
                    player_character['temporary_shield'] -= absorbed_by_shield
                    damage_after_shield -= absorbed_by_shield
                    print(f"Your arcane shield absorbs {absorbed_by_shield} damage!")
                    if player_character['temporary_shield'] == 0:
                        print("Your arcane shield dissipates.")
                        del player_character['temporary_shield'] # Remove if used up
                
                player_armor_defense = 0
                equipped_armor_id = player_character.get('equipped_armor')
                armor_name_display = ""
                if equipped_armor_id and equipped_armor_id in items.ITEM_DB:
                    armor_data = items.ITEM_DB[equipped_armor_id]
                    if armor_data.get('type') == 'armor':
                        player_armor_defense = armor_data.get('defense_bonus', 0)
                        armor_name_display = f" (defended by {armor_data['name']})"
                
                player_shield_defense = 0
                equipped_shield_id = player_character.get('equipped_shield')
                shield_name_display = ""
                if equipped_shield_id and equipped_shield_id in items.ITEM_DB:
                    shield_data = items.ITEM_DB[equipped_shield_id]
                    if shield_data.get('type') == 'shield':
                        player_shield_defense = shield_data.get('defense_bonus', 0)
                        shield_name_display = f" and {shield_data['name']}" if armor_name_display else f" (defended by {shield_data['name']})"

                total_player_defense = player_armor_defense + player_shield_defense
                defense_display = f"{armor_name_display}{shield_name_display}"
                actual_damage_taken = max(0, damage_after_shield - total_player_defense) # Use damage_after_shield here
                player_health -= actual_damage_taken
                print(f"The {enemy_name} attacks you for {enemy_raw_attack} damage!{defense_display} You take {actual_damage_taken} damage. Your health is now {player_health}.")

        elif action == 'Flee':
            print("You managed to flee!")
            player_character['health'] = player_health
            return "fled"
        
        if enemy_health <= 0:
            print(f"\nYou defeated the {enemy_name}!")
            player_character['health'] = player_health
            # Award XP
            xp_reward = enemy_instance.get('xp_value', 0)
            if xp_reward > 0:
                character.gain_xp(player_character, xp_reward)
            
            # --- New Loot Handling Logic ---
            dropped_items_this_combat = [] # To collect all item names dropped

            # 1. Process loot_groups
            for group_name in enemy_instance.get('loot_groups', []):
                group_table = entities.SHARED_LOOT_GROUPS.get(group_name, [])
                for loot_entry in group_table:
                    item_id = loot_entry.get("item_id")
                    chance = loot_entry.get("chance", 0)
                    if item_id and random.random() <= chance:
                        if item_id in items.ITEM_DB:
                            player_character['inventory'].append(item_id)
                            dropped_items_this_combat.append(items.ITEM_DB[item_id]['name'])
                        elif config.DEBUG_MODE:
                            print(f"DEBUG: Loot item ID '{item_id}' from group '{group_name}' not found in ITEM_DB.")
            
            # 2. Process unique_loot
            unique_loot_table = enemy_instance.get('unique_loot', [])
            for loot_entry in unique_loot_table:
                item_id = loot_entry.get("item_id")
                chance = loot_entry.get("chance", 0)
                if item_id and random.random() <= chance:
                    if item_id in items.ITEM_DB:
                        player_character['inventory'].append(item_id)
                        dropped_items_this_combat.append(items.ITEM_DB[item_id]['name'])
                    elif config.DEBUG_MODE:
                        print(f"DEBUG: Unique loot item ID '{item_id}' not found in ITEM_DB.")
            
            # 3. Process old loot_table (for backward compatibility during transition)
            # This part should eventually be removed once all enemies are updated.
            old_format_loot_table = enemy_instance.get('loot_table', [])
            if old_format_loot_table and isinstance(old_format_loot_table[0], str): # Check if it's the old list-of-strings format
                if config.DEBUG_MODE:
                    print(f"DEBUG: Enemy '{enemy_name}' is using old loot_table string format. Please update.")
                for item_id in old_format_loot_table: # Assuming 100% drop for old format as a fallback
                    if item_id in items.ITEM_DB:
                        player_character['inventory'].append(item_id)
                        dropped_items_this_combat.append(items.ITEM_DB[item_id]['name'])
                    elif config.DEBUG_MODE:
                         print(f"DEBUG: Old format loot item ID '{item_id}' not found in ITEM_DB.")
            elif old_format_loot_table and isinstance(old_format_loot_table[0], dict): # It might be already new format from a previous step
                 for loot_entry in old_format_loot_table:
                    item_id = loot_entry.get("item_id")
                    chance = loot_entry.get("chance", 0) 
                    if item_id and random.random() <= chance: 
                        if item_id in items.ITEM_DB: 
                            player_character['inventory'].append(item_id)
                            dropped_items_this_combat.append(items.ITEM_DB[item_id]['name'])
                        elif config.DEBUG_MODE:
                            print(f"DEBUG: Loot item ID '{item_id}' from loot table not found in ITEM_DB.")

            # Display dropped items
            if dropped_items_this_combat:
                print(f"The {enemy_name} dropped:")
                for item_name_dropped in dropped_items_this_combat:
                    print(f"- {item_name_dropped}")
                print("Added to your inventory.")
            else:
                print(f"The {enemy_name} dropped nothing of interest this time.")

            return "won"
        elif player_health <= 0:
            print("You have been defeated!")
            player_character['health'] = 0
            return "lost"
    return "error" # Should ideally not be reached if logic is correct 