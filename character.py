import random
import game_data
import ui
import abilities


ARMOR_SLOTS = ['head', 'chest', 'legs', 'hands', 'feet']
ARMOR_SLOT_FIELDS = {slot: f'equipped_{slot}' for slot in ARMOR_SLOTS}


def armor_defense_total(player, item_db):
    """Sum defense_bonus across all equipped armor slots + shield.

    Dwarven `armor_mastery` grants +1 defense per equipped armor piece.
    """
    total = 0
    armor_pieces = 0
    for field in ARMOR_SLOT_FIELDS.values():
        iid = player.get(field)
        if iid and iid in item_db:
            data = item_db[iid]
            if data.get('type') == 'armor':
                total += data.get('defense_bonus', 0)
                armor_pieces += 1
    shield_id = player.get('equipped_shield')
    if shield_id and shield_id in item_db:
        sdata = item_db[shield_id]
        if sdata.get('type') == 'shield':
            total += sdata.get('defense_bonus', 0)
    if player.get('race_trait') == 'armor_mastery':
        total += armor_pieces
    return total


def magic_resistance_total(player, item_db):
    """Sum magic_resistance from equipped armor + shield (from their `effect` dict)."""
    total = 0
    for field in list(ARMOR_SLOT_FIELDS.values()) + ['equipped_shield']:
        iid = player.get(field)
        if iid and iid in item_db:
            effect = item_db[iid].get('effect', {}) or {}
            total += effect.get('magic_resistance', 0)
    return total


def slot_for_item(item_data):
    """Return which player field an equippable item slots into, or None."""
    if not item_data:
        return None
    item_type = item_data.get('type')
    if item_type == 'weapon':
        return 'equipped_weapon'
    if item_type == 'shield':
        return 'equipped_shield'
    if item_type == 'armor':
        slot = item_data.get('slot')
        if slot in ARMOR_SLOTS:
            return f'equipped_{slot}'
    return None

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
        player_character['xp_to_next_level'] = int(BASE_XP_TO_NEXT_LEVEL * (XP_LEVEL_MULTIPLIER ** (player_character['level'] - 1)))
        
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

    starting_ability_id = abilities.starting_abilities_for(player_character['star_sign'])
    if starting_ability_id:
        ability = abilities.ABILITIES.get(starting_ability_id[0])
        if ability:
            print(f"\nYour sign grants you the ability: {ability['name']} — {ability['description']} (cost: {abilities.format_cost(ability)})")
    
    player_character['health'] = 30
    player_character['max_health'] = 30
    player_character['mana'] = 10
    player_character['max_mana'] = 10
    player_character['stamina'] = 10
    player_character['max_stamina'] = 10
    player_character['effects'] = []
    player_character['known_abilities'] = abilities.starting_abilities_for(player_character['star_sign'])
    player_character['inventory'] = []
    player_character['gold'] = 0
    player_character['race_trait'] = None
    player_character['location'] = "beach_starting"
    player_character['last_described_location'] = None
    player_character['equipped_weapon'] = None
    player_character['equipped_shield'] = None
    for slot in ARMOR_SLOTS:
        player_character[f'equipped_{slot}'] = None
    player_character['level'] = 1
    player_character['xp'] = 0
    player_character['xp_to_next_level'] = int(BASE_XP_TO_NEXT_LEVEL * (XP_LEVEL_MULTIPLIER ** 0)) # Initial XP for level 1 to 2

    _apply_race(player_character)
    _apply_origin(player_character)

    return player_character


def _apply_race(player):
    """Apply race stat modifiers + record the race trait. Idempotent-ish — only
    mutates the first time for each created character."""
    race = player.get('race')
    trait_def = game_data.RACE_TRAITS.get(race)
    if not trait_def:
        return
    for field, delta in trait_def.get('stat_mods', {}).items():
        player[field] = max(1, player.get(field, 0) + delta)
    player['health'] = player['max_health']
    player['mana'] = player.get('max_mana', 0)
    player['stamina'] = player.get('max_stamina', 0)
    player['race_trait'] = trait_def.get('trait')
    desc = trait_def.get('description') or ""
    trait_desc = trait_def.get('trait_description') or ""
    if desc:
        print(f"\nAs a {race}, {desc}")
    if trait_desc:
        print(f"  Racial trait: {trait_desc}")


def _apply_origin(player):
    """Grant origin starting inventory and gold."""
    origin = player.get('origin')
    kit = game_data.ORIGIN_STARTING_KIT.get(origin)
    if not kit:
        return
    for iid in kit.get('inventory', []):
        player['inventory'].append(iid)
    player['gold'] = player.get('gold', 0) + kit.get('gold', 0)
    flavor = kit.get('flavor')
    if flavor:
        print(f"\nYour {origin} upbringing left you with {flavor}.")
