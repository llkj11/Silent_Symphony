import random
import ui
import items # Import items to access ITEM_DB for weapon stats
import character # Import character module to use gain_xp
import config # Make sure config is imported if DEBUG_MODE is used here
import entities # Import entities to access SHARED_LOOT_GROUPS
import spells # Import the spells module

# Combat status effects
class StatusEffect:
    def __init__(self, name, duration, effect_type, value=0, description=""):
        self.name = name
        self.duration = duration  # turns remaining
        self.effect_type = effect_type  # 'damage_over_time', 'buff_attack', 'debuff_defense', etc.
        self.value = value
        self.description = description
    
    def apply_effect(self, target):
        """Apply the status effect to the target"""
        if self.effect_type == 'damage_over_time':
            target['health'] = max(0, target['health'] - self.value)
            return f"{target.get('name', 'Target')} takes {self.value} damage from {self.name}!"
        elif self.effect_type == 'heal_over_time':
            old_health = target['health']
            target['health'] = min(target.get('max_health', target['health']), target['health'] + self.value)
            healed = target['health'] - old_health
            return f"{target.get('name', 'Target')} heals {healed} HP from {self.name}!"
        # Buff/debuff effects don't apply damage directly, but modify stats during combat
        # They're handled when calculating attack/defense values
        return ""
    
    def tick(self):
        """Reduce duration by 1 turn"""
        self.duration -= 1
        return self.duration > 0

