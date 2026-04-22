# Silent Symphony — TODO

Priority-ordered backlog. Top = ship-blocking / immersion-breaking; bottom = speculative.
All agents: read this before starting work. Check items off as you complete them.

## Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` done
- `[?]` proposed — needs discussion before starting

When an item is done, mark it `[x]` and leave a 1-line note if the implementation differs from the description. Delete obsolete items rather than leaving them unchecked.

---

## P0 — Bugs and immersion-breakers (fix first)

### Crashes and logic errors
- [x] `character.py:20` — fix `player_character['level' -1]` typo (string math). Crashes on first level-up. Should be `player_character['level'] - 1`.
- [x] `main.py:328` — remove `elif True:` that forces an enemy encounter on "look around generally". Restored `random.random() < 0.15` and stripped the DEBUG prints that leaked to the player. Also gated the two unconditional trap-sprung DEBUG prints at main.py:363/366 behind `config.DEBUG_MODE`.
- [x] `locations.py:63` — revert `trapped_chance: 1.0` on `beach_chest_barnacled` to a real value (~0.25). Set to 0.25.
- [x] `locations.py` — `rocky_shoreline_west` references encounter group `giant_crab_rockshore` which isn't defined in `ENCOUNTER_GROUPS`. Defined new `rocky_shoreline_creatures` group (giant_crab_rockshore 60, sea_serpent_hatchling 25, giant_sand_crab 15) and re-pointed the location at it.

### Dead code and tech debt
- [x] `ai_utils.py` — delete dead `get_ai_description` function (references nonexistent `global_generation_config`, references undefined `config.AI_MODEL_NAME`).
- [x] `config.py` — de-duplicate the two blocks that import `ai_function_declarations` (lines ~30-53 and ~66-83 do the same thing). Removed the dead `GAME_EVENT_TOOLS`/`TOOL_CONFIG` block; the later `RAW_FUNCTION_DECLARATIONS` block is the live one used by both providers.
- [x] `config.py:56` + `config.py:108` — `DEBUG_MODE = True` is set twice. Collapsed to a single env-driven `DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() in ("1","true","yes")`.
- [x] `config.py:9` — decide AI provider default; currently hardcoded `"OPENAI"` with a commented-out `os.getenv` fallback. Honor env var. Now `AI_PROVIDER = os.getenv("AI_PROVIDER", "OPENAI").upper()`.

