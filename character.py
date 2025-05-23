import random
import game_data
import ui
import spells  # Import spells for learning system
import items  # Import items for equipment display

# --- Leveling Configuration ---
BASE_XP_TO_NEXT_LEVEL = 50
XP_LEVEL_MULTIPLIER = 1.5 # How much more XP is needed for each subsequent level (e.g., 100, 150, 225)
LEVEL_UP_HEALTH_BONUS = 10
LEVEL_UP_MANA_BONUS = 5
SKILL_POINTS_PER_LEVEL = 2

# --- Character Helper Functions ---
def check_for_level_up(player_character):
    leveled_up = False
    while player_character['xp'] >= player_character['xp_to_next_level']:
        leveled_up = True
        player_character['level'] += 1
        # Deduct the XP for the level up, but carry over excess XP
        player_character['xp'] -= player_character['xp_to_next_level'] 
        
        # Update xp_to_next_level (example: simple scaling)
        player_character['xp_to_next_level'] = int(BASE_XP_TO_NEXT_LEVEL * (XP_LEVEL_MULTIPLIER ** (player_character['level' -1] )))
        
        old_max_health = player_character['max_health']
        old_max_mana = player_character['max_mana']
        
        player_character['max_health'] += LEVEL_UP_HEALTH_BONUS
        player_character['max_mana'] += LEVEL_UP_MANA_BONUS
        
        # Heal player by the amount max_health increased, up to new max_health
        player_character['health'] = min(player_character['max_health'], player_character['health'] + LEVEL_UP_HEALTH_BONUS)
        # Restore some mana as well
        player_character['mana'] = min(player_character['max_mana'], player_character['mana'] + LEVEL_UP_MANA_BONUS)
        
        # Award skill points
        player_character['skill_points'] = player_character.get('skill_points', 0) + SKILL_POINTS_PER_LEVEL
        
        print(f"\n*** LEVEL UP! ***")
        print(f"You are now Level {player_character['level']}!")
        print(f"Max Health increased from {old_max_health} to {player_character['max_health']}.")
        print(f"Max Mana increased from {old_max_mana} to {player_character['max_mana']}.")
        print(f"Health restored. Current Health: {player_character['health']}/{player_character['max_health']}.")
        print(f"Mana restored. Current Mana: {player_character['mana']}/{player_character['max_mana']}.")
        print(f"You gained {SKILL_POINTS_PER_LEVEL} skill points! Total: {player_character['skill_points']}")
        print(f"XP to next level: {player_character['xp_to_next_level']}.")
        
        # Check for new spells available to learn
        available_spells = spells.get_available_spells_to_learn(player_character)
        if available_spells:
            print(f"\nNew spells available to learn: {', '.join([spells.SPELL_DB[spell]['name'] for spell in available_spells])}")
            print("Visit a trainer or use your skill points to learn them!")
    
    return leveled_up

def gain_xp(player_character, amount):
    if amount <= 0:
        return
    print(f"\nYou gained {amount} XP.")
    player_character['xp'] += amount
    check_for_level_up(player_character)

def spend_skill_points_menu(player_character):
    """Interactive menu for spending skill points"""
    while player_character.get('skill_points', 0) > 0:
        print(f"\n--- Skill Point Allocation ---")
        print(f"Available Skill Points: {player_character['skill_points']}")
        
        options = []
        
        # Spell learning options
        available_spells = spells.get_available_spells_to_learn(player_character)
        if available_spells:
            options.append("Learn New Spells")
        
        # Attribute improvements
        options.extend([
            "Increase Max Health (+10 HP) - 1 skill point",
            "Increase Max Mana (+5 MP) - 1 skill point", 
            "Improve Combat Training (+1% crit chance) - 2 skill points",
            "Improve Magic Efficiency (-1 mana cost for all spells) - 3 skill points"
        ])
        
        options.append("Exit")
        
        choice = ui.get_numbered_choice("How would you like to spend your skill points?", options)
        
        if choice == "Learn New Spells":
            learn_spell_menu(player_character)
        elif choice.startswith("Increase Max Health"):
            if player_character['skill_points'] >= 1:
                player_character['max_health'] += 10
                player_character['skill_points'] -= 1
                print("Max health increased by 10!")
            else:
                print("Not enough skill points!")
        elif choice.startswith("Increase Max Mana"):
            if player_character['skill_points'] >= 1:
                player_character['max_mana'] += 5
                player_character['skill_points'] -= 1
                print("Max mana increased by 5!")
            else:
                print("Not enough skill points!")
        elif choice.startswith("Improve Combat Training"):
            if player_character['skill_points'] >= 2:
                player_character['combat_training'] = player_character.get('combat_training', 0) + 1
                player_character['skill_points'] -= 2
                print("Combat training improved! Critical hit chance increased.")
            else:
                print("Not enough skill points!")
        elif choice.startswith("Improve Magic Efficiency"):
            if player_character['skill_points'] >= 3:
                player_character['magic_efficiency'] = player_character.get('magic_efficiency', 0) + 1
                player_character['skill_points'] -= 3
                print("Magic efficiency improved! All spells now cost 1 less mana (minimum 1).")
            else:
                print("Not enough skill points!")
        elif choice == "Exit":
            break
    
    if player_character.get('skill_points', 0) == 0:
        print("No skill points remaining.")

