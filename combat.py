import random
import ui
import items # Import items to access ITEM_DB for weapon stats
import character # Import character module to use gain_xp
import config # Make sure config is imported if DEBUG_MODE is used here

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
                player_defense = 0
                equipped_armor_id = player_character.get('equipped_armor')
                armor_name_display = ""

                if equipped_armor_id and equipped_armor_id in items.ITEM_DB:
                    armor_data = items.ITEM_DB[equipped_armor_id]
                    if armor_data.get('type') == 'armor':
                        player_defense = armor_data.get('defense_bonus', 0)
                        armor_name_display = f" (defended by {armor_data['name']})"
                
                actual_damage_taken = max(0, enemy_raw_attack - player_defense) # Ensure damage isn't negative
                player_health -= actual_damage_taken
                print(f"The {enemy_name} attacks you for {enemy_raw_attack} damage!{armor_name_display} You take {actual_damage_taken} damage. Your health is now {player_health}.")
        elif action == 'Flee':
            print("You managed to flee!")
            player_character['health'] = player_health
            return "fled"
        
        if enemy_health <= 0:
            print(f"You defeated the {enemy_name}!")
            player_character['health'] = player_health
            # Award XP
            xp_reward = enemy_instance.get('xp_value', 0)
            if xp_reward > 0:
                character.gain_xp(player_character, xp_reward)
            
            # Handle Loot Drops
            loot_table = enemy_instance.get('loot_table', [])
            dropped_items_count = 0
            if loot_table:
                print(f"The {enemy_name} dropped:")
                for loot_entry in loot_table:
                    item_id = loot_entry.get("item_id")
                    chance = loot_entry.get("chance", 0) # Default to 0 chance if not specified
                    
                    if random.random() <= chance: # random.random() is 0.0 to <1.0
                        if item_id in items.ITEM_DB: # Check if item exists
                            player_character['inventory'].append(item_id)
                            print(f"- {items.ITEM_DB[item_id]['name']}")
                            dropped_items_count += 1
                        else:
                            # It's good practice to check if config is available
                            # For simplicity, assuming config.DEBUG_MODE is accessible if config is imported.
                            if 'config' in globals() and config.DEBUG_MODE:
                                print(f"DEBUG: Loot item ID '{item_id}' from loot table not found in ITEM_DB.")
            
            if dropped_items_count > 0:
                print("Added to your inventory.")
            else:
                print(f"The {enemy_name} dropped nothing of interest this time.")

            return "won"
        elif player_health <= 0:
            print("You have been defeated!")
            player_character['health'] = 0
            return "lost"
    return "error" # Should ideally not be reached if logic is correct 