### Project hygiene
- [x] Add `requirements.txt` (pin `python-dotenv`, `openai`, `google-genai`).
- [x] Add `.env.example` with `AI_PROVIDER`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` placeholders. Also `DEBUG_MODE`.
- [x] Add a short `README.md` with setup + run instructions.

### Immersion-breaking gaps
- [x] Consumables can't be used. Inventory UI says `[U] Use` but only `effect.heal` is handled. Wired through new `effects.apply_item_effect`: heal, restore_mana, cure_poison, cure_bleeding, buff_stamina, buff_strength (with duration), cast_spell (damage in combat, fizzle outside). `provides_dim_light`/`luck_bonus`/`magic_resistance` remain out of scope (passive trinket effects, belong with equipment-slot expansion). `readable_content` still TODO as a dedicated lore-book reader.
- [x] Save files don't migrate. Added `migrate_player` in `saveload.py` that defaults missing fields (mana/max_mana, stamina/max_stamina, effects, world_state). Called on every load.
- [x] Character creation race/origin/star-sign have zero mechanical effect. Race now grants stat mods + a trait (`game_data.RACE_TRAITS` → `player['race_trait']`; consumed in combat via elven_accuracy, low_hp_fury, mana_attuned, stout, and in `character.armor_defense_total` via armor_mastery). Origin grants a starting kit (`game_data.ORIGIN_STARTING_KIT` → inventory + gold). Star sign continues to grant the starting ability from P1. Save migration back-fills `race_trait` from race.
- [x] No way to rest/heal outside of level-up. Added "Rest" main-menu action: full HP/mana/stamina restore + clears DoT statuses. Location-safety gating (unsafe = encounter risk) deferred to P3 day/night work.

---

## P1 — Core systems wiring (content exists; hook it up)

Biggest ROI tier. Data is already in `items.py` / `entities.py`; code just needs to consume it.

### Item effect system (fix the "I have 5 potions and can't drink one" problem)
- [x] Central `apply_item_effect(player, item_id, context)` in a new `effects.py`. Handles `heal`, `restore_mana`, `cure_*`, `buff_*`, `cast_spell`, `sate_hunger`. Returns narrative + side-effects + `damage_to_enemy` + `ended_combat_turn`.
- [x] Wire "Use Item" into combat action menu. Cancellable without losing turn.
- [x] Wire consumption: remove item from inventory on use (fizzled casts aren't consumed).
- [x] Items with `uses` count down instead of being consumed. `effects.apply_item_effect` now decrements a per-item_id counter on `player['item_uses']` when an item declares `uses > 1`; the item stays in inventory until charges are exhausted and the narrative includes a "N uses remaining" line. Scaffolding works end-to-end for consumables/scrolls; the in-data multi-use items (lockpick_simple, repair_kit_basic) are `type: tool` and still lack a usage-trigger code path of their own.
- [x] `readable_content` items open a modal. New `[R] Read` hotkey in the curses inventory surfaces when the highlighted item has `readable_content`; `ui._display_readable_modal` renders the text in a full-screen, word-wrapped view that closes on any key.
- [ ] `provides_dim_light` torches change location darkness flag (belongs with equipment-slot expansion — passive equipped effect).

### Mana and stamina resources
- [x] Add `mana`, `max_mana`, `stamina`, `max_stamina` to player. Flat defaults (10/10) for now — race/origin scaling covered under P1 "Character creation matters."
- [x] Regen model: stamina refreshes +1 per combat round (silent, capped at max), +2 extra on Guard; mana refreshes on Rest. Fully restored on Rest action.
- [x] Update stats UI to show both bars + active effects summary.
- [x] Show HP/mana/stamina in inventory curses screen. New row-0 status bar in `ui.display_curses_inventory` shows HP/Mana/Stamina/Gold plus active-effect summary.

### World state (the "scripted" fix)
- [x] `player['world_state']` — nested dict: `{locations: {loc_id: {visits, pois: {poi_id: {status, ...}}, flags}}, slain_unique_enemies, flags, turn_counter}`. Helpers in new `world.py`.
- [x] Looted `loot_container` POIs marked `looted` and filtered out of the POI pool on revisit. Empty chest also marks looted (no refill without a restock timer — parked for later).
- [x] Sprung traps marked `sprung` and filtered out so they can't retrigger. Locked chests *without* a key intentionally remain un-marked and retryable.
- [x] `clue_object` → `read`, `simple_description` → `observed`, `navigation_hint` → `revealed` (with `reveals_exit_to` stored in state for future exit-unlocking).
- [x] Fixed the `can_unlock = True` hack in main.py — now real check: `player['inventory']` must contain the POI's `key_id`. With key, unlock narration prepends "Using their <key name>...".
- [x] Visit count per location — `mark_visit` bumps on initial entry and on move. Description prompt switches from `description_first_visit_prompt` to `description_revisit_prompt` on visit #2+.
- [x] Slain unique enemies — `world.mark_enemy_slain` called in combat `_award_xp_and_loot` when enemy template has `unique: True`. `get_random_enemy_for_location` filters them out of future encounter rolls. No enemies are tagged `unique` yet — scaffolding for bosses.
- [x] Save migration — `world_state` default is an empty dict; `world.ensure` builds the nested shape lazily on first touch. Old saves work without schema surgery.

### Combat expansion (turn 2-button loop into tactical)
- [x] Expand action menu: now `Attack`, `Ability`, `Use Item`, `Guard`, `Flee`.
- [x] `Guard` action: halves incoming damage, restores +2 stamina. (Consumed on use; bypassed by `bypasses_defense` specials.)
- [x] Ability system: data-driven in `abilities.py` (fire_dart, gust, invigorate, shadow_strike, warcry). Player has `known_abilities` list. Abilities have mana/stamina costs + affordability check + cancel option. `Ability` action in combat menu calls `ABILITIES[id]['handler']`.
- [x] Hit rolls — base 85% hit, +5% per weapon `accuracy_bonus`, capped 98%. Enemy basic attack also rolls (85%); specials skip hit rolls. Misses narrate on both sides.
- [x] Status effects — `poison`, `bleeding`, `burn` tick per round (damage + duration). `stun` implemented via `_skip_turns` counter so applying mid-round still blocks the very next action. `cure_poison`/`cure_bleeding` removes them. Enemy-side statuses also tick (so fire_dart burn damages enemies).
- [x] Wire enemy `special_attack` field — handlers in `enemy_specials.py` (poison_bite, slam_stun, ember_burst, tail_spikes, precise_shot, rending_claw). Supports legacy `special_attack` string (30% chance) and new `special_attacks: [{id, chance}]` list. 6 enemies now have specials: giant_sand_crab, bandit_archer, sand_viper, desert_scorpion_giant, giant_crab_rockshore, sea_serpent_hatchling (plus legacy venomous_snake, manticore_young).
- [x] Crit system — natural 6 on 1d6 crits for player attacks; enemy crits when raw roll equals `attack_max`. 1.5x damage and distinct narration ("CRITICAL HIT!" / "A savage blow!").

### Character creation matters
- [x] Star sign → 1 starting ability. All 10 signs mapped in `abilities.STAR_SIGN_STARTING_ABILITY` to one of fire_dart/gust/invigorate/shadow_strike/warcry. Announced post-creation and surfaced in the Stats view.
- [x] Race → stat modifier + one passive trait. Covered by `game_data.RACE_TRAITS`: Human +mana/stam; Orc +HP / `low_hp_fury`; Naiad +mana / `river_born` (flag for future thirst); Elf +mana+stam / `elven_accuracy`; Dwarf +HP / `armor_mastery`; Maithar +mana / `mana_attuned`; Urthar +stam / `stout`. Traits consumed in `combat.py` and `character.armor_defense_total`.
- [x] Origin → starting inventory. `game_data.ORIGIN_STARTING_KIT`: Lowborn (tarnished coin), Highborn (25g purse), Rural (rations + flint + 3g), Marauder (wooden club + 1g).

### Weapon/armor richer traits
- [x] `reach` — round 1, if player wields a reach weapon, enemy counterattack is skipped (free opening exchange).
- [x] `accuracy_bonus` — +5% hit per point, feeds player hit rolls.
- [x] `magic_bonus` — staves boost scroll `cast_spell.damage` and abilities flagged `magic_scales` (fire_dart, gust).
- [x] `magic_resistance` — reduces magical/elemental damage (abilities/specials with `damage_type != 'physical'`). Drawn from any equipped armor/shield with `effect.magic_resistance`. Bypasses the physical armor path entirely.
- [x] Multi-slot armor — player now has `equipped_head`/`_chest`/`_legs`/`_hands`/`_feet`, each summing into total defense. `character.slot_for_item` routes equip hotkey, inventory UI uses it. Save migration moves legacy `equipped_armor` into `equipped_chest`.

---

## P2 — AI as reasoning engine (the "dynamic" lever)

### Richer AI function toolkit
- [ ] `reveal_clue(clue_id, narrative)` — AI chooses which defined clue to surface based on context. (Blocked on a clue database; park until quests land in P3.)
- [x] `offer_choice(setup_narrative, choices[])` — AI authors 2–3 options with pre-written outcomes; engine asks player to pick; prints the chosen outcome. Schema in `ai_function_declarations.py`; handler `_handle_offer_choice` in `main.py`; dispatched for both providers.
- [x] `skill_check(difficulty, description, success_narrative, failure_narrative)` — AI commits both branches; engine rolls 1d10 vs difficulty (1–10). Handler `_handle_skill_check` in `main.py`.
- [x] `introduce_npc(npc_id, disposition, narrative)` — declared in `ai_function_declarations.py`, dispatched on both providers via `_handle_introduce_npc`. Engine validates that the NPC exists AND currently lives at the player's location (hallucinated ids are refused), prints the narrative, logs a normal-significance event, and offers an interaction prompt that routes into `_interact_with_npc` if accepted. `ai_context._location_block` now lists NPCs-at-location so the AI only picks from valid ids.
- [x] `set_world_flag(flag_name, scope, narrative)` — tool declared; handler `_handle_set_world_flag` routes to `world.set_flag` (global or per-location scope), prints the narrative, and logs the event as significant. Dispatched on both Gemini and OpenAI.

### Context-rich prompts
- [x] Prompt builder `ai_context.build_context_prefix` assembles: character sheet (HP/mana/stamina/level/race/origin/sign), equipped gear across all slots, known abilities, active status effects, current location (name + visit count + traits + resolved POIs + local/global flags), recent events (last 6 of a 20-deep ring buffer). Fed into all 3 AI call sites (initial location desc, move desc, POI outcome).
- [x] Event logging via `ai_context.log_event`: fires on location arrival, travel, POI resolution (with status), combat won/fled/lost, and rest. Default empty list migrated in `saveload.migrate_player`.
- [x] Prompt cache the static parts. Pulled the session-invariant narrator contract into `ai_context.SYSTEM_INSTRUCTION`. OpenAI now sends it as the `system` message (auto-cached on the provider side when long enough); Gemini's `GenerativeModel` now receives it via `system_instruction=`. Per-call user prompts keep only the dynamic `=== CONTEXT ===` block. Tool schemas were already static on both providers.
- [x] Significance-tagged events (`significant`/`normal`/`minor`); context builder selects by priority — always pulls significant first, then fills with normal, then minor. Combat outcomes + trap springs + AI flag sets are `significant`; travel / POI resolution / arrival are `normal`; rest is `minor`. Old string-only event history auto-migrates to `{text, significance}` dicts on load.

### Transient AI-authored POIs
- [x] `add_flavor_poi` tool + `_maybe_generate_flavor_poi` helper. Gated by cost: 100% attempt when engine POIs exhausted, ~35% when 1–2 engine POIs already offered, skipped when 3+ are shown or no AI client is configured. AI can opt out via `narrative_outcome("none")`. Chosen ephemeral POI short-circuits Stage 3: prints `_preresolved_narrative`, skips AI re-narration and `world_state` marking. Verified: injected flavor POI appears as option 3, player selection prints pre-resolved text cleanly.

### Ambient color
- [x] Idle between-action ambient snippets. `locations.random_ambient_for(location_id)` draws from a per-location `ambient_snippets` list (hand-written for each of the 4 existing locations) and falls back to property-keyed pools (coastal, settlement, rocky_terrain, etc.). `main._maybe_show_ambient` fires before the action menu, ticking on the world turn counter with a 2-turn minimum gap and a 30% roll. Non-time-passing actions (inventory, stats, quest log) don't advance the gate.

---

## P3 — Content loops and purpose (why keep playing)

### Quests
- [x] Quest data model (id, name, steps, active/completed, trigger conditions). Lives in `quests.py`: `QUEST_DB` + `on_event(player, event_type, **payload)` dispatcher. Player state `player['quests'] = {id: {status, step_index}}`. Auto-starts and step advances are both matcher-dicts keyed on event type; steps can gate on `requires_item`.
- [x] Quest log UI — new main-menu action "View Quest Log" (slot 6). Lists active + completed quests, each with a step checklist (`[x]`/`[~]`/`[ ]`). Empty state prints a hint.
- [x] Seed quest: "Echoes of the Wreck" — auto-starts on reading the driftwood log; steps: open barnacled chest → recover `captain_log_waterlogged` → enter `survivor_camp` → speak to Morwyn (requires item). New `captain_log_waterlogged` item added to `items.py` and to the chest loot table with chance 1.0 so it's a deterministic payoff.
- [x] Seed quest: "Markings on the Log" — auto-starts on reading the driftwood log; steps: enter `coastal_dunes_edge` → investigate `dunes_skull` (used as the matching waypoint placeholder).
- [x] Payoff: bronze key → barnacled chest → captain's log → survivor camp → Morwyn. Chain lives entirely in `quests.QUEST_DB['echoes_of_the_wreck']`.

### NPCs and economy
- [x] NPC data model + `npcs.py` — `NPC_DB` keyed by id (name, location, role, title, disposition, greeting, farewell, shop_inventory, buy/sell multipliers). Helpers: `npcs_at`, `get`, `buy_price`, `sell_price`.
- [x] First hub location — "Survivor's Cove Camp" added in `locations.py`, reachable east from `coastal_dunes_edge`. 2 defined clue POIs (fire, flag), `safe: True`, empty encounter groups.
- [x] Merchant flow — NPCs surface as always-visible POIs (`_npc_pois_for`) prepended to the explore list, short-circuit into `_interact_with_npc`. Morwyn stocks 9 starter items at 1.0x buy / 0.5x sell. Buy/sell loops handle affordability, inventory updates, gold tracking, and Cancel/Back.
- [x] Healer NPC — `brother_asche` added to `npcs.NPC_DB` at `survivor_camp` with `role: "healer"`. `_healer_loop` in `main.py` offers: restore HP (1g per missing HP), cure DoT statuses (8g flat), or full rest (15g — HP/mana/stamina + clears statuses, advances 2 turns).
- [x] Currency system — `player['gold']` (default 0), displayed in Stats, save-migrated. `gold_drop: [min, max]` added to `goblin_scout` (1–4) and `bandit_archer` (3–8). Combat awards gold via `_award_xp_and_loot`.

### Time, day/night, weather
- [x] Turn counter advances on move/explore. `world.tick_turn(player)` called on Explore (1 turn), Move (1 turn), and Rest (4 turns). Healer's "Full rest" adds 2.
- [x] Day/night phase tied to turn counter — `world.current_phase(player)` resolves to dawn/day/dusk/night over a 16-turn cycle. Surfaced to the AI through the location block in `ai_context._location_block` (so narration can reflect light/time without changing engine rules). Encounter-table modulation not yet wired; park behind richer encounter groups.
- [x] Weather flag per location — `world.current_weather(player, loc_id, loc_data)` rolls from a per-location `weather_pool` (defaulted to clear/overcast/windy/foggy), persists for ~5 turns, then has a chance to reroll. Coastal locations get `stormy` in their pool. Exposed to AI context in the same location block. Encounter modifiers deferred.

### Rest system
- [x] "Rest" action available in safe locations. In `safe: True` locations (e.g. `survivor_camp`): full HP/mana/stamina + clear DoTs, 4 turns pass. In unsafe locations: 35% chance of an encounter rolled from that area's encounter groups; if no combat, partial heal (≈max/3 HP, max/2 mana, full stamina). Healer NPC offers a paid safe-rest fallback anywhere you can reach him.

---

## P4 — Procedural variety (replay layer)

### Travel events
- [ ] Small pool of contextual events triggered when moving between locations. Weighted by world_state flags (injured? storm active? low inventory?).

### Rumor / fragment system
- [ ] Reading a clue in one location unlocks a conditional POI in another. Players build understanding across areas.

### Location expansion
- [ ] `dunes_hinterland` (already referenced from `coastal_dunes_edge`).
- [ ] `shipwreck_cove` (quest destination).
- [ ] `survivor_camp` (P3 hub).
- [ ] Each new location needs: first_visit_prompt, revisit_prompt, defined_pois, encounter_groups, items_common_find, properties.

### Respawn / world breathing
- [ ] Encounter groups refresh on a slow timer so revisited areas aren't permanently empty.
- [ ] Resource POIs (seabirds/shiny) reset after N turns.

---

## Parking lot (not yet prioritized)

Ideas worth considering but not scheduled. Promote to a tier when you're ready to work on them.

- [?] Crafting — combine reagents/materials into items. Data hooks already exist (`crafting_material`, `alchemy_ingredient`, `reagent` item types).
- [?] Companions / party members with their own combat turn.
- [?] Reputation / factions (Marauder origin has obvious hooks).
- [?] Magic schools and spell learning (scrolls → permanent spells at cost).
- [?] Hunger / thirst / fatigue (would make `sate_hunger` / rations meaningful).
- [?] Dialogue trees with NPCs (vs. pure AI freeform).
- [?] Dreams / visions tied to star sign — sleeping triggers AI-narrated lore drops.
- [?] Procedural map — post-MVP, if hand-authored locations feel too limiting.
- [?] Combat log / replay — last 10 combat rounds viewable for debugging and flavor.
- [?] Controller/keyboard-friendly whole-game curses UI (currently only inventory is curses).

---

## Completed

Move items here when done so the active list stays scannable. Oldest at bottom.

_(nothing yet)_