def learn_spell_menu(player_character):
    """Menu for learning new spells"""
    available_spells = spells.get_available_spells_to_learn(player_character)
    
    if not available_spells:
        print("No new spells available to learn at your current level.")
        return
    
    print("\n--- Spell Learning ---")
    spell_options = []
    for spell_id in available_spells:
        spell = spells.SPELL_DB[spell_id]
        cost = calculate_spell_learning_cost(spell)
        spell_options.append(f"{spell['name']} - {spell['description']} (Cost: {cost} skill points)")
    
    spell_options.append("Back")
    
    choice = ui.get_numbered_choice("Which spell would you like to learn?", spell_options)
    
    if choice == "Back":
        return
    
    # Find the selected spell
    chosen_index = spell_options.index(choice)
    chosen_spell_id = available_spells[chosen_index]
    chosen_spell = spells.SPELL_DB[chosen_spell_id]
    cost = calculate_spell_learning_cost(chosen_spell)
    
    if player_character.get('skill_points', 0) >= cost:
        player_character['known_spells'].append(chosen_spell_id)
        player_character['skill_points'] -= cost
        print(f"You learned {chosen_spell['name']}!")
    else:
        print("Not enough skill points to learn this spell.")

def calculate_spell_learning_cost(spell):
    """Calculate skill point cost for learning a spell"""
    base_cost = spell.get('level', 1)
    return max(1, base_cost // 2)  # Higher level spells cost more

def character_development(player_character):
    """Main character development menu"""
    while True:
        print(f"\n--- Character Development ---")
        print(f"Name: {player_character['name']} the {player_character['race']} {player_character['origin']}")
        print(f"Level: {player_character['level']} | XP: {player_character['xp']}/{player_character['xp_to_next_level']}")
        print(f"Health: {player_character['health']}/{player_character['max_health']}")
        print(f"Mana: {player_character['mana']}/{player_character['max_mana']}")
        print(f"Skill Points Available: {player_character.get('skill_points', 0)}")
        
        # Show character improvements
        if player_character.get('combat_training', 0) > 0:
            print(f"Combat Training: Level {player_character['combat_training']} (+{player_character['combat_training']}% crit chance)")
        if player_character.get('magic_efficiency', 0) > 0:
            print(f"Magic Efficiency: Level {player_character['magic_efficiency']} (-{player_character['magic_efficiency']} mana cost)")
        
        # Show known spells
        known_spells = player_character.get('known_spells', [])
        if known_spells:
            print(f"\nKnown Spells ({len(known_spells)}):")
            for spell_id in known_spells:
                if spell_id in spells.SPELL_DB:
                    spell = spells.SPELL_DB[spell_id]
                    actual_cost = max(1, spell['mana_cost'] - player_character.get('magic_efficiency', 0))
                    print(f"  - {spell['name']} (Cost: {actual_cost} MP): {spell['description']}")
        
        # Show available actions
        options = []
        if player_character.get('skill_points', 0) > 0:
            options.append("Spend Skill Points")
        
        options.extend([
            "View Spell Details",
            "Character Stats Summary",
            "Back to Game"
        ])
        
        choice = ui.get_numbered_choice("What would you like to do?", options)
        
        if choice == "Spend Skill Points":
            spend_skill_points_menu(player_character)
        elif choice == "View Spell Details":
            view_spell_details(player_character)
        elif choice == "Character Stats Summary":
            show_detailed_stats(player_character)
        elif choice == "Back to Game":
            break

def view_spell_details(player_character):
    """Show detailed information about known spells"""
    known_spells = player_character.get('known_spells', [])
    if not known_spells:
        print("You don't know any spells yet.")
        return
    
    spell_options = []
    for spell_id in known_spells:
        if spell_id in spells.SPELL_DB:
            spell = spells.SPELL_DB[spell_id]
            spell_options.append(f"{spell['name']}")
    
    spell_options.append("Back")
    
    choice = ui.get_numbered_choice("Which spell would you like to examine?", spell_options)
    
    if choice == "Back":
        return
    
    # Find the selected spell
    chosen_index = spell_options.index(choice)
    chosen_spell_id = known_spells[chosen_index]
    spell = spells.SPELL_DB[chosen_spell_id]
    
    print(f"\n--- {spell['name']} ---")
    print(f"School: {spell.get('school', 'Unknown').title()}")
    print(f"Level: {spell.get('level', 1)}")
    actual_cost = max(1, spell['mana_cost'] - player_character.get('magic_efficiency', 0))
    print(f"Mana Cost: {actual_cost} MP")
    print(f"Type: {spell['type']}")
    print(f"Target: {spell['target']}")
    if spell.get('duration', 0) > 0:
        print(f"Duration: {spell['duration']} turns")
    if spell.get('value', 0) > 0:
        if spell['type'] in ['OFFENSE', 'VAMPIRIC']:
            print(f"Damage: {spell['value']}")
        elif spell['type'] in ['HEAL', 'HEAL_OVER_TIME']:
            print(f"Healing: {spell['value']}")
        elif 'BUFF' in spell['type']:
            print(f"Bonus: +{spell['value']}")
        elif 'DEBUFF' in spell['type']:
            print(f"Penalty: {spell['value']}")
    print(f"Description: {spell['description']}")
    
    if spell.get('special_effect'):
        print(f"Special Effect: {spell['special_effect']}")

def show_detailed_stats(player_character):
    """Show comprehensive character statistics"""
    print(f"\n--- Detailed Character Stats ---")
    print(f"Name: {player_character['name']}")
    print(f"Race: {player_character['race']}")
    print(f"Origin: {player_character['origin']}")
    print(f"Star Sign: {player_character['star_sign']}")
    print(f"\nLevel: {player_character['level']}")
    print(f"Experience: {player_character['xp']}/{player_character['xp_to_next_level']}")
    print(f"Health: {player_character['health']}/{player_character['max_health']}")
    print(f"Mana: {player_character['mana']}/{player_character['max_mana']}")
    
    # Combat stats
    base_crit = 5 + player_character.get('combat_training', 0)
    print(f"\nCombat Stats:")
    print(f"Base Critical Hit Chance: {base_crit}%")
    if player_character.get('magic_efficiency', 0) > 0:
        print(f"Mana Cost Reduction: {player_character['magic_efficiency']}")
    
    # Equipment
    print(f"\nEquipment:")
    weapon_name = "None"
    if player_character.get('equipped_weapon') and player_character['equipped_weapon'] in items.ITEM_DB:
        weapon_name = items.ITEM_DB[player_character['equipped_weapon']]['name']
    print(f"Weapon: {weapon_name}")
    
    armor_name = "None" 
    if player_character.get('equipped_armor') and player_character['equipped_armor'] in items.ITEM_DB:
        armor_name = items.ITEM_DB[player_character['equipped_armor']]['name']
    print(f"Armor: {armor_name}")
    
    shield_name = "None"
    if player_character.get('equipped_shield') and player_character['equipped_shield'] in items.ITEM_DB:
        shield_name = items.ITEM_DB[player_character['equipped_shield']]['name']
    print(f"Shield: {shield_name}")
    
    print(f"\nInventory Items: {len(player_character.get('inventory', []))}")
    print(f"Known Spells: {len(player_character.get('known_spells', []))}")
    print(f"Available Skill Points: {player_character.get('skill_points', 0)}")

# Character Creation Function with Validation
def character_creation():
    print("Welcome to The Silent Symphony!")
    player_character = {}

    quick_start_input = input("Quick Start character creation? (y/n): ").strip().lower()

    if quick_start_input == 'y':
        # Generate random character attributes
        player_character['race'] = random.choice(game_data.valid_races)
        player_character['origin'] = random.choice(game_data.valid_origins)
        player_character['star_sign'] = random.choice(game_data.valid_star_signs)
        
        # Generate random name based on race
        race_names = game_data.random_names.get(player_character['race'], game_data.random_names["Human"])
        all_names = race_names["male"] + race_names["female"] + race_names["neutral"]
        player_character['name'] = random.choice(all_names)
        
        print(f"\nQuick Start selected! Your character is {player_character['name']}, a {player_character['race']} {player_character['origin']} born under the sign of {player_character['star_sign']}.")
    else:
        player_character['race'] = ui.get_numbered_choice("\nChoose your race:", game_data.valid_races)
        player_character['origin'] = ui.get_numbered_choice("\nChoose your origin:", game_data.valid_origins)
        player_character['star_sign'] = ui.get_numbered_choice("\nChoose your star sign:", game_data.valid_star_signs)
        player_character['name'] = input("\nWhat is your character's name?: ").strip()
        while not player_character['name']:
            print("Name cannot be empty.")
            player_character['name'] = input("What is your character's name?: ").strip()

    backstory_template = f"""
    You awaken to the gentle lapping of waves, the caress of seafoam at your feet, a stark contrast to the tempest that raged just hours before. Your body lies heavy upon the wet sand, each breath a testament to your survival against the capricious wrath of the sea. As your eyes flutter open, the blurred edges of reality sharpen, revealing the sun-drenched shores of some land unknown to you, {player_character['name']}.

Memories flash like lightning across the firmament of your mind — the creaking of wood, the howl of the storm, the desperate cries of your companions now lost to the abyss. The details of your past voyage are as scattered as the flotsam strewn about the beach, but one thing is clear: you are far from home.

This land greets you with its wild, untamed beauty. Towering cliffs crowned with verdure rise to the east, and to the west, the ocean spans the horizon, a sapphire sheet etched with the gold of the dawning day. 

Now, as destiny's hand guides you forth from the shores of providence, you stand at the threshold of a new beginning. Here, amidst the echoes of a history both grand and cruel, you, a {player_character['race']} of {player_character['origin']} origin, born under the sign of {player_character['star_sign']}, will find your place in the stories yet unwritten. Your journey begins not with the remembrance of whence you came, but with the promise of what lies ahead.

With the salt on your lips and the horizon calling, you rise. The path before you is fraught with shadows and light, danger and opportunity. Every step is a story, and every choice carves the key to your future.

As you take your first steps into the unknown, you can't shake the feeling that your arrival was no mere accident. The threads of destiny are woven tight around your fate, and only time will reveal the role you are to play in this new world. 
    """
    print("\n--- Your Story Begins ---")
    print(backstory_template)
    
    print(f"\nWelcome, {player_character['name']} the {player_character['race']} {player_character['origin']}, born under the sign of {player_character['star_sign']}. Your journey begins now...")
    
    player_character['health'] = 30 
    player_character['max_health'] = 30
    player_character['inventory'] = []
    player_character['location'] = "beach_starting"
    player_character['last_described_location'] = None
    player_character['equipped_weapon'] = None
    player_character['equipped_armor'] = None
    player_character['equipped_shield'] = None
    player_character['level'] = 1
    player_character['xp'] = 0
    player_character['xp_to_next_level'] = int(BASE_XP_TO_NEXT_LEVEL * (XP_LEVEL_MULTIPLIER ** 0)) # Initial XP for level 1 to 2
    player_character['completed_pois'] = {}
    player_character['known_spells'] = ['minor_heal']
    player_character['max_mana'] = 10
    player_character['mana'] = 10
    player_character['skill_points'] = 0
    player_character['combat_training'] = 0
    player_character['magic_efficiency'] = 0

    return player_character 