# Enhanced combat function with status effects and tactical options
def combat(player_character, enemy_instance):
    player_health = player_character['health']
    # Enemy stats from enemy_instance
    enemy_health = enemy_instance['health'] 
    enemy_name = enemy_instance['name']
    enemy_attack_min = enemy_instance['attack_min']
    enemy_attack_max = enemy_instance['attack_max']
    
    # Initialize status effects tracking
    player_status_effects = []
    enemy_status_effects = []
    
    # Combat momentum system
    player_momentum = 0  # Build up for special attacks
    enemy_momentum = 0
    
    # Combat stance system
    player_stance = "balanced"  # balanced, aggressive, defensive
    stance_bonuses = {
        "balanced": {"attack": 0, "defense": 0, "crit_chance": 0},
        "aggressive": {"attack": 2, "defense": -1, "crit_chance": 0.1},
        "defensive": {"attack": -1, "defense": 2, "crit_chance": 0}
    }

    print(f"\n--- Combat Initiated! ---")
    print(f"You face {enemy_name}! Prepare for battle!")

    while player_health > 0 and enemy_health > 0:
        # Process status effects at start of turn
        if player_status_effects:
            print(f"\n--- Status Effects ---")
            for effect in player_status_effects[:]:  # Use slice to avoid modification during iteration
                message = effect.apply_effect(player_character)
                if message:
                    print(message)
                if not effect.tick():
                    player_status_effects.remove(effect)
                    print(f"{effect.name} effect on you has worn off.")
        
        if enemy_status_effects:
            for effect in enemy_status_effects[:]:
                message = effect.apply_effect(enemy_instance)
                if message:
                    print(message)
                if not effect.tick():
                    enemy_status_effects.remove(effect)
                    print(f"{effect.name} effect on {enemy_name} has worn off.")
        
        # Update health from status effects
        player_health = player_character['health']
        enemy_health = enemy_instance['health']
        
        # Display combat status
        status_display = f"\nYour Health: {player_health}/{player_character['max_health']} | {enemy_name} Health: {enemy_health}"
        if player_momentum > 0:
            status_display += f" | Momentum: {player_momentum}"
        if player_stance != "balanced":
            status_display += f" | Stance: {player_stance.title()}"
        if player_status_effects:
            effects_str = ", ".join([f"{e.name}({e.duration})" for e in player_status_effects])
            status_display += f" | Effects: {effects_str}"
        print(status_display)
        
        # Organized combat menu
        print(f"\n--- Combat Actions ---")
        action_categories = {
            "Melee": ["Attack", "Power Attack"],
            "Magic": ["Cast Spell", "Analyze Enemy"], 
            "Items": ["Use Item"],
            "Tactics": ["Change Stance", "Flee"]
        }
        
        # Display categorized actions
        action_number = 1
        action_map = {}
        
        for category, actions in action_categories.items():
            print(f"\n{category}:")
            for action in actions:
                # Add special indicators for certain actions
                display_text = action
                if action == "Power Attack" and player_momentum < 3:
                    display_text += f" (Need 3 momentum, have {player_momentum})"
                elif action == "Cast Spell":
                    spell_count = len(player_character.get('known_spells', []))
                    available_spells = sum(1 for spell_id in player_character.get('known_spells', []) 
                                         if spell_id in spells.SPELL_DB and 
                                         player_character['mana'] >= max(1, spells.SPELL_DB[spell_id]['mana_cost'] - player_character.get('magic_efficiency', 0)))
                    display_text += f" ({available_spells}/{spell_count} available)"
                elif action == "Use Item":
                    usable_count = sum(1 for item_id in player_character['inventory'] 
                                     if item_id in items.ITEM_DB and 
                                     items.ITEM_DB[item_id].get('combat_usable') and 
                                     isinstance(items.ITEM_DB[item_id].get('effects'), dict))
                    display_text += f" ({usable_count} usable)"
                
                print(f"  {action_number}. {display_text}")
                action_map[str(action_number)] = action
                action_number += 1
        
        choice = input("\nChoose your action: ").strip()
        
        if choice not in action_map:
            print("Invalid choice. Please try again.")
            continue
            
        action = action_map[choice]
        
        if action == 'Attack':
            # Calculate base damage
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
                
            # Apply stance bonuses
            stance_bonus = stance_bonuses[player_stance]["attack"]
            
            # Apply status effect bonuses
            status_attack_bonus = 0
            for effect in player_status_effects:
                if effect.effect_type == "buff_attack":
                    status_attack_bonus += effect.value
            
            total_damage = base_damage + weapon_bonus + stance_bonus + status_attack_bonus
            
            # Critical hit chance (base 5% + stance bonus + momentum + battle fury bonus + combat training)
            crit_chance = 0.05 + stance_bonuses[player_stance]["crit_chance"] + (player_momentum * 0.02)
            
            # Combat training bonus
            crit_chance += player_character.get('combat_training', 0) * 0.01  # 1% per level
            
            # Battle fury adds extra crit chance
            for effect in player_status_effects:
                if effect.name == "Battle Fury":
                    crit_chance += 0.15  # Extra 15% crit chance
            
            is_critical = random.random() < crit_chance
            
            if is_critical:
                total_damage = int(total_damage * 1.5)  # 50% more damage
                print(f"CRITICAL HIT! You deal {total_damage} damage to the {enemy_name}!")
                player_momentum += 2  # Build momentum on crits
            else:
                print(f"You deal {total_damage} damage to the {enemy_name}!")
                player_momentum += 1  # Build momentum gradually
            
            enemy_health -= total_damage
            enemy_instance['health'] = enemy_health
            
            # Some weapons have special effects
            if equipped_weapon_id and equipped_weapon_id in items.ITEM_DB:
                weapon_data = items.ITEM_DB[equipped_weapon_id]
                if weapon_data.get('name') == 'Steel Dagger' and is_critical:
                    # Chance to apply bleeding
                    if random.random() < 0.3:
                        bleeding = StatusEffect("Bleeding", 3, "damage_over_time", 2, "Losing blood")
                        enemy_status_effects.append(bleeding)
                        print(f"Your dagger causes {enemy_name} to bleed!")
        
        elif action == 'Power Attack':
            if player_momentum < 3:
                print(f"You need at least 3 momentum to use a power attack (you have {player_momentum}).")
                continue
            
            # Powerful attack that costs momentum
            base_damage = random.randint(3, 10)  # Higher base damage
            weapon_bonus = 0
            equipped_weapon_id = player_character.get('equipped_weapon')
            
            if equipped_weapon_id and equipped_weapon_id in items.ITEM_DB:
                weapon_data = items.ITEM_DB[equipped_weapon_id]
                if weapon_data.get('type') == 'weapon':
                    weapon_bonus = weapon_data.get('damage_bonus', 0)
                    print(f"You unleash a devastating blow with your {weapon_data['name']}!")
                else: 
                    print("You unleash a devastating punch!") 
            else:
                print("You unleash a devastating punch!")
            
            total_damage = base_damage + weapon_bonus + 3  # Power attack bonus
            
            # Always critical, but uses momentum
            total_damage = int(total_damage * 1.5)
            print(f"POWER ATTACK! You deal {total_damage} damage to the {enemy_name}!")
            
            enemy_health -= total_damage
            enemy_instance['health'] = enemy_health
            player_momentum = max(0, player_momentum - 3)  # Spend momentum
        
        elif action == 'Change Stance':
            stance_options = ["Balanced", "Aggressive (+2 ATK, -1 DEF, +10% crit)", "Defensive (-1 ATK, +2 DEF)"]
            chosen_stance = ui.get_numbered_choice("Choose your combat stance:", stance_options)
            
            if chosen_stance == "Balanced":
                player_stance = "balanced"
            elif chosen_stance.startswith("Aggressive"):
                player_stance = "aggressive"
            elif chosen_stance.startswith("Defensive"):
                player_stance = "defensive"
            
            print(f"You shift into a {player_stance} stance!")
            continue  # Changing stance doesn't consume a turn
        
        elif action == 'Analyze Enemy':
            print(f"\n--- {enemy_name} Analysis ---")
            print(f"Health: {enemy_health} (estimated)")
            print(f"Attack Power: {enemy_attack_min}-{enemy_attack_max}")
            
            # Reveal special abilities or weaknesses
            special_attack = enemy_instance.get('special_attack')
            if special_attack:
                print(f"Special Ability: {special_attack}")
            
            if enemy_status_effects:
                effects_str = ", ".join([f"{e.name}({e.duration})" for e in enemy_status_effects])
                print(f"Status Effects: {effects_str}")
            else:
                print("No status effects detected.")
            
            # Analyzing doesn't consume a turn but gives strategic info
            continue

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
            
            elif "restore_mana" in item_effects:
                mana_amount = item_effects["restore_mana"]
                old_mana = player_character['mana']
                player_character['mana'] = min(player_character['max_mana'], player_character['mana'] + mana_amount)
                restored_mana = player_character['mana'] - old_mana
                effect_applied_message += f" You restored {restored_mana} MP."
                if restored_mana == 0 and old_mana == player_character['max_mana']:
                    effect_applied_message += " Your mana is already at maximum."
                print(effect_applied_message)
                turn_consumed = True
                
            elif "damage" in item_effects:
                # Explosive/damaging items
                damage = item_effects["damage"]
                ignore_armor = item_effects.get("ignore_armor", False)
                
                if ignore_armor:
                    print(f"Your {item_to_use_def['name']} explodes, dealing {damage} armor-piercing damage to the {enemy_name}!")
                else:
                    print(f"Your {item_to_use_def['name']} deals {damage} damage to the {enemy_name}!")
                
                enemy_health -= damage
                enemy_instance['health'] = enemy_health
                turn_consumed = True
                
            elif "escape_chance" in item_effects:
                # Smoke bomb or similar escape items
                escape_chance = item_effects["escape_chance"]
                if random.random() < escape_chance:
                    print(f"Your {item_to_use_def['name']} creates a concealing cloud! You successfully escape!")
                    player_character['health'] = player_health
                    player_character['inventory'].remove(chosen_item_id)
                    return "fled"
                else:
                    print(f"Your {item_to_use_def['name']} creates some concealment, but you still can't escape!")
                    turn_consumed = True
                    
            elif "buff_attack" in item_effects or "buff_defense" in item_effects:
                # Apply temporary buffs
                duration = item_effects.get("duration", 3)
                
                if "buff_attack" in item_effects:
                    attack_buff = StatusEffect(
                        f"{item_to_use_def['name']} (Attack)", 
                        duration, 
                        "buff_attack", 
                        item_effects["buff_attack"], 
                        f"Enhanced by {item_to_use_def['name']}"
                    )
                    player_status_effects.append(attack_buff)
                    effect_applied_message += f" Attack increased by {item_effects['buff_attack']} for {duration} turns."
                
                if "buff_defense" in item_effects:
                    defense_buff = StatusEffect(
                        f"{item_to_use_def['name']} (Defense)", 
                        duration, 
                        "buff_defense", 
                        item_effects["buff_defense"], 
                        f"Protected by {item_to_use_def['name']}"
                    )
                    player_status_effects.append(defense_buff)
                    effect_applied_message += f" Defense increased by {item_effects['buff_defense']} for {duration} turns."
                
                if "debuff_defense" in item_effects:
                    # Some items like berserker brew have negative side effects
                    defense_debuff = StatusEffect(
                        f"{item_to_use_def['name']} (Side Effect)", 
                        duration, 
                        "debuff_defense", 
                        item_effects["debuff_defense"], 
                        f"Side effect of {item_to_use_def['name']}"
                    )
                    player_status_effects.append(defense_debuff)
                    effect_applied_message += f" Defense reduced by {abs(item_effects['debuff_defense'])} as a side effect."
                
                print(effect_applied_message)
                turn_consumed = True
                
            elif "spell_power" in item_effects:
                # Focus crystal type items
                duration = item_effects.get("duration", 5)
                spell_power_buff = StatusEffect(
                    f"{item_to_use_def['name']} (Magic)", 
                    duration, 
                    "spell_power", 
                    item_effects["spell_power"], 
                    f"Enhanced by {item_to_use_def['name']}"
                )
                player_status_effects.append(spell_power_buff)
                effect_applied_message += f" Spell power increased by {item_effects['spell_power']} for {duration} turns."
                print(effect_applied_message)
                turn_consumed = True

            # Handle combination effects (like spirit essence with heal_hp AND restore_mana)
            elif "heal_hp" in item_effects and "restore_mana" in item_effects:
                heal_amount = item_effects["heal_hp"]
                mana_amount = item_effects["restore_mana"]
                
                old_health = player_health
                player_health = min(player_character['max_health'], player_health + heal_amount)
                healed_for = player_health - old_health
                
                old_mana = player_character['mana']
                player_character['mana'] = min(player_character['max_mana'], player_character['mana'] + mana_amount)
                restored_mana = player_character['mana'] - old_mana
                
                effect_applied_message += f" You restored {healed_for} HP and {restored_mana} MP."
                print(effect_applied_message)
                turn_consumed = True

            else: # Item had no recognized effect in combat or was purely narrative
                print(f"You use the {item_to_use_def['name']}, but it has no immediate combat effect.")
                # Decide if using an item with no recognized combat effect consumes a turn.
                # For now, let's assume it does if it was 'combat_usable'.
                turn_consumed = True 

            if turn_consumed:
                player_character['inventory'].remove(chosen_item_id) # Remove one instance
                print(f"{item_to_use_def['name']} removed from inventory.")
                
                # Update player health after item use
                player_character['health'] = player_health

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
                    # Apply magic efficiency to reduce mana cost
                    actual_mana_cost = max(1, spell_data['mana_cost'] - player_character.get('magic_efficiency', 0))
                    if player_character['mana'] >= actual_mana_cost:
                        available_spells_for_choice.append(f"{spell_data['name']} (Cost: {actual_mana_cost} MP)")
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

            # Apply magic efficiency to actual mana cost
            actual_mana_cost = max(1, spell_to_cast['mana_cost'] - player_character.get('magic_efficiency', 0))
            player_character['mana'] -= actual_mana_cost
            print(f"You cast {spell_to_cast['name']}! (Mana: {player_character['mana']}/{player_character['max_mana']})")
            turn_consumed_by_spell = False

            # Apply spell effects
            if spell_to_cast['type'] == "OFFENSE" and spell_to_cast['target'] == "ENEMY":
                spell_damage = spell_to_cast.get('value', 0)
                
                # Special effects for specific spells
                if spell_to_cast.get('id') == 'firebolt':
                    # Chance to apply burning
                    if random.random() < 0.3:
                        burning = StatusEffect("Burning", 3, "damage_over_time", 2, "On fire")
                        enemy_status_effects.append(burning)
                        print(f"The {enemy_name} catches fire!")
                elif spell_to_cast.get('id') == 'frost_lance':
                    # Chance to slow enemy (reduce their damage next turn)
                    if random.random() < 0.4:
                        slow = StatusEffect("Slowed", 2, "debuff_attack", -2, "Slowed by frost")
                        enemy_status_effects.append(slow)
                        print(f"The {enemy_name} is slowed by the frost!")
                elif spell_to_cast.get('special_effect') == 'cannot_miss':
                    print(f"Your {spell_to_cast['name']} cannot miss!")
                
                enemy_health -= spell_damage
                enemy_instance['health'] = enemy_health
                print(f"Your {spell_to_cast['name']} hits the {enemy_name} for {spell_damage} damage! Enemy health is now {enemy_health}.")
                player_momentum += 1
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "HEAL" and spell_to_cast['target'] == "SELF":
                heal_amount = spell_to_cast.get('value', 0)
                old_player_health = player_health
                player_health = min(player_character['max_health'], player_health + heal_amount)
                healed_for = player_health - old_player_health
                player_character['health'] = player_health
                print(f"Your {spell_to_cast['name']} restores {healed_for} HP. Your health is now {player_health}/{player_character['max_health']}.")
                if healed_for == 0 and old_player_health == player_character['max_health']:
                    print("You are already at maximum health.")
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "HEAL_OVER_TIME" and spell_to_cast['target'] == "SELF":
                # Create healing over time effect
                heal_ward = StatusEffect(
                    spell_to_cast['name'], 
                    spell_to_cast['duration'], 
                    "heal_over_time", 
                    spell_to_cast['value'], 
                    "Healing ward active"
                )
                player_status_effects.append(heal_ward)
                print(f"Your {spell_to_cast['name']} creates a healing ward that will restore {spell_to_cast['value']} HP per turn for {spell_to_cast['duration']} turns.")
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "OFFENSE_DOT" and spell_to_cast['target'] == "ENEMY":
                # Create damage over time effect
                poison = StatusEffect(
                    spell_to_cast['name'], 
                    spell_to_cast['duration'], 
                    "damage_over_time", 
                    spell_to_cast['value'], 
                    "Poisoned by magic"
                )
                enemy_status_effects.append(poison)
                print(f"Your {spell_to_cast['name']} creates a toxic cloud around the {enemy_name}! They will take {spell_to_cast['value']} damage per turn for {spell_to_cast['duration']} turns.")
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "VAMPIRIC" and spell_to_cast['target'] == "ENEMY":
                # Life drain - damage enemy and heal self
                spell_damage = spell_to_cast.get('value', 0)
                enemy_health -= spell_damage
                enemy_instance['health'] = enemy_health
                
                # Heal for 50% of damage dealt
                heal_amount = spell_damage // 2
                old_player_health = player_health
                player_health = min(player_character['max_health'], player_health + heal_amount)
                healed_for = player_health - old_player_health
                player_character['health'] = player_health
                
                print(f"Your {spell_to_cast['name']} drains {spell_damage} life from the {enemy_name} and heals you for {healed_for} HP!")
                player_momentum += 1
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "DEBUFF" and spell_to_cast['target'] == "ENEMY":
                # Apply debuff to enemy
                if spell_to_cast.get('id') == 'weakness':
                    debuff = StatusEffect("Weakness", spell_to_cast['duration'], "debuff_attack", spell_to_cast['value'], "Cursed with weakness")
                    enemy_status_effects.append(debuff)
                    print(f"Your {spell_to_cast['name']} weakens the {enemy_name}, reducing their attack power by {abs(spell_to_cast['value'])} for {spell_to_cast['duration']} turns.")
                elif spell_to_cast.get('id') == 'time_slow':
                    debuff = StatusEffect("Time Slow", spell_to_cast['duration'], "time_slow", spell_to_cast['value'], "Caught in slow time")
                    enemy_status_effects.append(debuff)
                    print(f"Your {spell_to_cast['name']} slows time around the {enemy_name}! Their actions will be less effective.")
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "ATTACK_BUFF" and spell_to_cast['target'] == "SELF":
                # Apply attack buff to player
                if spell_to_cast.get('id') == 'battle_fury':
                    buff = StatusEffect("Battle Fury", spell_to_cast['duration'], "buff_attack", spell_to_cast['value'], "Filled with battle rage")
                    player_status_effects.append(buff)
                    print(f"Your {spell_to_cast['name']} fills you with rage! Attack power increased by {spell_to_cast['value']} for {spell_to_cast['duration']} turns.")
                    # Additional crit chance bonus handled separately
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "DEFENSE_BUFF" and spell_to_cast['target'] == "SELF":
                if spell_to_cast.get('id') == 'stone_skin':
                    # Long-lasting defense buff
                    buff = StatusEffect("Stone Skin", spell_to_cast['duration'], "buff_defense", spell_to_cast['value'], "Skin hardened like stone")
                    player_status_effects.append(buff)
                    print(f"Your {spell_to_cast['name']} hardens your skin! Defense increased by {spell_to_cast['value']} for {spell_to_cast['duration']} turns.")
                else:
                    # Original temporary shield system for arcane shield
                    temp_shield_value = spell_to_cast.get('value', 0)
                    player_character['temporary_shield'] = player_character.get('temporary_shield', 0) + temp_shield_value
                    print(f"Your {spell_to_cast['name']} grants you a temporary shield of {temp_shield_value} points (Current: {player_character['temporary_shield']}). It will absorb damage from the next hit.")
                turn_consumed_by_spell = True
                
            elif spell_to_cast['type'] == "UTILITY":
                if spell_to_cast.get('id') == 'dispel_magic':
                    # Remove all status effects from target
                    target = ui.get_numbered_choice("Dispel magic from:", ["Yourself", "Enemy"])
                    if target == "Yourself":
                        if player_status_effects:
                            removed_effects = [effect.name for effect in player_status_effects]
                            player_status_effects.clear()
                            print(f"Removed effects: {', '.join(removed_effects)}")
                        else:
                            print("You have no magical effects to dispel.")
                    else:
                        if enemy_status_effects:
                            removed_effects = [effect.name for effect in enemy_status_effects]
                            enemy_status_effects.clear()
                            print(f"Removed effects from {enemy_name}: {', '.join(removed_effects)}")
                        else:
                            print(f"The {enemy_name} has no magical effects to dispel.")
                elif spell_to_cast.get('id') == 'mana_burn':
                    # Special damage that ignores armor
                    spell_damage = spell_to_cast.get('value', 0)
                    enemy_health -= spell_damage
                    enemy_instance['health'] = enemy_health
                    print(f"Your {spell_to_cast['name']} disrupts the {enemy_name}'s magical essence for {spell_damage} damage that bypasses defenses!")
                turn_consumed_by_spell = True

        elif action == 'Flee':
            # Fleeing chance based on current health ratio and enemy type
            flee_chance = 0.7 + (1.0 - player_health / player_character['max_health']) * 0.2
            if random.random() < flee_chance:
                print("You managed to flee!")
                player_character['health'] = player_health
                return "fled"
            else:
                print("You couldn't escape! The enemy blocks your path!")
                # Failed flee attempt consumes turn
        
        # === ENEMY TURN ===
        if enemy_health > 0:
            # Enhanced enemy AI
            enemy_action = choose_enemy_action(enemy_instance, player_character, enemy_momentum, 
                                             player_health, player_character['max_health'])
            
            if enemy_action == "basic_attack":
                enemy_raw_attack = random.randint(enemy_attack_min, enemy_attack_max)
                
                # Apply enemy debuffs to attack
                enemy_attack_debuff = 0
                for effect in enemy_status_effects:
                    if effect.effect_type == "debuff_attack":
                        enemy_attack_debuff += effect.value  # value is negative for debuffs
                    elif effect.effect_type == "time_slow":
                        enemy_attack_debuff += -2  # Time slow reduces effectiveness
                
                enemy_raw_attack = max(1, enemy_raw_attack + enemy_attack_debuff)  # Minimum 1 damage
                
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
                
                # Calculate defense
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

                # Apply stance defense bonus
                stance_defense = stance_bonuses[player_stance]["defense"]
                
                # Apply status effect defense bonuses
                status_defense_bonus = 0
                for effect in player_status_effects:
                    if effect.effect_type == "buff_defense":
                        status_defense_bonus += effect.value
                
                total_player_defense = player_armor_defense + player_shield_defense + stance_defense + status_defense_bonus
                defense_display = f"{armor_name_display}{shield_name_display}"

                actual_damage_taken = max(0, damage_after_shield - total_player_defense)
                player_health -= actual_damage_taken
                player_character['health'] = player_health
                
                # Show reduced damage from debuffs if applicable
                if enemy_attack_debuff < 0:
                    print(f"The {enemy_name} attacks for {enemy_raw_attack} damage (reduced by debuffs)!{defense_display} You take {actual_damage_taken} damage. Your health is now {player_health}.")
                else:
                    print(f"The {enemy_name} attacks you for {enemy_raw_attack} damage!{defense_display} You take {actual_damage_taken} damage. Your health is now {player_health}.")
                enemy_momentum += 1
                
            elif enemy_action == "special_attack":
                # Execute enemy special attacks
                special_attack = enemy_instance.get('special_attack')
                if special_attack == "poison_bite":
                    damage = random.randint(1, 2)
                    player_health -= damage
                    player_character['health'] = player_health
                    print(f"The {enemy_name} bites you with venomous fangs for {damage} damage!")
                    
                    # Apply poison status effect
                    if random.random() < 0.6:  # 60% chance to poison
                        poison = StatusEffect("Poison", 4, "damage_over_time", 2, "Poisoned")
                        player_status_effects.append(poison)
                        print("You feel poison coursing through your veins!")
                else:
                    # Generic powerful attack
                    damage = random.randint(enemy_attack_min + 2, enemy_attack_max + 4)
                    player_health -= damage
                    player_character['health'] = player_health
                    print(f"The {enemy_name} unleashes a powerful attack for {damage} damage!")
                
                enemy_momentum = max(0, enemy_momentum - 2)  # Special attacks cost momentum
        
        # Check combat end conditions
        if enemy_health <= 0:
            print(f"\nYou defeated the {enemy_name}!")
            player_character['health'] = player_health
            
            # Bonus XP for combat performance
            base_xp = enemy_instance.get('xp_value', 0)
            bonus_xp = 0
            
            if player_momentum >= 5:
                bonus_xp += int(base_xp * 0.2)  # 20% bonus for high momentum
                print(f"Combat mastery bonus! +{bonus_xp} XP")
            
            total_xp = base_xp + bonus_xp
            if total_xp > 0:
                character.gain_xp(player_character, total_xp)
            
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

