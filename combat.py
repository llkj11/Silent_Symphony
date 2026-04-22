import random
import ui
import items
import character
import config
import entities
import effects
import abilities
import enemy_specials
import world


def combat(player_character, enemy_instance):
    # Per-combat mutable state on the enemy instance (get_enemy_instance returns a shallow copy).
    enemy_instance['effects'] = []
    enemy_instance['_skip_turns'] = 0
    enemy_name = enemy_instance['name']

    print(f"\n--- Combat Initiated! ---")
    combat_actions = ["Attack", "Ability", "Use Item", "Guard", "Flee"]
    round_number = 0

    while player_character['health'] > 0 and enemy_instance['health'] > 0:
        round_number += 1
        # Start-of-round ticks.
        for line in effects.tick_combat_turn(player_character):
            print(line)
        if player_character['health'] <= 0:
            print("You collapse from your lingering wounds.")
            return "lost"
        for line in effects.tick_combat_turn(enemy_instance, subject_label=enemy_name):
            print(line)
        # Stamina regen — silent, capped at max. Urthar's 'stout' trait adds +1.
        stam_regen = 2 if player_character.get('race_trait') == 'stout' else 1
        if player_character.get('stamina', 0) < player_character.get('max_stamina', 0):
            player_character['stamina'] = min(
                player_character.get('max_stamina', 0),
                player_character.get('stamina', 0) + stam_regen,
            )
        if enemy_instance['health'] <= 0:
            print(f"\nThe {enemy_name} succumbs to its wounds!")
            player_character.pop('_guard_active', None)
            _award_xp_and_loot(player_character, enemy_instance)
            return "won"

        print(
            f"\nHealth: {player_character['health']}/{player_character['max_health']} | "
            f"Mana: {player_character.get('mana', 0)}/{player_character.get('max_mana', 0)} | "
            f"Stamina: {player_character.get('stamina', 0)}/{player_character.get('max_stamina', 0)}"
        )
        effect_summary = effects.active_effects_summary(player_character)
        if effect_summary:
            print(f"Effects: {effect_summary}")
        enemy_effect_summary = effects.active_effects_summary(enemy_instance)
        enemy_status_extra = f" [{enemy_effect_summary}]" if enemy_effect_summary else ""
        print(f"{enemy_name} Health: {enemy_instance['health']}{enemy_status_extra}")

        # Player stun check (pre-action).
        if player_character.get('_skip_turns', 0) > 0:
            player_character['_skip_turns'] -= 1
            print("\nYou are stunned and cannot act this round!")
            player_turn_ended = True
        else:
            action = ui.get_numbered_choice("Choose your action:", combat_actions)
            player_turn_ended = False

            if action == 'Attack':
                _do_attack(player_character, enemy_instance)
                player_turn_ended = True

            elif action == 'Ability':
                player_turn_ended = _do_ability(player_character, enemy_instance)

            elif action == 'Use Item':
                player_turn_ended = _do_use_item(player_character, enemy_instance)

            elif action == 'Guard':
                player_character['_guard_active'] = True
                gain = 2
                player_character['stamina'] = min(
                    player_character.get('max_stamina', 0),
                    player_character.get('stamina', 0) + gain,
                )
                print(f"You brace yourself, weapon raised. (+{gain} stamina)")
                player_turn_ended = True

            elif action == 'Flee':
                print("You managed to flee!")
                player_character.pop('_guard_active', None)
                return "fled"

        # Check enemy death before enemy turn.
        if enemy_instance['health'] <= 0:
            print(f"\nYou defeated the {enemy_name}!")
            player_character.pop('_guard_active', None)
            _award_xp_and_loot(player_character, enemy_instance)
            return "won"

        # Enemy retaliation (only if player took a real turn and both sides are still up).
        # A reach weapon lets the player strike freely in the opening exchange.
        if player_turn_ended and player_character['health'] > 0:
            if round_number == 1 and _player_has_reach(player_character):
                weapon = items.ITEM_DB.get(player_character.get('equipped_weapon'), {})
                print(f"Your {weapon.get('name','weapon')}'s reach keeps the {enemy_name} at bay — no counter this round.")
            else:
                _do_enemy_attack(player_character, enemy_instance)

        if player_character['health'] <= 0:
            print("You have been defeated!")
            player_character['health'] = 0
            return "lost"

    return "error"


