import items


def apply_item_effect(player, item_id, in_combat=False, enemy=None):
    """Apply a consumable or scroll effect.

    Returns a dict:
        ok: effect applied successfully
        consumed: item should be removed from inventory (False if fizzled; also
            False when a `uses`-tracked item still has charges left — callers
            should leave it in inventory in that case)
        uses_remaining: for items declaring `uses`, the charges remaining after
            this use. None for single-use items.
        narrative: list[str] of lines to show the player
        damage_to_enemy: int damage for caller to subtract from current foe
        ended_combat_turn: True if using this counts as the player's combat action
    """
    result = {
        "ok": False,
        "consumed": False,
        "uses_remaining": None,
        "narrative": [],
        "damage_to_enemy": 0,
        "ended_combat_turn": False,
    }

    item_data = items.ITEM_DB.get(item_id)
    if not item_data:
        result["narrative"].append("The item vanishes, as if it never was.")
        return result

    effect = item_data.get("effect")
    if not effect:
        result["narrative"].append(f"{item_data['name']} has no usable effect.")
        return result

    item_name = item_data.get("name", item_id)
    applied_any = False

    if "heal" in effect:
        amount = effect["heal"]
        before = player["health"]
        player["health"] = min(player["max_health"], before + amount)
        gained = player["health"] - before
        result["narrative"].append(
            f"You use {item_name}. Recovered {gained} HP ({player['health']}/{player['max_health']})."
        )
        applied_any = True

    if "restore_mana" in effect:
        amount = effect["restore_mana"]
        before = player.get("mana", 0)
        player["mana"] = min(player.get("max_mana", 0), before + amount)
        gained = player["mana"] - before
        result["narrative"].append(
            f"Magical energy flows in. +{gained} mana ({player['mana']}/{player.get('max_mana', 0)})."
        )
        applied_any = True

    # Buffs share a normalized duration. Items declare `duration` in loose units;
    # we clamp to a playable combat-turn count.
    if "buff_stamina" in effect or "buff_strength" in effect:
        raw_duration = effect.get("duration", 30)
        turns = max(1, min(10, raw_duration // 10))
        for buff_key in ("buff_stamina", "buff_strength"):
            if buff_key in effect:
                _add_or_refresh_effect(player, buff_key, turns, value=effect[buff_key])
                label = buff_key.replace("buff_", "")
                result["narrative"].append(
                    f"You feel a surge of {label} (+{effect[buff_key]} for {turns} turns)."
                )
                applied_any = True

    if effect.get("cure_poison"):
        removed = _remove_effect(player, "poison")
        result["narrative"].append(
            "The poison in your veins is neutralized."
            if removed
            else "You drink it, but there was no poison to cure."
        )
        applied_any = True

    if effect.get("cure_bleeding"):
        removed = _remove_effect(player, "bleeding")
        result["narrative"].append(
            "The bleeding stops."
            if removed
            else "You apply the poultice. Soothing, though you were not bleeding."
        )
        applied_any = True

    if "cast_spell" in effect:
        spell = effect["cast_spell"]
        spell_damage = effect.get("damage", 0)
        if spell_damage > 0:
            if in_combat and enemy is not None:
                # Staves and similar channelers boost spell damage via `magic_bonus`.
                weapon_id = player.get("equipped_weapon")
                weapon = items.ITEM_DB.get(weapon_id, {}) if weapon_id else {}
                magic_bonus = weapon.get("magic_bonus", 0) if weapon.get("type") == "weapon" else 0
                total_damage = spell_damage + magic_bonus
                result["damage_to_enemy"] = total_damage
                bonus_note = f" (+{magic_bonus} from your {weapon.get('name','focus')})" if magic_bonus else ""
                result["narrative"].append(
                    f"You read {item_name}. A bolt of {spell} strikes {enemy.get('name','the foe')} for {total_damage} damage{bonus_note}!"
                )
                applied_any = True
            else:
                result["narrative"].append(
                    f"You begin to read {item_name}, but there is no target. The energy dissipates."
                )
                return result  # fizzle; not consumed
        else:
            result["narrative"].append(
                f"You invoke {spell}. {_utility_spell_narrative(spell)}"
            )
            applied_any = True

    if "sate_hunger" in effect and not applied_any:
        result["narrative"].append(f"You eat {item_name}. It's filling.")
        applied_any = True

    if applied_any:
        result["ok"] = True
        if in_combat:
            result["ended_combat_turn"] = True
        max_uses = item_data.get("uses")
        if max_uses and max_uses > 1:
            remaining = _decrement_uses(player, item_id, max_uses)
            result["uses_remaining"] = remaining
            if remaining > 0:
                result["consumed"] = False
                result["narrative"].append(f"({remaining} use{'s' if remaining != 1 else ''} remaining.)")
            else:
                result["consumed"] = True
                result["narrative"].append(f"Your {item_name} is spent.")
        else:
            result["consumed"] = True

    return result


def _decrement_uses(player, item_id, max_uses):
    """Track remaining charges for an item_id. Returns charges left after this use.

    A shared counter per item_id — if the player carries two identical multi-use
    items they share the pool. That's a deliberate simplification; promote to a
    per-instance model only if stacks of multi-use items become common.
    """
    tracker = player.setdefault("item_uses", {})
    current = tracker.get(item_id, max_uses)
    remaining = max(0, current - 1)
    if remaining > 0:
        tracker[item_id] = remaining
    else:
        tracker.pop(item_id, None)
    return remaining


def _utility_spell_narrative(spell):
    return {
        "light": "A warm glow surrounds you, pushing back the darkness.",
    }.get(spell, "The spell takes effect.")


def _add_or_refresh_effect(player, kind, turns, value=0, tick_dmg=0):
    effects = player.setdefault("effects", [])
    for e in effects:
        if e.get("kind") == kind:
            e["turns_remaining"] = max(e.get("turns_remaining", 0), turns)
            if value:
                e["value"] = max(e.get("value", 0), value)
            if tick_dmg:
                e["tick_dmg"] = max(e.get("tick_dmg", 0), tick_dmg)
            return
    effects.append({
        "kind": kind,
        "turns_remaining": turns,
        "value": value,
        "tick_dmg": tick_dmg,
    })


def _remove_effect(player, kind):
    effects = player.get("effects", [])
    before = len(effects)
    player["effects"] = [e for e in effects if e.get("kind") != kind]
    return len(player["effects"]) != before


def add_status(subject, kind, turns, tick_dmg=0, value=0):
    """Public helper for adding a status effect (poison, bleeding, burn, stun, etc.).

    Stun is modeled as a `_skip_turns` counter rather than an effects-list entry,
    so a stun applied *during* a round still blocks the very next action without
    getting ticked down before it can fire.
    """
    if kind == "stun":
        subject["_skip_turns"] = subject.get("_skip_turns", 0) + turns
        return
    _add_or_refresh_effect(subject, kind, turns, value=value, tick_dmg=tick_dmg)


def has_effect(player, kind):
    return any(e.get("kind") == kind for e in player.get("effects", []))


def get_buff_value(player, kind):
    return sum(e.get("value", 0) for e in player.get("effects", []) if e.get("kind") == kind)


def tick_combat_turn(subject, subject_label="You"):
    """Apply per-round ticks: status damage, then decrement durations. Returns narration.

    `subject_label` controls narration voice: "You" for the player, the enemy's
    name for an enemy instance.
    """
    narratives = []
    is_player = subject_label == "You"
    subject_effects = subject.get("effects", [])

    for e in subject_effects:
        kind = e.get("kind")
        tick_dmg = e.get("tick_dmg", 0)
        if tick_dmg and kind in ("poison", "bleeding", "burn"):
            subject["health"] = max(0, subject["health"] - tick_dmg)
            if is_player:
                narratives.append(f"You suffer {tick_dmg} {kind} damage.")
            else:
                narratives.append(f"The {subject_label} suffers {tick_dmg} {kind} damage.")

    remaining = []
    for e in subject_effects:
        e["turns_remaining"] = e.get("turns_remaining", 0) - 1
        if e["turns_remaining"] > 0:
            remaining.append(e)
        else:
            kind = e.get("kind", "effect")
            label = kind.replace("buff_", "").replace("_", " ")
            if is_player:
                narratives.append(f"{label.capitalize()} wears off.")
            else:
                narratives.append(f"The {subject_label}'s {label} fades.")
    subject["effects"] = remaining
    return narratives


def active_effects_summary(player):
    parts = []
    for e in player.get("effects", []):
        kind = e.get("kind", "?")
        turns = e.get("turns_remaining", 0)
        value = e.get("value", 0)
        label = kind.replace("buff_", "").replace("_", " ")
        if value:
            parts.append(f"{label}+{value}({turns})")
        else:
            parts.append(f"{label}({turns})")
    return ", ".join(parts)