# Enhanced enemy AI decision making
def choose_enemy_action(enemy_instance, player_character, enemy_momentum, player_health, player_max_health):
    """Enhanced AI that makes tactical decisions based on combat state"""
    
    player_health_ratio = player_health / player_max_health
    has_special_attack = enemy_instance.get('special_attack') is not None
    
    # AI behavior weights
    basic_attack_weight = 60
    special_attack_weight = 0
    
    # If enemy has special attack and momentum, consider using it
    if has_special_attack and enemy_momentum >= 2:
        special_attack_weight = 40
        
        # More likely to use special when player is at high health (finishing move)
        if player_health_ratio < 0.3:
            special_attack_weight += 30
        
        # Some enemies are more aggressive
        if 'aggressive' in enemy_instance.get('ai_traits', []):
            special_attack_weight += 20
    
    # Defensive enemies might be more cautious
    if 'defensive' in enemy_instance.get('ai_traits', []):
        basic_attack_weight += 20
        special_attack_weight -= 10
    
    # Choose action based on weights
    total_weight = basic_attack_weight + special_attack_weight
    if total_weight <= 0:
        return "basic_attack"
    
    roll = random.randint(1, total_weight)
    
    if roll <= basic_attack_weight:
        return "basic_attack"
    else:
        return "special_attack" 