def _do_attack(player_character, enemy_instance):
    weapon_id = player_character.get('equipped_weapon')
    weapon_data = items.ITEM_DB.get(weapon_id) if weapon_id else None
    weapon_bonus = 0
    accuracy_bonus = 0
    if weapon_data and weapon_data.get('type') == 'weapon':
        weapon_bonus = weapon_data.get('damage_bonus', 0)
        accuracy_bonus = weapon_data.get('accuracy_bonus', 0)
        print(f"You attack with your {weapon_data['name']}!")
    else:
        print("You attack with your bare hands.")

    if player_character.get('race_trait') == 'elven_accuracy':
        accuracy_bonus += 1
    hit_chance = min(0.98, 0.85 + 0.05 * accuracy_bonus)
    if random.random() > hit_chance:
        print(f"Your attack misses the {enemy_instance['name']}!")
        return

    base_damage = random.randint(1, 6)
    is_crit = base_damage == 6
    strength_buff = effects.get_buff_value(player_character, 'buff_strength')
    total_damage = base_damage + weapon_bonus + strength_buff
    fury_bonus = 0
    if (player_character.get('race_trait') == 'low_hp_fury'
            and player_character['health'] <= player_character['max_health'] / 3):
        fury_bonus = 2
        total_damage += fury_bonus
    if is_crit:
        total_damage = int(total_damage * 1.5)

    enemy_instance['health'] = max(0, enemy_instance['health'] - total_damage)
    crit_note = "CRITICAL HIT! " if is_crit else ""
    buff_note = f" (+{strength_buff} strength)" if strength_buff else ""
    fury_note = " (bloodied fury)" if fury_bonus else ""
    print(
        f"{crit_note}You dealt {total_damage} damage{buff_note}{fury_note} to the {enemy_instance['name']}! "
        f"Enemy health is now {enemy_instance['health']}."
    )


def _player_has_reach(player_character):
    weapon_id = player_character.get('equipped_weapon')
    if not weapon_id:
        return False
    data = items.ITEM_DB.get(weapon_id, {})
    return data.get('type') == 'weapon' and bool(data.get('reach'))


def _weapon_magic_bonus(player_character):
    weapon_id = player_character.get('equipped_weapon')
    if not weapon_id:
        return 0
    data = items.ITEM_DB.get(weapon_id, {})
    if data.get('type') != 'weapon':
        return 0
    return data.get('magic_bonus', 0)


def _do_ability(player_character, enemy_instance):
    """Return True if the turn was consumed."""
    known = player_character.get('known_abilities', [])
    valid = []
    for aid in known:
        ability = abilities.ABILITIES.get(aid)
        if ability:
            valid.append((aid, ability))
    if not valid:
        print("You have no abilities to use.")
        return False

    display = []
    for aid, ability in valid:
        cost = abilities.format_cost(ability)
        affordable = abilities.can_afford(player_character, ability)
        suffix = "" if affordable else " [unavailable]"
        display.append(f"{ability['name']} ({cost}) — {ability['description']}{suffix}")
    display.append("[Cancel]")

    chosen = ui.get_numbered_choice("Use which ability?", display)
    if chosen == "[Cancel]":
        return False
    idx = display.index(chosen)
    aid, ability = valid[idx]
    if not abilities.can_afford(player_character, ability):
        print(f"You lack the resources to use {ability['name']}.")
        return False

    abilities.pay_cost(player_character, ability)
    handler = ability.get('handler')
    if not handler:
        print("The ability misfires.")
        return True
    result = handler(player_character, enemy_instance)

    if result.get('narrative'):
        print(result['narrative'])
    if result.get('damage'):
        dmg = result['damage']
        magic_bonus = 0
        attuned_bonus = 0
        if ability.get('magic_scales'):
            magic_bonus = _weapon_magic_bonus(player_character)
            if magic_bonus:
                dmg += magic_bonus
            if player_character.get('race_trait') == 'mana_attuned':
                attuned_bonus = 1
                dmg += attuned_bonus
        enemy_instance['health'] = max(0, enemy_instance['health'] - dmg)
        notes = []
        if magic_bonus:
            notes.append(f"+{magic_bonus} magic")
        if attuned_bonus:
            notes.append(f"+{attuned_bonus} attuned")
        bonus_note = f" ({', '.join(notes)})" if notes else ""
        print(f"The {enemy_instance['name']} takes {dmg} damage{bonus_note}. (HP: {enemy_instance['health']})")
    if result.get('self_heal'):
        heal = result['self_heal']
        before = player_character['health']
        player_character['health'] = min(player_character['max_health'], before + heal)
        print(f"You heal {player_character['health'] - before} HP.")
    if result.get('status_to_enemy'):
        s = result['status_to_enemy']
        effects.add_status(
            enemy_instance,
            s['kind'],
            s['turns'],
            tick_dmg=s.get('tick_dmg', 0),
        )
    if result.get('status_to_self'):
        s = result['status_to_self']
        effects.add_status(
            player_character,
            s['kind'],
            s['turns'],
            tick_dmg=s.get('tick_dmg', 0),
            value=s.get('value', 0),
        )
    return True


