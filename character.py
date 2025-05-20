import random
import game_data
import ui

SKILLS_DATA = {
    'power_attack': {
        'name': 'Power Attack',
        'cooldown': 2,
        'damage_multiplier': 1.5,
        'description': 'A strong attack that deals 1.5x damage. Cooldown: 2 turns.'
    },
    'shield_bash': {
        'name': 'Shield Bash',
        'cooldown': 3,
        'damage_multiplier': 0.5,
        'effect': {'type': 'stun', 'chance': 0.3, 'duration': 1},
        'description': 'Bash with your shield, dealing 0.5x damage with a 30% chance to stun for 1 turn. Cooldown: 3 turns. Requires a shield.'
    }
}

def get_skill_details(skill_id):
    """Returns the details of a skill from SKILLS_DATA."""
    return SKILLS_DATA.get(skill_id)

# --- Leveling Configuration ---
BASE_XP_TO_NEXT_LEVEL = 50
XP_LEVEL_MULTIPLIER = 1.5 # How much more XP is needed for each subsequent level (e.g., 100, 150, 225)
LEVEL_UP_HEALTH_BONUS = 10

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
        player_character['max_health'] += LEVEL_UP_HEALTH_BONUS
        # Heal player by the amount max_health increased, up to new max_health
        player_character['health'] = min(player_character['max_health'], player_character['health'] + LEVEL_UP_HEALTH_BONUS)
        
        print(f"\n*** LEVEL UP! ***")
        print(f"You are now Level {player_character['level']}!")
        print(f"Max Health increased from {old_max_health} to {player_character['max_health']}.")
        print(f"Health restored. Current Health: {player_character['health']}/{player_character['max_health']}.")
        print(f"XP to next level: {player_character['xp_to_next_level']}.")
        # Future: Add attribute points, skill unlocks, etc.
    return leveled_up

def gain_xp(player_character, amount):
    if amount <= 0:
        return
    print(f"\nYou gained {amount} XP.")
    player_character['xp'] += amount
    check_for_level_up(player_character)

# Character Creation Function with Validation
def character_creation():
    print("Welcome to The Silent Symphony!")
    player_character = {}

    quick_start_input = input("Quick Start character creation? (y/n): ").strip().lower()

    if quick_start_input == 'y':
        player_character['name'] = "Rynn"
        player_character['race'] = random.choice(game_data.valid_races)
        player_character['origin'] = random.choice(game_data.valid_origins)
        player_character['star_sign'] = random.choice(game_data.valid_star_signs)
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
    player_character['available_skills'] = ['power_attack', 'shield_bash']
    player_character['skill_cooldowns'] = {}
    # Initialize skill cooldowns to 0
    for skill in player_character["available_skills"]:
        if skill in SKILLS_DATA:
             player_character["skill_cooldowns"][skill] = 0

    return player_character 

def is_skill_on_cooldown(player_character, skill_id):
    """Checks if a skill is currently on cooldown."""
    return player_character['skill_cooldowns'].get(skill_id, 0) > 0

def set_skill_on_cooldown(player_character, skill_id):
    """Sets the cooldown for a skill."""
    skill_details = get_skill_details(skill_id)
    if skill_details:
        player_character['skill_cooldowns'][skill_id] = skill_details['cooldown']

def decrement_skill_cooldowns(player_character):
    """Decrements all active skill cooldowns by 1."""
    for skill_id in player_character['skill_cooldowns']:
        if player_character['skill_cooldowns'][skill_id] > 0:
            player_character['skill_cooldowns'][skill_id] -= 1
