# --- Item Database ---
ITEM_DB = {
    "pebble_shiny": {
        "id": "pebble_shiny",
        "name": "Shiny Pebble",
        "description": "A smooth, glistening pebble. It catches the light beautifully.",
        "type": "junk", # Categories: junk, consumable, weapon, armor, quest_item, etc.
        "value": 1
    },
    "seaweed_clump": {
        "id": "seaweed_clump",
        "name": "Clump of Seaweed",
        "description": "A damp and slightly smelly clump of seaweed.",
        "type": "junk",
        "value": 0
    },
    "broken_shell": {
        "id": "broken_shell",
        "name": "Broken Shell Fragment",
        "description": "A sharp fragment from a larger seashell.",
        "type": "junk",
        "value": 0
    },
    "healing_salve_minor": {
        "id": "healing_salve_minor",
        "name": "Minor Healing Salve",
        "description": "A soothing balm that mends minor wounds.",
        "type": "consumable",
        "effects": {"heal_hp": 15}, 
        "combat_usable": True,
        "value": 10
    },
    "rusty_dagger": {
        "id": "rusty_dagger",
        "name": "Rusty Dagger",
        "description": "A small, pitted dagger. It's not much, but it's better than nothing.",
        "type": "weapon",
        "damage_bonus": 2, # Adds 2 to base attack damage
        "value": 5
    },
    "leather_scraps": {
        "id": "leather_scraps",
        "name": "Leather Scraps",
        "description": "Tough, stitched-together pieces of leather. Offers minor protection.",
        "type": "armor",
        "defense_bonus": 1, # Reduces damage taken by 1
        "value": 8
    },

    # --- NEW ITEMS START HERE ---

    # == Consumables (Potions, Food, Scrolls) ==
    "healing_potion_lesser": {
        "id": "healing_potion_lesser",
        "name": "Lesser Healing Potion",
        "description": "A common potion that restores a small amount of health.",
        "type": "consumable",
        "effects": {"heal_hp": 25}, # Increased healing value
        "combat_usable": True,
        "value": 25
    },
    "mana_potion_minor": {
        "id": "mana_potion_minor",
        "name": "Minor Mana Potion",
        "description": "A shimmering liquid that slightly restores magical energy.",
        "type": "consumable",
        "effects": {"restore_mana": 10},
        "combat_usable": True,
        "value": 20
    },
    "antidote_simple": {
        "id": "antidote_simple",
        "name": "Simple Antidote",
        "description": "A bitter brew that cures common poisons.",
        "type": "consumable",
        "effect": {"cure_poison": True},
        "value": 15
    },
    "ration_pack_basic": {
        "id": "ration_pack_basic",
        "name": "Basic Ration Pack",
        "description": "Dried meat, hardtack, and a waterskin. Enough for a day.",
        "type": "consumable",
        "effect": {"sate_hunger": 1, "heal": 3}, # Placeholder for hunger mechanic
        "value": 5
    },
    "berries_wild": {
        "id": "berries_wild",
        "name": "Wild Berries",
        "description": "A handful of juicy wild berries. Might be slightly tart.",
        "type": "consumable",
        "effect": {"heal": 2},
        "value": 2
    },
    "scroll_fire_dart": {
        "id": "scroll_fire_dart",
        "name": "Scroll of Fire Dart",
        "description": "A magical scroll that unleashes a small bolt of fire upon reading.",
        "type": "scroll",
        "effect": {"cast_spell": "fire_dart", "damage": 8},
        "value": 50
    },
    "scroll_light": {
        "id": "scroll_light",
        "name": "Scroll of Light",
        "description": "Illuminates the surroundings when read.",
        "type": "scroll",
        "effect": {"cast_spell": "light"},
        "value": 30
    },
    "stamina_draught_minor": {
        "id": "stamina_draught_minor",
        "name": "Minor Stamina Draught",
        "description": "A fizzy concoction that temporarily boosts endurance.",
        "type": "consumable",
        "effect": {"buff_stamina": 10, "duration": 60}, # Duration in seconds or turns
        "value": 40
    },
    "strength_potion_fleeting": {
        "id": "strength_potion_fleeting",
        "name": "Fleeting Strength Potion",
        "description": "Briefly enhances physical power.",
        "type": "consumable",
        "effect": {"buff_strength": 1, "duration": 30},
        "value": 45
    },
    "herbal_poultice": {
        "id": "herbal_poultice",
        "name": "Herbal Poultice",
        "description": "A mix of healing herbs to apply to wounds.",
        "type": "consumable",
        "effects": {"heal_hp": 8, "cure_bleeding": True}, # Standardized heal effect key
        "combat_usable": True,
        "value": 18
    },

    # == Weapons ==
    "short_sword_iron": {
        "id": "short_sword_iron",
        "name": "Iron Short Sword",
        "description": "A standard-issue iron short sword. Reliable and sharp.",
        "type": "weapon",
        "damage_bonus": 4,
        "value": 40
    },
    "wooden_club": {
        "id": "wooden_club",
        "name": "Wooden Club",
        "description": "A sturdy piece of wood, good for bludgeoning.",
        "type": "weapon",
        "damage_bonus": 3,
        "value": 10
    },
    "hunting_bow_simple": {
        "id": "hunting_bow_simple",
        "name": "Simple Hunting Bow",
        "description": "A basic bow for hunting small game, or less armored foes.",
        "type": "weapon",
        "damage_bonus": 3, # Assumes arrows have base damage
        "value": 30
    },
    "staff_apprentice": {
        "id": "staff_apprentice",
        "name": "Apprentice's Staff",
        "description": "A smooth wooden staff, sometimes used to channel minor magics.",
        "type": "weapon",
        "damage_bonus": 1,
        "magic_bonus": 1, # Bonus to magic power or mana
        "value": 25
    },
    "steel_dagger": {
        "id": "steel_dagger",
        "name": "Steel Dagger",
        "description": "A well-crafted steel dagger, sharper and more durable than iron.",
        "type": "weapon",
        "damage_bonus": 3,
        "value": 20
    },
    "orcish_hand_axe": {
        "id": "orcish_hand_axe",
        "name": "Orcish Hand Axe",
        "description": "A crudely made but effective axe, favored by orcish raiders.",
        "type": "weapon",
        "damage_bonus": 5,
        "value": 55
    },
    "elven_shortbow": {
        "id": "elven_shortbow",
        "name": "Elven Shortbow",
        "description": "A lightweight and gracefully curved bow of elven make.",
        "type": "weapon",
        "damage_bonus": 4,
        "accuracy_bonus": 1,
        "value": 70
    },
    "dwarven_hammer_light": {
        "id": "dwarven_hammer_light",
        "name": "Light Dwarven Hammer",
        "description": "A compact warhammer, balanced for one-handed use.",
        "type": "weapon",
        "damage_bonus": 6,
        "value": 75
    },
    "spear_common": {
        "id": "spear_common",
        "name": "Common Spear",
        "description": "A simple spear with a sharpened stone or iron tip.",
        "type": "weapon",
        "damage_bonus": 4,
        "reach": True, # Potentially for combat mechanics
        "value": 35
    },
    "sling_leather": {
        "id": "sling_leather",
        "name": "Leather Sling",
        "description": "A simple leather sling for hurling stones.",
        "type": "weapon",
        "damage_bonus": 2, # Stones might have base damage
        "value": 8
    },

    # == Armor ==
    "leather_cap": {
        "id": "leather_cap",
        "name": "Leather Cap",
        "description": "A simple cap made from boiled leather.",
        "type": "armor",
        "slot": "head",
        "defense_bonus": 1,
        "value": 15
    },
    "padded_tunic": {
        "id": "padded_tunic",
        "name": "Padded Tunic",
        "description": "A thick tunic offering minimal protection.",
        "type": "armor",
        "slot": "chest",
        "defense_bonus": 2,
        "value": 20
    },
    "wooden_shield_round": {
        "id": "wooden_shield_round",
        "name": "Round Wooden Shield",
        "description": "A basic shield made of wood, reinforced with leather.",
        "type": "shield",
        "slot": "off_hand",
        "defense_bonus": 1, # Shields might add to block chance or direct defense
        "value": 25
    },
    "iron_helmet_basic": {
        "id": "iron_helmet_basic",
        "name": "Basic Iron Helmet",
        "description": "A sturdy iron helmet offering decent head protection.",
        "type": "armor",
        "slot": "head",
        "defense_bonus": 2,
        "value": 50
    },
    "chainmail_vest": {
        "id": "chainmail_vest",
        "name": "Chainmail Vest",
        "description": "A vest made of interlocking iron rings.",
        "type": "armor",
        "slot": "chest",
        "defense_bonus": 4,
        "value": 120
    },
    "leather_gloves": {
        "id": "leather_gloves",
        "name": "Leather Gloves",
        "description": "Simple gloves for hand protection.",
        "type": "armor",
        "slot": "hands",
        "defense_bonus": 1,
        "value": 12
    },
    "leather_boots_sturdy": {
        "id": "leather_boots_sturdy",
        "name": "Sturdy Leather Boots",
        "description": "Well-made boots for travelling rough terrain.",
        "type": "armor",
        "slot": "feet",
        "defense_bonus": 1,
        "value": 18
    },
    "hide_armor_crude": {
        "id": "hide_armor_crude",
        "name": "Crude Hide Armor",
        "description": "Armor made from poorly cured animal hides.",
        "type": "armor",
        "slot": "chest",
        "defense_bonus": 3,
        "value": 45
    },
    "mage_robe_novice": {
        "id": "mage_robe_novice",
        "name": "Novice Mage Robe",
        "description": "Simple robes worn by aspiring mages, offering little physical protection.",
        "type": "armor",
        "slot": "chest",
        "defense_bonus": 1,
        "mana_regen_bonus": 0.5,
        "value": 30
    },
    "iron_greaves": {
        "id": "iron_greaves",
        "name": "Iron Greaves",
        "description": "Protective iron coverings for the lower legs.",
        "type": "armor",
        "slot": "legs",
        "defense_bonus": 2,
        "value": 60
    },

    # == Crafting Materials ==
    "iron_ore": {
        "id": "iron_ore",
        "name": "Iron Ore",
        "description": "A chunk of rock containing iron.",
        "type": "crafting_material",
        "value": 3
    },
    "copper_ore": {
        "id": "copper_ore",
        "name": "Copper Ore",
        "description": "A piece of ore rich in copper.",
        "type": "crafting_material",
        "value": 2
    },
    "timber_rough": {
        "id": "timber_rough",
        "name": "Rough Timber",
        "description": "Unprocessed wood, suitable for basic crafting.",
        "type": "crafting_material",
        "value": 1
    },
    "animal_hide_small": {
        "id": "animal_hide_small",
        "name": "Small Animal Hide",
        "description": "The hide of a small creature, can be tanned into leather.",
        "type": "crafting_material",
        "value": 4
    },
    "wolf_pelt": {
        "id": "wolf_pelt",
        "name": "Wolf Pelt",
        "description": "The furred hide of a wolf.",
        "type": "crafting_material",
        "value": 10
    },
    "spider_silk_strand": {
        "id": "spider_silk_strand",
        "name": "Spider Silk Strand",
        "description": "A single, strong strand of spider silk.",
        "type": "crafting_material",
        "value": 5
    },
    "bone_fragment": {
        "id": "bone_fragment",
        "name": "Bone Fragment",
        "description": "A shard of bone, perhaps from an animal or humanoid.",
        "type": "crafting_material",
        "value": 1
    },
    "clay_lump": {
        "id": "clay_lump",
        "name": "Lump of Clay",
        "description": "Moist clay, suitable for pottery or construction.",
        "type": "crafting_material",
        "value": 1
    },
    "flint_sharp": {
        "id": "flint_sharp",
        "name": "Sharp Flint",
        "description": "A piece of flint with a sharp edge, useful for tools or tinder.",
        "type": "crafting_material",
        "value": 2
    },
    "iron_ingot": {
        "id": "iron_ingot",
        "name": "Iron Ingot",
        "description": "A bar of smelted iron.",
        "type": "crafting_material",
        "value": 10
    },

    # == Alchemy Ingredients & Reagents ==
    "sunpetal_leaf": {
        "id": "sunpetal_leaf",
        "name": "Sunpetal Leaf",
        "description": "A bright yellow leaf that thrives in sunlight, used in healing concoctions.",
        "type": "alchemy_ingredient",
        "value": 6
    },
    "moonbloom_flower": {
        "id": "moonbloom_flower",
        "name": "Moonbloom Flower",
        "description": "A pale flower that blooms only at night, linked to mana restoration.",
        "type": "alchemy_ingredient",
        "value": 8
    },
    "shadowroot_bark": {
        "id": "shadowroot_bark",
        "name": "Shadowroot Bark",
        "description": "Dark bark from a root that grows in dim light, used in stealth potions.",
        "type": "alchemy_ingredient",
        "value": 7
    },
    "goblin_ear": {
        "id": "goblin_ear",
        "name": "Goblin Ear",
        "description": "A severed goblin ear. Gross, but some alchemists find uses for it.",
        "type": "alchemy_ingredient",
        "value": 3
    },
    "crab_chitin_fragment": {
        "id": "crab_chitin_fragment",
        "name": "Crab Chitin Fragment",
        "description": "A hard piece of a crab's shell.",
        "type": "alchemy_ingredient",
        "value": 4
    },
    "bat_wing": {
        "id": "bat_wing",
        "name": "Bat Wing",
        "description": "The leathery wing of a bat.",
        "type": "alchemy_ingredient",
        "value": 2
    },
    "crystal_shard_mundane": {
        "id": "crystal_shard_mundane",
        "name": "Mundane Crystal Shard",
        "description": "A small, clear crystal fragment with no apparent magical properties.",
        "type": "reagent",
        "value": 5
    },
    "brimstone_dust": {
        "id": "brimstone_dust",
        "name": "Brimstone Dust",
        "description": "Fine yellow powder with a sulfuric smell, used in fiery concoctions.",
        "type": "reagent",
        "value": 10
    },
    "fey_dust": {
        "id": "fey_dust",
        "name": "Fey Dust",
        "description": "Sparkling dust said to be shed by fey creatures, used in illusion magic.",
        "type": "reagent",
        "value": 20
    },
    "ectoplasm_vial": {
        "id": "ectoplasm_vial",
        "name": "Vial of Ectoplasm",
        "description": "A viscous, glowing substance, residue of a spiritual presence.",
        "type": "reagent",
        "value": 15
    },

    # == Junk (More Variety) ==
    "bent_spoon": {
        "id": "bent_spoon",
        "name": "Bent Spoon",
        "description": "An ordinary spoon, now quite bent out of shape.",
        "type": "junk",
        "value": 0
    },
    "torn_rag": {
        "id": "torn_rag",
        "name": "Torn Rag",
        "description": "A dirty, torn piece of cloth.",
        "type": "junk",
        "value": 0
    },
    "chipped_mug": {
        "id": "chipped_mug",
        "name": "Chipped Mug",
        "description": "An old ceramic mug with a large chip on the rim.",
        "type": "junk",
        "value": 0
    },
    "dull_arrowhead": {
        "id": "dull_arrowhead",
        "name": "Dull Arrowhead",
        "description": "An arrowhead too blunt to be effective.",
        "type": "junk",
        "value": 1
    },
    "fish_bones": {
        "id": "fish_bones",
        "name": "Fish Bones",
        "description": "The skeletal remains of a small fish.",
        "type": "junk",
        "value": 0
    },
    "rat_tail": {
        "id": "rat_tail",
        "name": "Rat Tail",
        "description": "A severed rat's tail. Unpleasant.",
        "type": "junk",
        "value": 0
    },
    "old_coin_tarnished": {
        "id": "old_coin_tarnished",
        "name": "Tarnished Old Coin",
        "description": "A coin so old and tarnished its origin is unclear. Likely worthless.",
        "type": "junk",
        "value": 1
    },
    "string_piece": {
        "id": "string_piece",
        "name": "Piece of String",
        "description": "A short length of ordinary string.",
        "type": "junk",
        "value": 0
    },
    "moldy_bread_crust": {
        "id": "moldy_bread_crust",
        "name": "Moldy Bread Crust",
        "description": "A hard, moldy crust of bread. Not edible.",
        "type": "junk",
        "value": 0
    },
    "rusted_nail": {
        "id": "rusted_nail",
        "name": "Rusted Nail",
        "description": "A bent and rusty nail.",
        "type": "junk",
        "value": 0
    },

    # == Valuables & Trade Goods ==
    "gem_amethyst_rough": {
        "id": "gem_amethyst_rough",
        "name": "Rough Amethyst",
        "description": "An uncut purple gemstone.",
        "type": "valuable",
        "value": 25
    },
    "silver_ring_plain": {
        "id": "silver_ring_plain",
        "name": "Plain Silver Ring",
        "description": "A simple ring made of silver.",
        "type": "valuable",
        "value": 15
    },
    "gold_nugget_small": {
        "id": "gold_nugget_small",
        "name": "Small Gold Nugget",
        "description": "A tiny nugget of natural gold.",
        "type": "valuable",
        "value": 30
    },
    "ivory_figurine_crude": {
        "id": "ivory_figurine_crude",
        "name": "Crude Ivory Figurine",
        "description": "A small, roughly carved figurine made of ivory.",
        "type": "valuable",
        "value": 40
    },
    "spices_exotic_pouch": {
        "id": "spices_exotic_pouch",
        "name": "Pouch of Exotic Spices",
        "description": "A small pouch filled with fragrant, rare spices.",
        "type": "trade_good",
        "value": 75
    },
    "silk_bolt_common": {
        "id": "silk_bolt_common",
        "name": "Bolt of Common Silk",
        "description": "A bolt of decent quality silk fabric.",
        "type": "trade_good",
        "value": 60
    },
    "ancient_tome_cover": {
        "id": "ancient_tome_cover",
        "name": "Ancient Tome Cover",
        "description": "The ornate but damaged cover of a very old book.",
        "type": "valuable",
        "value": 20
    },
    "pearl_small": {
        "id": "pearl_small",
        "name": "Small Pearl",
        "description": "A lustrous pearl, likely from a freshwater mussel.",
        "type": "valuable",
        "value": 50
    },
    "obsidian_shard": {
        "id": "obsidian_shard",
        "name": "Obsidian Shard",
        "description": "A sharp piece of volcanic glass.",
        "type": "valuable", # Can also be a crafting material
        "value": 10
    },
    "copper_goblet": {
        "id": "copper_goblet",
        "name": "Copper Goblet",
        "description": "A simple drinking goblet made of copper.",
        "type": "valuable",
        "value": 8
    },

    # == Tools ==
    "lockpick_simple": {
        "id": "lockpick_simple",
        "name": "Simple Lockpick",
        "description": "A crudely fashioned lockpick. Prone to breaking.",
        "type": "tool",
        "uses": 3, # Example of limited uses
        "value": 10
    },
    "torch_unlit": {
        "id": "torch_unlit",
        "name": "Unlit Torch",
        "description": "A piece of wood tipped with flammable material. Needs a light source.",
        "type": "tool",
        "value": 2
    },
    "fishing_rod_basic": {
        "id": "fishing_rod_basic",
        "name": "Basic Fishing Rod",
        "description": "A simple rod and line for fishing.",
        "type": "tool",
        "value": 15
    },
    "pickaxe_worn": {
        "id": "pickaxe_worn",
        "name": "Worn Pickaxe",
        "description": "A pickaxe that has seen better days, but still usable for mining.",
        "type": "tool",
        "value": 20
    },
    "shovel_rusty": {
        "id": "shovel_rusty",
        "name": "Rusty Shovel",
        "description": "A rusty shovel, good for digging shallow holes.",
        "type": "tool",
        "value": 12
    },
    "mortar_pestle_stone": {
        "id": "mortar_pestle_stone",
        "name": "Stone Mortar and Pestle",
        "description": "A heavy stone set for grinding herbs and minerals.",
        "type": "tool",
        "value": 25
    },
    "tinderbox": {
        "id": "tinderbox",
        "name": "Tinderbox",
        "description": "Contains flint, steel, and tinder to start a fire.",
        "type": "tool",
        "value": 8
    },
    "rope_hempen_10ft": {
        "id": "rope_hempen_10ft",
        "name": "10ft Hempen Rope",
        "description": "A 10-foot length of sturdy hempen rope.",
        "type": "tool",
        "value": 5
    },
    "empty_waterskin": {
        "id": "empty_waterskin",
        "name": "Empty Waterskin",
        "description": "A leather waterskin, currently empty.",
        "type": "tool", # Can be filled
        "value": 3
    },
    "repair_kit_basic": {
        "id": "repair_kit_basic",
        "name": "Basic Repair Kit",
        "description": "A few tools and scraps for minor equipment repairs.",
        "type": "tool",
        "uses": 1,
        "value": 30
    },

    # == Quest Items (Examples - these would be tied to specific quests) ==
    "hermits_lost_locket": {
        "id": "hermits_lost_locket",
        "name": "Hermit's Lost Locket",
        "description": "A small, tarnished silver locket. Seems important to someone.",
        "type": "quest_item",
        "value": 0 # Quest items typically have no resale value or are priceless to the quest giver
    },
    "sealed_message_for_captain": {
        "id": "sealed_message_for_captain",
        "name": "Sealed Message for the Captain",
        "description": "A rolled parchment sealed with an unfamiliar crest.",
        "type": "quest_item",
        "value": 0
    },
    "rare_herb_sunpetal_prime": {
        "id": "rare_herb_sunpetal_prime",
        "name": "Prime Sunpetal Leaf",
        "description": "An unusually vibrant and potent Sunpetal leaf.",
        "type": "quest_item",
        "value": 0
    },
    "goblin_chieftains_medallion": {
        "id": "goblin_chieftains_medallion",
        "name": "Goblin Chieftain's Medallion",
        "description": "A crudely made but imposing medallion, taken from a goblin leader.",
        "type": "quest_item",
        "value": 0
    },
    "ancient_artifact_fragment_A": {
        "id": "ancient_artifact_fragment_A",
        "name": "Ancient Artifact Fragment (A)",
        "description": "A piece of a larger, unknown ancient artifact. It hums faintly.",
        "type": "quest_item",
        "value": 0
    },

    # == Books & Notes (Readable for lore/hints, some might give XP or skill) ==
    "journal_page_ripped": {
        "id": "journal_page_ripped",
        "name": "Ripped Journal Page",
        "description": "A torn page from a journal, detailing a narrow escape.",
        "type": "book", # Or 'note'
        "readable_content": "Path was blocked... giant spiders... found a small crevice behind the waterfall...",
        "value": 5
    },
    "local_area_map_crude": {
        "id": "local_area_map_crude",
        "name": "Crude Local Area Map",
        "description": "A hand-drawn map of the immediate surroundings. Some areas marked 'DANGER'.",
        "type": "book",
        "readable_content": "Map shows a cave to the north, a ruined tower to the east.",
        "value": 10
    },
    "alchemy_basics_primer": {
        "id": "alchemy_basics_primer",
        "name": "Alchemy Basics: A Primer",
        "description": "A thin booklet covering the very basics of alchemy.",
        "type": "book",
        "readable_content": "Discusses Sunpetal for healing and Moonbloom for mana.",
        "skill_gain": {"alchemy": 1}, # Example of skill gain
        "value": 50
    },
    "tales_of_gaiatheia_vol1": {
        "id": "tales_of_gaiatheia_vol1",
        "name": "Tales of Gaiatheia, Vol. 1",
        "description": "A collection of local legends and folklore.",
        "type": "book",
        "readable_content": "Contains the story of the Sunken City and the Whispering Plains.",
        "value": 20
    },
    "note_smudged_warning": {
        "id": "note_smudged_warning",
        "name": "Smudged Warning Note",
        "description": "A hastily written note, smudged and hard to read. '...beware the shadows in the old mill...'",
        "type": "book",
        "readable_content": "Mentions a hidden danger in an old mill.",
        "value": 2
    },

    # == Magical Trinkets & Charms (Minor passive effects or unique properties) ==
    "charm_of_minor_warding": {
        "id": "charm_of_minor_warding",
        "name": "Charm of Minor Warding",
        "description": "A small carved stone that seems to faintly shimmer, offering slight magical protection.",
        "type": "trinket",
        "effect": {"magic_resistance": 1},
        "value": 75
    },
    "lucky_horseshoe_tarnished": {
        "id": "lucky_horseshoe_tarnished",
        "name": "Tarnished Lucky Horseshoe",
        "description": "An old, tarnished horseshoe. Some believe it brings good fortune.",
        "type": "trinket",
        "effect": {"luck_bonus": 1}, # Could affect loot drops or critical hits
        "value": 50
    },
    "glowing_ember_pendant": {
        "id": "glowing_ember_pendant",
        "name": "Glowing Ember Pendant",
        "description": "A pendant with a stone that glows with a faint, warm light. Provides minimal illumination.",
        "type": "trinket",
        "effect": {"provides_dim_light": True},
        "value": 60
    },
    "naiad_scale_shimmering": {
        "id": "naiad_scale_shimmering",
        "name": "Shimmering Naiad Scale",
        "description": "A single, beautiful scale that glimmers with aquatic colors. Feels cool to the touch.",
        "type": "trinket", # Could also be an alchemy ingredient
        "effect": {"water_breathing_short": True}, # e.g., for 30 seconds if equipped/activated
        "value": 100
    },
    "ring_of_lesser_regeneration": {
        "id": "ring_of_lesser_regeneration",
        "name": "Ring of Lesser Regeneration",
        "description": "A simple band that slowly mends minor injuries over time.",
        "type": "trinket",
        "slot": "ring", # If rings are equippable
        "effect": {"health_regen_per_minute": 1},
        "value": 150
    },
    "small_tarnished_bronze_key": {
        "id": "small_tarnished_bronze_key",
        "name": "Small Tarnished Bronze Key",
        "description": "A small, old bronze key, covered in a layer of green tarnish. It looks like it might unlock a small box or old lock.",
        "type": "key_item", # Or quest_item, or a new type "key"
        "value": 5 
    },
    # --- END OF NEW ITEMS (100 added) ---
}