def _do_use_item(player_character, enemy_instance):
    """Return True if the turn was consumed."""
    usable = [
        iid for iid in player_character['inventory']
        if items.ITEM_DB.get(iid, {}).get('type') in ('consumable', 'scroll')
    ]
    if not usable:
        print("You have no usable items in your inventory.")
        return False

    seen = set()
    choices = []
    for iid in usable:
        if iid in seen:
            continue
        seen.add(iid)
        count = usable.count(iid)
        name = items.ITEM_DB[iid]['name']
        label = f"{name} x{count}" if count > 1 else name
        choices.append((iid, label))

    display = [label for _, label in choices] + ["[Cancel]"]
    chosen = ui.get_numbered_choice("Use which item?", display)
    if chosen == "[Cancel]":
        return False

    item_id = choices[display.index(chosen)][0]
    enemy_view = {'name': enemy_instance['name'], 'health': enemy_instance['health']}
    res = effects.apply_item_effect(player_character, item_id, in_combat=True, enemy=enemy_view)
    for line in res['narrative']:
        print(line)
    if res['consumed']:
        player_character['inventory'].remove(item_id)
    if res['damage_to_enemy']:
        enemy_instance['health'] = max(0, enemy_instance['health'] - res['damage_to_enemy'])
        print(f"{enemy_instance['name']} health is now {enemy_instance['health']}.")
    return res['ended_combat_turn']


def _do_enemy_attack(player_character, enemy_instance):
    enemy_name = enemy_instance['name']

    if enemy_instance.get('_skip_turns', 0) > 0:
        enemy_instance['_skip_turns'] -= 1
        print(f"The {enemy_name} reels, unable to act this round!")
        return

    special_id = enemy_specials.get_special_for_turn(enemy_instance)
    if special_id:
        result = enemy_specials.execute_special(special_id, player_character, enemy_instance)
        if result:
            print(result['narrative'])
            raw = result.get('damage', 0)
            bypass = result.get('bypasses_defense', False)
            damage_type = result.get('damage_type', 'physical')
            actual = _apply_damage_to_player(
                player_character, raw, bypass=bypass, damage_type=damage_type
            )
            print(f"You take {actual} damage. (HP: {player_character['health']})")
            status = result.get('status_to_player')
            if status:
                effects.add_status(
                    player_character,
                    status['kind'],
                    status['turns'],
                    tick_dmg=status.get('tick_dmg', 0),
                )
                print(f"You are afflicted with {status['kind']}!")
            return

    # Basic attack — hit roll + crit on natural max.
    hit_chance = 0.85
    if random.random() > hit_chance:
        print(f"The {enemy_name}'s attack goes wide!")
        return

    attack_min = enemy_instance['attack_min']
    attack_max = enemy_instance['attack_max']
    raw = random.randint(attack_min, attack_max)
    is_crit = attack_max > attack_min and raw == attack_max
    if is_crit:
        raw = int(raw * 1.5)
    actual = _apply_damage_to_player(player_character, raw, bypass=False)
    crit_note = "A savage blow! " if is_crit else ""
    print(f"{crit_note}The {enemy_name} attacks you for {raw} damage. You take {actual}. (HP: {player_character['health']})")


