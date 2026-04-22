"""NPC data + helpers. NPCs live in locations, surface as selectable POIs
during exploration, and route to role-specific interaction flows
(currently: merchant)."""


NPC_DB = {
    "morwyn_trader": {
        "id": "morwyn_trader",
        "name": "Morwyn",
        "location": "survivor_camp",
        "role": "merchant",
        "title": "weary trader",
        "disposition": "cautious",
        "greeting": (
            "\"Another one washed up, hm? Sit if you've got business — "
            "I'm Morwyn. I keep what trade I've salvaged. Coin is coin.\""
        ),
        "farewell": "\"Keep your head down out there.\"",
        "shop_inventory": [
            "healing_salve_minor",
            "healing_potion_lesser",
            "ration_pack_basic",
            "rope_hempen_10ft",
            "tinderbox",
            "antidote_simple",
            "crude_club",
            "leather_cap",
            "padded_tunic",
        ],
        "buy_multiplier": 1.0,
        "sell_multiplier": 0.5,
    },
    "brother_asche": {
        "id": "brother_asche",
        "name": "Brother Asche",
        "location": "survivor_camp",
        "role": "healer",
        "title": "soft-spoken healer",
        "disposition": "kind",
        "greeting": (
            "\"Peace, traveler. I tend what wounds I can out here — the gods saw fit to wash a "
            "few bandages up with the rest of us. Rest a while, if you've the coin.\""
        ),
        "farewell": "\"Walk gently.\"",
        "heal_cost_per_hp": 1,     # gold per HP restored
        "cure_cost": 8,            # flat gold to clear all DoT statuses
        "rest_cost": 15,           # flat gold for a supervised full rest (HP/mana/stamina + statuses)
    },
}


def npcs_at(location_id):
    """Return all NPCs currently in the given location."""
    return [n for n in NPC_DB.values() if n.get("location") == location_id]


def get(npc_id):
    return NPC_DB.get(npc_id)


def buy_price(npc, item_value):
    return max(1, int(item_value * npc.get("buy_multiplier", 1.0)))


def sell_price(npc, item_value):
    return max(1, int(item_value * npc.get("sell_multiplier", 0.5)))
