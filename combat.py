import random
import ui
import items # Import items to access ITEM_DB for weapon stats
import character # Import character module to use gain_xp
from character import SKILLS_DATA, get_skill_details, is_skill_on_cooldown, set_skill_on_cooldown, decrement_skill_cooldowns # Specific imports
import config # Make sure config is imported if DEBUG_MODE is used here
import entities # Import entities to access SHARED_LOOT_GROUPS

# Simple Combat Function
def combat(player_character, enemy_instance):
    player_health = player_character['health']
    player_stunned_turns = 0
    enemy_stunned_turns = 0
    # Enemy stats from enemy_instance
    enemy_health = enemy_instance['health'] 
    enemy_name = enemy_instance['name']
    enemy_attack_min = enemy_instance['attack_min']
    enemy_attack_max = enemy_instance['attack_max']

    print(f"\n--- Combat Initiated! ---")
    # Description is now printed before calling combat in main.py
    # print(f"You've encountered a {enemy_name}! {enemy_instance['description']}") 

    combat_actions = ["Attack", "Skills", "Flee"] # Added Skills

    while player_health > 0 and enemy_health > 0:
        print(f"\nYour Health: {player_health}/{player_character['max_health']} | {enemy_name} Health: {enemy_health}")

        # Decrement player character skill cooldowns at the start of their turn options
        # This was moved here from later to ensure it happens before player chooses an action
        # and also if the player was stunned on their previous turn.
        decrement_skill_cooldowns(player_character)

        if player_stunned_turns > 0:
            print(f"You are stunned for {player_stunned_turns} more turn(s) and cannot act!")
            player_stunned_turns -= 1
            # Enemy still gets to attack
        else:
            action = ui.get_numbered_choice("Choose your action:", combat_actions)
            
            if action == 'Attack':
                base_damage = random.randint(1, 6) # Default bare-handed damage
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

            elif action == 'Skills':
                available_skills = player_character.get('available_skills', [])
                if not available_skills:
                    print("You have no skills available.")
                    continue # Go back to action choice

                skill_display_options = []
                for skill_id in available_skills:
                    skill_info = get_skill_details(skill_id)
                    if skill_info:
                        status = " (Ready)" if not is_skill_on_cooldown(player_character, skill_id) else f" (On Cooldown: {player_character['skill_cooldowns'].get(skill_id, 0)} turns)"
                        skill_display_options.append(f"{skill_info['name']}{status} - {skill_info['description']}")
                
                skill_display_options.append("Back")
                chosen_skill_display = ui.get_generic_choice("Choose a skill:", skill_display_options, show_numbers=True)

                if chosen_skill_display == "Back":
                    continue # Go back to main action choice

                # Determine which skill_id was chosen based on display name
                chosen_skill_id = None
                for skill_id in available_skills:
                    skill_info = get_skill_details(skill_id)
                    if skill_info and chosen_skill_display.startswith(skill_info['name']):
                        chosen_skill_id = skill_id
                        break
                
                if not chosen_skill_id:
                    print("Invalid skill choice.")
                    continue

                skill_details = get_skill_details(chosen_skill_id)

                if is_skill_on_cooldown(player_character, chosen_skill_id):
                    print(f"{skill_details['name']} is on cooldown!")
                    continue

                # Skill-specific requirements
                if chosen_skill_id == 'shield_bash':
                    equipped_shield_id = player_character.get('equipped_shield') # Corrected line
                    shield_item_details = items.ITEM_DB.get(equipped_shield_id) if equipped_shield_id else None
                    if not shield_item_details or shield_item_details.get('type') != 'shield':
                        print("You need a shield equipped to use Shield Bash.")
                        continue
                
                # --- Skill Execution ---
                base_damage = random.randint(1, 6) # Default bare-handed
                weapon_bonus = 0
                equipped_weapon_id = player_character.get('equipped_weapon')
                if equipped_weapon_id and equipped_weapon_id in items.ITEM_DB:
                    weapon_data = items.ITEM_DB[equipped_weapon_id]
                    if weapon_data.get('type') == 'weapon':
                        weapon_bonus = weapon_data.get('damage_bonus', 0)

                player_attack_power = base_damage + weapon_bonus
                
                damage_dealt_by_skill = 0

                if chosen_skill_id == 'power_attack':
                    damage_dealt_by_skill = int(player_attack_power * skill_details['damage_multiplier'])
                    enemy_health -= damage_dealt_by_skill
                    print(f"You use {skill_details['name']}! You dealt {damage_dealt_by_skill} damage to the {enemy_name}.")
                    set_skill_on_cooldown(player_character, chosen_skill_id)

                elif chosen_skill_id == 'shield_bash':
                    # Shield Bash might use a different base, e.g., shield's own damage or fixed, but for now, use player_attack_power
                    damage_dealt_by_skill = int(player_attack_power * skill_details['damage_multiplier'])
                    enemy_health -= damage_dealt_by_skill
                    print(f"You use {skill_details['name']}! You dealt {damage_dealt_by_skill} damage to the {enemy_name}.")
                    
                    if 'effect' in skill_details and skill_details['effect']['type'] == 'stun':
                        if random.random() < skill_details['effect']['chance']:
                            enemy_stunned_turns = skill_details['effect']['duration']
                            print(f"The {enemy_name} is stunned for {enemy_stunned_turns} turn(s)!")
                    set_skill_on_cooldown(player_character, chosen_skill_id)
                
                # After skill use, enemy health is updated
                print(f"Enemy health is now {enemy_health}.")


            elif action == 'Flee':
                print("You managed to flee!")
                player_character['health'] = player_health # Save current health before exiting
                return "fled"
        
        # --- Enemy's Turn ---
        if enemy_health > 0:
            special_ability_used_this_turn = False
            if enemy_stunned_turns > 0:
                print(f"The {enemy_name} is stunned and cannot attack!")
                enemy_stunned_turns -= 1
            else:
                # Check for special abilities
                if 'special_abilities' in enemy_instance and enemy_instance['special_abilities']:
                    for ability in enemy_instance['special_abilities']:
                        if ability.get('current_cooldown', 0) <= 0 and random.random() <= ability.get('chance', 0):
                            print(f"\nThe {enemy_name} uses {ability['name']}!")
                            if 'description' in ability:
                                print(ability['description'])
                            
                            base_enemy_attack = random.randint(enemy_attack_min, enemy_attack_max)
                            modified_damage = int(base_enemy_attack * ability.get('damage_multiplier', 1.0))

                            # Handle effects like stun
                            if 'effect' in ability:
                                effect = ability['effect']
                                if effect.get('type') == 'stun' and random.random() <= effect.get('chance', 0):
                                    player_stunned_turns = effect.get('duration', 1)
                                    print(f"You have been stunned by {ability['name']} for {player_stunned_turns} turn(s)!")

                            # Apply damage to player (similar to regular attack)
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
                            actual_damage_taken = max(0, modified_damage - total_player_defense)
                            player_health -= actual_damage_taken
                            print(f"The {enemy_name}'s {ability['name']} deals {modified_damage} damage!{defense_display} You take {actual_damage_taken} damage. Your health is now {player_health}.")
                            
                            ability['current_cooldown'] = ability['cooldown']
                            special_ability_used_this_turn = True
                            break # Enemy uses one special ability per turn
                
                if not special_ability_used_this_turn:
                    # Regular enemy attack
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
            
            # Decrement enemy ability cooldowns
            if 'special_abilities' in enemy_instance and enemy_instance['special_abilities']:
                for ability in enemy_instance['special_abilities']:
                    if ability.get('current_cooldown', 0) > 0:
                        ability['current_cooldown'] -= 1
                        
        # --- Check for combat end conditions ---
        if enemy_health <= 0:
            print(f"\nYou defeated the {enemy_name}!")
            player_character['health'] = player_health # Save final health
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