def _apply_damage_to_player(player_character, raw, bypass, damage_type='physical'):
    """Apply incoming damage respecting armor, shield, magic resistance, and guard.

    Physical damage is reduced by summed armor + shield defense (unless `bypass`).
    Magical/elemental damage is reduced by magic_resistance instead; physical
    armor does not apply. `bypass` skips physical armor and guard but not MR.
    """
    if damage_type == 'physical':
        defense = 0 if bypass else character.armor_defense_total(player_character, items.ITEM_DB)
    else:
        defense = character.magic_resistance_total(player_character, items.ITEM_DB)

    dmg = max(0, raw - defense)

    guard_was_active = player_character.pop('_guard_active', False)
    if guard_was_active and not bypass:
        dmg = dmg // 2

    player_character['health'] = max(0, player_character['health'] - dmg)
    return dmg


def _award_xp_and_loot(player_character, enemy_instance):
    if enemy_instance.get('unique'):
        world.mark_enemy_slain(player_character, enemy_instance.get('id'))

    xp_reward = enemy_instance.get('xp_value', 0)
    if xp_reward > 0:
        character.gain_xp(player_character, xp_reward)

    gold_range = enemy_instance.get('gold_drop')
    if gold_range and len(gold_range) == 2:
        gold = random.randint(gold_range[0], gold_range[1])
        if gold > 0:
            player_character['gold'] = player_character.get('gold', 0) + gold
            print(f"You recover {gold} gold. (Total: {player_character['gold']})")

    dropped_items_this_combat = []

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

    for loot_entry in enemy_instance.get('unique_loot', []):
        item_id = loot_entry.get("item_id")
        chance = loot_entry.get("chance", 0)
        if item_id and random.random() <= chance:
            if item_id in items.ITEM_DB:
                player_character['inventory'].append(item_id)
                dropped_items_this_combat.append(items.ITEM_DB[item_id]['name'])
            elif config.DEBUG_MODE:
                print(f"DEBUG: Unique loot item ID '{item_id}' not found in ITEM_DB.")

    # Legacy loot_table format (list-of-strings or list-of-dicts) — some older enemies still use it.
    old_format_loot_table = enemy_instance.get('loot_table', [])
    if old_format_loot_table and isinstance(old_format_loot_table[0], str):
        if config.DEBUG_MODE:
            enemy_name = enemy_instance.get('name', enemy_instance.get('id', '?'))
            print(f"DEBUG: Enemy '{enemy_name}' is using old loot_table string format. Please update.")
        for item_id in old_format_loot_table:
            if item_id in items.ITEM_DB:
                player_character['inventory'].append(item_id)
                dropped_items_this_combat.append(items.ITEM_DB[item_id]['name'])
    elif old_format_loot_table and isinstance(old_format_loot_table[0], dict):
        for loot_entry in old_format_loot_table:
            item_id = loot_entry.get("item_id")
            chance = loot_entry.get("chance", 0)
            if item_id and random.random() <= chance:
                if item_id in items.ITEM_DB:
                    player_character['inventory'].append(item_id)
                    dropped_items_this_combat.append(items.ITEM_DB[item_id]['name'])
                elif config.DEBUG_MODE:
                    print(f"DEBUG: Loot item ID '{item_id}' from loot table not found in ITEM_DB.")

    if dropped_items_this_combat:
        enemy_name = enemy_instance.get('name', 'The foe')
        print(f"The {enemy_name} dropped:")
        for item_name_dropped in dropped_items_this_combat:
            print(f"- {item_name_dropped}")
        print("Added to your inventory.")
    else:
        print(f"The {enemy_instance.get('name', 'foe')} dropped nothing of interest this time.")
