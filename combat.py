import random
import ui
import items # Import items to access ITEM_DB for weapon stats
import character # Import character module to use gain_xp
import config # Make sure config is imported if DEBUG_MODE is used here
import entities # Import entities to access SHARED_LOOT_GROUPS

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

    combat_actions = ["Attack", "Flee"]

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