"""
Forbidden Stars — полная база данных юнитов, карт и приказов
============================================================
Структура данных:
  FACTIONS         — словарь фракций с вложенными данными
  get_faction()    — получить данные одной фракции
  get_unit()       — найти юнит по имени (поиск по всем фракциям)
  get_combat_card()— найти боевую карту по имени
  search()         — текстовый поиск по всей базе

Условные обозначения (иконки):
  [?]  — случайный результат кубика
  [G]  — атака / offence
  [S]  — щит / defence
  [M]  — моральный дух / aquila
  (g)  — жетон атаки
  (s)  — жетон щита
  (R)  — жетон подкрепления
  (F)  — жетон кузницы
"""

# ---------------------------------------------------------------------------
# Вспомогательные константы
# ---------------------------------------------------------------------------

STRUCTURES = {
    "Factory": {"cost": 2, "dice": None, "health": None, "morale": None, "capacity": 1},
    "City":    {"cost": 3, "dice": None, "health": None, "morale": None, "capacity": None},
    "Bastion": {"cost": 2, "dice": 2,    "health": 3,    "morale": 2,    "capacity": None},
}

# ---------------------------------------------------------------------------
# Основная база данных фракций
# ---------------------------------------------------------------------------

FACTIONS = {

    # ═══════════════════════════════════════════════════════════════════════
    "Space Marines": {
        "dominate_action": (
            "Spend 1 materiel to upgrade a Scout to a Space Marine, "
            "or a Space Marine to a Land Raider, in active system."
        ),

        # ── Юниты ──────────────────────────────────────────────────────────
        # Поля: tier, cost, dice, health, morale, starting_qty, max_qty
        "units": {
            "Scout": {
                "tier": 0, "cost": 2, "dice": 1, "health": 2,
                "morale": 2, "starting_qty": 4, "max_qty": 6,
            },
            "Strike Cruiser": {
                "tier": 0, "cost": 2, "dice": 2, "health": 2,
                "morale": 2, "starting_qty": 1, "max_qty": 3,
            },
            "Space Marine": {
                "tier": 1, "cost": 3, "dice": 2, "health": 3,
                "morale": 3, "starting_qty": 1, "max_qty": 6,
            },
            "Land Raider": {
                "tier": 2, "cost": 4, "dice": 3, "health": 4,
                "morale": 3, "starting_qty": None, "max_qty": 6,
            },
            "Battle Barge": {
                "tier": 2, "cost": 5, "dice": 4, "health": 5,
                "morale": 4, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
            "Warlord Titan": {
                "tier": 3, "cost": 5, "dice": 3, "health": 5,
                "morale": 4, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
        },

        # ── Боевые карты ────────────────────────────────────────────────────
        # Поля: tier, cost, icons{G,S,M}, requires, effect
        "combat_cards": {
            "Ambush": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": ["Scout", "Strike Cruiser"],
                "effect": "When enemy is routed this round, must spend [M] or be destroyed.",
            },
            "Blessed Power Armour": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": ["Bastion", "Space Marine", "Strike Cruiser"],
                "effect": "Convert up to 2 dice to [S].",
            },
            "Faith in the Emperor": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": ["Scout", "Space Marine", "Strike Cruiser"],
                "effect": "Rally 1 unit or gain 1 [M].",
            },
            "Fury of the Ultramar": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": ["Space Marine", "Strike Cruiser"],
                "effect": "Force enemy to lose 1 [S] or 2 (s).",
            },
            "Reconnaissance": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": ["Scout", "Strike Cruiser"],
                "effect": "Spend 1 [M] to retreat 1 unit.",
            },
            "Drop Pod Assault": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": ["Space Marine"],
                "effect": "Spend 1 [M] to take 1 scout or 1 marine from any world to this world.",
            },
            "Glory and Death": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 0, "M": 1},
                "requires": ["Space Marine", "Strike Cruiser"],
                "effect": "Force enemy to lose 1 [S] or 1 [M].",
            },
            "Hold the Line": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 1, "M": 1},
                "requires": ["Bastion", "Space Marine", "Strike Cruiser"],
                "effect": "Gain 1 [S] or 1 [M].",
            },
            "Veteran Scouts": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": ["Scout", "Strike Cruiser"],
                "effect": "Spend any [M]; retreat 1 unit per die.",
            },
            "Armoured Advance": {
                "tier": 2, "cost": 4,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["Land Raider", "Battle Barge"],
                "effect": "Resolve 1 additional assess damage step this round (including tokens etc).",
            },
            "Break the Line": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 2, "M": 0},
                "requires": ["Land Raider", "Battle Barge"],
                "effect": "Enemy choses 1 face up combat card to discard.",
            },
            "Show No Fear": {
                "tier": 2, "cost": 4,
                "icons": {"G": 0, "S": 2, "M": 1},
                "requires": ["Bastion", "Space Marine", "Strike Cruiser"],
                "effect": "Spend 1 [M] rally all units.",
            },
            "Emperor's Glory": {
                "tier": 3, "cost": 6,
                "icons": {"G": 0, "S": 2, "M": 2},
                "requires": ["Warlord Titan", "Battle Barge"],
                "effect": "Rally all units. Convert any dice to [M].",
            },
            "Emperor's Might": {
                "tier": 3, "cost": 6,
                "icons": {"G": 3, "S": 0, "M": 0},
                "requires": ["Warlord Titan", "Battle Barge"],
                "effect": "Spend any [G]; gain 2 (g) per die.",
            },
        },

        # ── Улучшенные приказы ──────────────────────────────────────────────
        "enhanced_orders": [
            {"tier": 0, "name": "Reign of Fire",       "cost": 1, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Crusade",              "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 1, "name": "Direct the Faithful",  "cost": 2, "order": "Strategize", "limit": "Once per round"},
            {"tier": 1, "name": "Recruitment Worlds",   "cost": 2, "order": "Deploy",     "limit": "Once per round"},
            {"tier": 2, "name": "Drop Pods",            "cost": 3, "order": "Advance",    "limit": "Orbital Strike, once per round"},
        ],

        # ── Карты событий ───────────────────────────────────────────────────
        "event_cards": [
            {"name": "Adeptus Mechanicus",   "type": "Scheme", "effect": "Gain [?], convert 1 [M] into [G]."},
            {"name": "Emperor's Champion",   "type": "Scheme", "effect": "If no friendly worlds in system, gain 1 (R)."},
            {"name": "Exterminatus",         "type": "Scheme", "effect": "May change 1 structure to a different structure."},
            {"name": "Heroic Intervention",  "type": "Tactic", "effect": "Treat Bastions as Factories, lower deployment limit by 1 each."},
            {"name": "Marines",              "type": "Tactic", "effect": "Bastions do not prevent orbital strike. Spend 2 [S] to place free Marine (may start combat)."},
            {"name": "Rites of Battle",      "type": "Scheme", "effect": "At start of assess damage, discard to gain 2 (s), plus 1 (s) per (F) you have."},
            {"name": "The Emperor Protects", "type": "Scheme", "effect": "At start of assess damage, discard to rally 1 unit."},
            {"name": "Unwavering Resolve",   "type": "Scheme", "effect": "Before orbital strike, discard to convert all dice to [G]."},
            {"name": "Work of the Righteous","type": "Tactic", "effect": "Place free Marine on friendly structure or free Scout on any friendly world."},
            {"name": "— (Purchase order upgrade)", "type": "Tactic", "effect": "Purchase 1 order upgrade, reduce by 1 materiel per Bastion."},
            {"name": "— (Place Bastion)",    "type": "Tactic", "effect": "Place Bastion on friendly world. Free if no other structure, otherwise cost 2 materiel."},
            {"name": "— (Rally all)",        "type": "Scheme", "effect": "Instead of revealing an order, discard to rally all units in a system."},
            {"name": "— (Gain assets)",      "type": "Tactic", "effect": "Gain assets or materiel from a friendly world."},
        ],

        # ── Warp Storm Move таблица ─────────────────────────────────────────
        "warp_storm_moves": {
            "Across":             "Gain 2 [?].",
            "Sideways":           "Gain 2 [?].",
            "Top Right/Bottom Left": "Gain 2 [?].",
            "Top Left/Bottom Right": "Gain 2 [?].",
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    "Chaos Space Marines": {
        "dominate_action": (
            "Take 1 cultist from active system and place on friendly or "
            "uncontested world in adjacent system."
        ),

        "units": {
            "Cultist": {
                "tier": 0, "cost": 2, "dice": 1, "health": 2,
                "morale": 2, "starting_qty": 2, "max_qty": 9,
            },
            "Iconoclast Destroyer": {
                "tier": 0, "cost": 2, "dice": 2, "health": 2,
                "morale": 2, "starting_qty": 1, "max_qty": 3,
            },
            "Chaos Marine": {
                "tier": 1, "cost": 3, "dice": 3, "health": 3,
                "morale": 2, "starting_qty": 2, "max_qty": 6,
            },
            "Helbrute": {
                "tier": 2, "cost": 4, "dice": 3, "health": 4,
                "morale": 3, "starting_qty": None, "max_qty": 3,
            },
            "Repulsive Cruiser": {
                "tier": 2, "cost": 5, "dice": 4, "health": 5,
                "morale": 4, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
            "Chaos Reaver Titan": {
                "tier": 3, "cost": 5, "dice": 4, "health": 5,
                "morale": 3, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
        },

        "combat_cards": {
            "Dark Faith": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": ["Cultist", "Iconoclast Destroyer"],
                "effect": "If more [M] than enemy, place free Cultist on another friendly or uncontrolled world in system.",
            },
            "Foul Worship": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": ["Cultist", "Iconoclast Destroyer"],
                "effect": "If enemy has routed unit, gain 1 (s) per unrouted Cultist or Iconoclast.",
            },
            "Impure Zeal": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": ["Cultist", "Iconoclast Destroyer"],
                "effect": "Enemy routs 1 unit, or you gain 1 (g) per unrouted Cultist or Iconoclast.",
            },
            "Khorne's Rage": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Chaos Marine", "Iconoclast Destroyer"],
                "effect": "Enemy spends 1 [S] or routs unit of his choosing.",
            },
            "Lure of Chaos": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": ["Cultist", "Iconoclast Destroyer"],
                "effect": "Gain 2 (g) or 2 (s).",
            },
            "Mark of Khorne": {
                "tier": 0, "cost": 2,
                "icons": {"G": 2, "S": 0, "M": 0},
                "requires": ["Chaos Marine", "Iconoclast Destroyer"],
                "effect": "Enemy spends 1 [S] or destroys 1 routed unit.",
            },
            "Mark of Nurgle": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 2, "M": 0},
                "requires": ["Chaos Marine", "Iconoclast Destroyer"],
                "effect": "Enemy destroys 1 routed unit, otherwise gain 2 (s).",
            },
            "Mark of Slaanesh": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": ["Chaos Marine"],
                "effect": "If enemy has routed unit, place free Cultist on this world.",
            },
            "Mark of Tzeentch": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 0, "M": 2},
                "requires": ["Chaos Marine", "Iconoclast Destroyer"],
                "effect": "Convert up to 2 [M] to [G] and/or [S].",
            },
            "Chaos United": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": ["Cultist", "Chaos Marine", "Helbrute"],
                "effect": "Take 1 unit from any world and place on this world. Command level cannot exceed number of Cultists in system.",
            },
            "Daemonic Resilience": {
                "tier": 2, "cost": 4,
                "icons": {"G": 0, "S": 2, "M": 1},
                "requires": ["Helbrute", "Repulsive Cruiser"],
                "effect": "Gain 4 (s) unless enemy destroys 1 unit of his choice.",
            },
            "Inhuman Strength": {
                "tier": 2, "cost": 4,
                "icons": {"G": 2, "S": 0, "M": 1},
                "requires": ["Helbrute", "Repulsive Cruiser"],
                "effect": "Destroy 1 unit to gain 4 (g).",
            },
            "Chaos Victorious": {
                "tier": 3, "cost": 6,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": ["Chaos Reaver Titan", "Repulsive Cruiser"],
                "effect": "Rout 1 enemy unit.",
            },
            "Death and Despair": {
                "tier": 3, "cost": 6,
                "icons": {"G": 2, "S": 0, "M": 1},
                "requires": ["Chaos Reaver Titan", "Repulsive Cruiser"],
                "effect": "If more [M] than enemy, destroy 1 routed unit.",
            },
        },

        "enhanced_orders": [
            {"tier": 0, "name": "Fear from Above",        "cost": 1, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Dread Ritual",            "cost": 2, "order": "Deploy",     "limit": "Once per round"},
            {"tier": 1, "name": "Favour of the Dark Gods", "cost": 2, "order": "Strategize", "limit": "Once per round"},
            {"tier": 1, "name": "From the Warp",           "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 2, "name": "Complete Destruction",    "cost": 3, "order": "Advance",    "limit": "Orbital Strike, once per round"},
        ],

        "event_cards": [
            {"name": "Blight of Nurgle",       "type": "Scheme", "effect": "Gain [?], spend 1 [M] to force any unit taking damage to rout."},
            {"name": "Incantation of Tzeentch","type": "Tactic", "effect": "Purchase 1 Tier 0-2 unit; reduce cost by 1 per Cultist in active system. Factory not required."},
            {"name": "Prayer to the Dark Gods","type": "Scheme", "effect": "Place 2 order tokens from play area onto top of event deck."},
            {"name": "Prophets and Signs",     "type": "Tactic", "effect": "Ships can move through Warp Storms."},
            {"name": "Seduced by Chaos",       "type": "Scheme", "effect": "Instead of playing an order, discard to rout an enemy unit in a system containing 1+ of your units."},
            {"name": "Spoils of War",          "type": "Tactic", "effect": "Draw 3 cards from Event Deck, choose 1 and resolve its ability (not Warp Storm move)."},
            {"name": "Through the Warp",       "type": "Scheme", "effect": "When a player moves a Warp Storm, discard to prevent this, and move in any direction."},
            {"name": "Touched by the Warp",    "type": "Tactic", "effect": "Place 2 free Cultists on friendly world not containing Cultists, or 1 free Cultist on any friendly world."},
            {"name": "— (Rout at end of damage)", "type": "Scheme", "effect": "At end of assess damage in a Chaos combat, discard to rout 1 unit in combat."},
            {"name": "— (Gain F and R)",       "type": "Tactic", "effect": "Gain 1 (F) and 1 (R)."},
            {"name": "— (Move through Warp)",  "type": "Scheme", "effect": "When resolving Advance Order, discard to allow units to move through Warp Storms. If combat occurs, gain 1 [M] at start."},
            {"name": "— (Tier upgrade card)",  "type": "Tactic", "effect": "Destroy 1 Cultist to gain 1 upgrade card. Tier cannot exceed number of Warp Storms bordering the system."},
        ],

        "warp_storm_moves": {
            "Across":                "Bastions do not prevent orbital strike. Spend 2 [S] to force enemy to choose unit or structure to destroy.",
            "Sideways":              "Ships can move through Warp Storms.",
            "Top Right/Bottom Left": "Gain 2 [G] or 2 [M]. Spend any [M], each destroys 1 Tier 0 unit.",
            "Top Left/Bottom Right": "Gain 2 [?]. If more [M] than enemy, rout all his Tier 0 units.",
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    "Orks": {
        "dominate_action": "Purchase 1 unit and place it on a world in the active system.",

        "units": {
            "Ork Boyz": {
                "tier": 0, "cost": 2, "dice": 2, "health": 2,
                "morale": 1, "starting_qty": 4, "max_qty": 9,
            },
            "Onslaught Attack Ships": {
                "tier": 0, "cost": 2, "dice": 1, "health": 3,
                "morale": 2, "starting_qty": None, "max_qty": 3,
            },
            "Nobz": {
                "tier": 1, "cost": 3, "dice": 2, "health": 4,
                "morale": 2, "starting_qty": 1, "max_qty": 6,
            },
            "Battlewagons": {
                "tier": 2, "cost": 4, "dice": 3, "health": 5,
                "morale": 3, "starting_qty": None, "max_qty": 3,
            },
            "Kill Kroozers": {
                "tier": 2, "cost": 5, "dice": 3, "health": 6,
                "morale": 4, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
            "Gargants": {
                "tier": 3, "cost": 5, "dice": 3, "health": 6,
                "morale": 3, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1, "R": 1},
            },
        },

        "combat_cards": {
            "'Ard Boyz": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 2, "M": 0},
                "requires": ["Ork Boyz"],
                "effect": "Enemy must reroll 1 [G] for each unrouted Boyz.",
            },
            "Gretchin": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 0},
                "requires": ["Onslaught Attack Ships"],
                "effect": "Destroy 1 Onslaught to force enemy to choose & destroy one of his units.",
            },
            "Mek Boyz": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": ["Ork Boyz", "Onslaught Attack Ships"],
                "effect": "Enemy discards top card of his combat deck. You gain the cards combat icons until end of this execution round.",
            },
            "Shoota Boyz": {
                "tier": None, "cost": None,
                "icons": {"G": 2, "S": 0, "M": 0},
                "requires": ["Ork Boyz"],
                "effect": "Enemy must reroll 1 [S] for each unrouted Boyz.",
            },
            "Slugga Boyz": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": ["Ork Boyz", "Onslaught Attack Ships"],
                "effect": "Rally 1 unit.",
            },
            "Biker Nobz": {
                "tier": 0, "cost": 2,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["Nobz", "Onslaught Attack Ships"],
                "effect": "Gain 1 (g).",
            },
            "Mega Nobz": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 2, "M": 0},
                "requires": ["Nobz", "Onslaught Attack Ships"],
                "effect": "Gain 1 (s).",
            },
            "Sea of Green": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": [],
                "effect": "-",
            },
            "Waaagh!!!!": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 0, "M": 3},
                "requires": ["Ork Boyz", "Onslaught Attack Ships"],
                "effect": "Gain 1 (g) per unrouted Boyz/Onslaught.",
            },
            "Party Wagon": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 2, "M": 0},
                "requires": ["Battlewagons", "Kill Kroozers"],
                "effect": "If you have more unrouted units, gain 2 (g) and 2 (s).",
            },
            "Rokkit Wagon": {
                "tier": 2, "cost": 4,
                "icons": {"G": 3, "S": 0, "M": 0},
                "requires": ["Battlewagons", "Kill Kroozers"],
                "effect": "Gain 3 (g). Enemy may retreat 1 unit.",
            },
            "Weirdboyz": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": ["Ork Boyz", "Onslaught Attack Ships"],
                "effect": "In this combat, each time enemy gets (g) or (s), you gain the same tokens as well.",
            },
            "Smasher Gargant": {
                "tier": 3, "cost": 6,
                "icons": {"G": 2, "S": 3, "M": 0},
                "requires": ["Gargants", "Kill Kroozers"],
                "effect": "Choose enemy unit. Destroy unit unless enemy spends dice equal to its Tier.",
            },
            "Snapper Gargant": {
                "tier": 3, "cost": 6,
                "icons": {"G": 4, "S": 1, "M": 0},
                "requires": ["Gargants", "Kill Kroozers"],
                "effect": "Discard 1 of enemy face up combat cards.",
            },
        },

        "enhanced_orders": [
            {"tier": 0, "name": "Lootin'",      "cost": 1, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Werk Fasta!",  "cost": 2, "order": "Deploy",     "limit": "Once per round"},
            {"tier": 1, "name": "The Green Tide","cost": 2, "order": "Strategize", "limit": "Once per round"},
            {"tier": 0, "name": "Ork Roks",     "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 2, "name": "Stealin'!",    "cost": 3, "order": "Advance",    "limit": "Orbital Strike, once per round"},
        ],

        "event_cards": [
            {"name": "Gitz Dem!",       "type": "Scheme", "effect": "When an enemy unit routs in combat, discard to destroy that unit."},
            {"name": "How We Getz Here?","type": "Tactic","effect": "Take 1 unit from any world and place on any uncontrolled world."},
            {"name": "Letz Get Fightin'","type": "Tactic","effect": "Gain 2 materiel. Choose a player to lose 1 asset of your choice."},
            {"name": "Lootin' 'n Stealin'","type": "Tactic","effect": "Gain 2 (R)."},
            {"name": "Moar Boyz!",      "type": "Tactic", "effect": "Instead of revealing Order, discard to resolve an Advance Order in a system with at least 2 of your own units."},
            {"name": "Mob Up!",         "type": "Scheme", "effect": "End of assess damage step in Ork combat, discard to destroy 1 structure on that world."},
            {"name": "Teer it Down!",   "type": "Scheme", "effect": "Either place 2 free Boyz on a world containing a Nob, or 1 free Boyz on a friendly world."},
            {"name": "Warboss",         "type": "Scheme", "effect": "When purchasing, reduce cost by 1 per (R) you have."},
        ],

        "warp_storm_moves": {
            "Across":                "Can move up to 2 units though 1 uncontrolled void as if it were a friendly area.",
            "Sideways":              "Bastions do not prevent orbital strike. Spend 1 [M] to discard an enemy asset token; you gain that token.",
            "Top Right/Bottom Left": "May purchase structure before purchasing units.",
            "Top Left/Bottom Right": "When revealed, can resolve it as one of the other orders instead.",
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    "Eldar": {
        "dominate_action": (
            "Take 1 unit from a world in the active system, and place it on any friendly world."
        ),

        "units": {
            "Aspect Warriors": {
                "tier": 0, "cost": 2, "dice": 2, "health": 1,
                "morale": 2, "starting_qty": 3, "max_qty": 6,
            },
            "Hellebore Frigates": {
                "tier": 0, "cost": 2, "dice": 3, "health": 2,
                "morale": 1, "starting_qty": 2, "max_qty": 6,
            },
            "Wraithguard": {
                "tier": 1, "cost": 3, "dice": 2, "health": 4,
                "morale": 2, "starting_qty": 1, "max_qty": 3,
            },
            "Falcons": {
                "tier": 2, "cost": 4, "dice": 3, "health": 4,
                "morale": 3, "starting_qty": None, "max_qty": 3,
            },
            "Void Stalkers": {
                "tier": 2, "cost": 5, "dice": 4, "health": 5,
                "morale": 4, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
            "Warlock Titans": {
                "tier": 3, "cost": 5, "dice": 4, "health": 5,
                "morale": 3, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
        },

        "combat_cards": {
            "Command of the Autarch": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 0},
                "requires": [],
                "effect": "-",
            },
            "Hit and Run": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Aspect Warriors", "Hellebore Frigates"],
                "effect": "Spend 1 [M] to move 1 unit to adjacent friendly or uncontrolled area.",
            },
            "Howling Banshees": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Aspect Warriors", "Hellebore Frigates"],
                "effect": "Spend 1 [M] to force enemy to rout a unit of his choice.",
            },
            "Ranger Support": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 1},
                "requires": [],
                "effect": "-",
            },
            "Striking Scorpions": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": ["Aspect Warriors", "Hellebore Frigates"],
                "effect": "Enemy loses 1 die of his choice.",
            },
            "Fire Dragon's Vengeance": {
                "tier": 0, "cost": 2,
                "icons": {"G": 2, "S": 0, "M": 0},
                "requires": ["Aspect Warriors", "Hellebore Frigates"],
                "effect": "Gain 2 (s).",
            },
            "Swooping Hawks": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 2, "M": 0},
                "requires": ["Aspect Warriors", "Hellebore Frigates"],
                "effect": "Spend 1 [M] to gain 2 (g).",
            },
            "Wraithguard Advance": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 0, "M": 1},
                "requires": ["Wraithguard", "Hellebore Frigates", "Void Stalkers"],
                "effect": "Enemy spends 1 [M] or routs unit of his choosing.",
            },
            "Wraithguard Support": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 1, "M": 1},
                "requires": ["Wraithguard", "Hellebore Frigates", "Void Stalkers"],
                "effect": "Spend 1 [M] to rally 1 unit.",
            },
            "Fire Prism": {
                "tier": 2, "cost": 4,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["Falcons", "Void Stalkers"],
                "effect": "If attacking, gain 2 (g). If defending, force enemy to lose 5 (s).",
            },
            "Spiritseer's Guidance": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": [],
                "effect": "-",
            },
            "Wave Serpent": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 2, "M": 0},
                "requires": ["Falcons", "Void Stalkers"],
                "effect": "Spend 1 [M] to move any number of Tier 0 and Tier 1 units to an adjacent area — may start a new combat.",
            },
            "Holofield Emitter": {
                "tier": 3, "cost": 6,
                "icons": {"G": 1, "S": 2, "M": 1},
                "requires": ["Warlock Titans", "Void Stalkers"],
                "effect": "Play 1 card from your hand — gain its combat icons but not its abilities.",
            },
            "Psychic Lance": {
                "tier": 3, "cost": 6,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["Warlock Titans", "Void Stalkers"],
                "effect": "Gain 4 (g) unless enemy discards 1 face up card of your choice.",
            },
        },

        "enhanced_orders": [
            {"tier": 0, "name": "Tactical Strikes",    "cost": 1, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Wraithbone Singers",  "cost": 2, "order": "Deploy",     "limit": "Once per round"},
            {"tier": 1, "name": "Farseer",             "cost": 2, "order": "Strategize", "limit": "Once per round"},
            {"tier": 1, "name": "Corsair Raid",        "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 2, "name": "Strafing Run",        "cost": 3, "order": "Advance",    "limit": "Orbital Strike, once per round"},
        ],

        "event_cards": [
            {"name": "Exodite Colony",    "type": "Tactic", "effect": "Spend 1 materiel to place 1 free city on a friendly or uncontrolled world not containing a structure or Eldar objective token."},
            {"name": "Farsight",          "type": "Scheme", "effect": "At start of assess damage, discard to take all units in this combat and place on any friendly area."},
            {"name": "Legacy of Vaul",    "type": "Tactic", "effect": "Gain 2 (F)."},
            {"name": "Outcasts Returned", "type": "Tactic", "effect": "Either place 1 free Frigate in any uncontrolled void, or take 1 Frigate from any void and place it in any uncontrolled void."},
            {"name": "Outmanoeuvre",      "type": "Scheme", "effect": "At end of Planning Phase, discard to look at 1 of your order tokens. Then place on top or bottom of the stack."},
            {"name": "Path of the Warrior","type": "Tactic","effect": "Purchase 1 combat upgrade, reducing its cost by 1 per friendly world with a city."},
            {"name": "Vicious Raids",     "type": "Scheme", "effect": "When resolving an orbital strike, discard to reroll any dice, then gain 1 die of your choice."},
            {"name": "Warp Gate",         "type": "Scheme", "effect": "Instead of revealing Order, discard to take any units from 1 area and place on any 1 area (friendly or uncontrolled)."},
        ],

        "warp_storm_moves": {
            "Across":                "Bastions do not prevent orbital strike. Spend 1 [S] to move any ships in active system to friendly or empty voids in adjacent system.",
            "Sideways":              "This order can be resolved even if there are no units in the active system.",
            "Top Right/Bottom Left": "After resolving a combat with this order, you may perform 1 orbital strike in the active system.",
            "Top Left/Bottom Right": "When purchasing structure, may place it on world containing exactly 1 different structure.",
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    "Necrons": {
        "dominate_action": (
            "Take any of your units from 1 world and place them on a friendly world "
            "containing a structure in the active system."
        ),

        "units": {
            "Warriors": {
                "tier": 0, "cost": 2, "dice": 2, "health": 3,
                "morale": 0, "starting_qty": 4, "max_qty": 4,
            },
            "Scythe-Class Harvest Ships": {
                "tier": 0, "cost": 2, "dice": 2, "health": 3,
                "morale": 1, "starting_qty": None, "max_qty": 2,
            },
            "Immortals": {
                "tier": 1, "cost": 3, "dice": 3, "health": 4,
                "morale": 1, "starting_qty": 1, "max_qty": 3,
            },
            "Monoliths": {
                "tier": 2, "cost": 4, "dice": 3, "health": 5,
                "morale": 2, "starting_qty": None, "max_qty": 2,
            },
            "Cairn-Class Tomb Ships": {
                "tier": 2, "cost": 5, "dice": 3, "health": 6,
                "morale": 4, "starting_qty": None, "max_qty": 2,
                "bonus_tokens": {"F": 1},
            },
            "C'tan Star God Shard": {
                "tier": 3, "cost": 5, "dice": 3, "health": 6,
                "morale": 3, "starting_qty": None, "max_qty": 1,
                "bonus_tokens": {"R": 1, "F": 1},
            },
        },

        "combat_cards": {
            "Attack Subroutines": {
                "tier": None, "cost": None,
                "icons": {"G": 2, "S": 0, "M": 0},
                "requires": ["Warriors", "Scythe-Class Harvest Ships"],
                "effect": "Gain 1 [M].",
            },
            "Everlasting Conquest": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 0},
                "requires": ["Warriors", "Immortals", "Scythe-Class Harvest Ships"],
                "effect": "For each [M] you have, gain either 1 [G] or 1 [S].",
            },
            "Flayed Ones": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Warriors", "Scythe-Class Harvest Ships"],
                "effect": "If enemy has any [M], gain 1 [M] and force enemy to lose 1 [M].",
            },
            "Fortelling Cryptek": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": [],
                "effect": "-",
            },
            "Warrior Phalanx": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 2, "M": 0},
                "requires": ["Warriors", "Scythe-Class Harvest Ships"],
                "effect": "Gain 1 [M].",
            },
            "Canoptek Swarm": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 0, "M": 1},
                "requires": [],
                "effect": "-",
            },
            "Destroyers": {
                "tier": 0, "cost": 2,
                "icons": {"G": 2, "S": 0, "M": 1},
                "requires": ["Immortals", "Scythe-Class Harvest Ships"],
                "effect": "If your enemy has at least 1 routed unit, gain 2 (g).",
            },
            "Lychguard": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 2, "M": 1},
                "requires": ["Immortals", "Scythe-Class Harvest Ships"],
                "effect": "If your enemy has at least 1 routed unit, gain 2 (s).",
            },
            "Overlord's Will": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 0, "M": 3},
                "requires": [],
                "effect": "-",
            },
            "Doomsday Phalanx": {
                "tier": 2, "cost": 4,
                "icons": {"G": 3, "S": 0, "M": 0},
                "requires": ["Monoliths", "Cairn-Class Tomb Ships"],
                "effect": "When an enemy unit is routed during assess damage step, it is destroyed unless your enemy spends 1 [S].",
            },
            "Monolith Phalanx": {
                "tier": 2, "cost": 4,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["Monoliths", "Cairn-Class Tomb Ships"],
                "effect": "Gain 3 (s).",
            },
            "Triarch Praetorians": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": ["Warriors", "Scythe-Class Harvest Ships"],
                "effect": "For each unrouted Warrior or Harvest Ship, spend up to 1 die to gain 1 [G], 1 [S] or 1 [M].",
            },
            "Shard of the Nightbringer": {
                "tier": 3, "cost": 6,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["C'tan Star God Shard", "Cairn-Class Tomb Ships"],
                "effect": "Destroy 1 Tier 0 or Tier 1 unit.",
            },
            "Shard of the Deceiver": {
                "tier": 3, "cost": 6,
                "icons": {"G": 1, "S": 1, "M": 2},
                "requires": ["C'tan Star God Shard", "Cairn-Class Tomb Ships"],
                "effect": "Take your C'tan Shard and place it on any friendly world.",
            },
        },

        "enhanced_orders": [
            {"tier": 0, "name": "Harvest Raid",           "cost": 1, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Eternity Gate",          "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 1, "name": "Reanimation Protocols",  "cost": 2, "order": "Strategize", "limit": "Once per round"},
            {"tier": 1, "name": "Tomb Worlds",            "cost": 2, "order": "Deploy",     "limit": "Once per round"},
            {"tier": 1, "name": "Translocation Crypts",   "cost": 2, "order": "Deploy",     "limit": "Once per round"},
        ],

        "event_cards": [
            {"name": "Chronomancy",        "type": "Scheme", "effect": "At start of execution round of combat, may discard to draw up to 2 combat cards and then discard that many from your hand."},
            {"name": "Deathmarks",         "type": "Scheme", "effect": "At start of execution round of combat, may discard to rout 1 enemy Tier 0 or Tier 1 unit."},
            {"name": "Doom Scythes",       "type": "Scheme", "effect": "At start of execution round of combat, may discard and rout up to 2 of your units. Enemy destroys 1 (R) per routed unit."},
            {"name": "Remorseless Advance","type": "Scheme", "effect": "At start of execution round of combat, may discard to resolve 1 additional assess damage step."},
            {"name": "Resurrection Orb",   "type": "Scheme", "effect": "When 1 of your Tier 0 or Tier 1 units is routed or destroyed during combat, may discard to return it unrouted at end of assess damage step."},
            {"name": "Tomb World Awakening","type": "Tactic","effect": "Purchase 1 structure and place it on a friendly world not containing a structure."},
            {"name": "Tomb World Archives","type": "Tactic", "effect": "Purchase 1 combat upgrade."},
            {"name": "Wrath of the Void Dragon","type": "Scheme","effect": "At start of execution round of combat, may discard. If you do, you and your enemy suffer an additional 3 damage during this assess damage step."},
        ],

        "warp_storm_moves": {
            "Across":                "While resolving this order, you may treat all your cities in the active system as factories.",
            "Sideways":              "After you resolve this order, if you purchased at least 1 unit or structure, you may purchase 1 bastion and place it on a friendly or uncontrolled world.",
            "Top Right/Bottom Left": "When you reveal this order token, rally all of your units in the active system and all ground units in every other system.",
            "Top Left/Bottom Right": "After moving your units, you may take any of your Tier 0 or Tier 1 units from 1 friendly world containing a structure and place them on any world in the active system containing an unrouted Monolith.",
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    "Tyranids": {
        "dominate_action": "Gain 1 additional asset token of your choice. You can have up to 4 of each asset token in your play area at any time.",

        "units": {
            "Gaunts": {
                "tier": 0, "cost": 2, "dice": 1, "health": 1,
                "morale": 3, "starting_qty": 3, "max_qty": 6,
            },
            "Devourer Bio-Ships": {
                "tier": 0, "cost": 2, "dice": 1, "health": 2,
                "morale": 3, "starting_qty": 1, "max_qty": 5,
            },
            "Warriors": {
                "tier": 1, "cost": 3, "dice": 3, "health": 2,
                "morale": 3, "starting_qty": None, "max_qty": 6,
            },
            "Carnifexes": {
                "tier": 2, "cost": 4, "dice": 4, "health": 3,
                "morale": 3, "starting_qty": None, "max_qty": 3,
            },
            "Leviathan Hive Ships": {
                "tier": 2, "cost": 5, "dice": 3, "health": 6,
                "morale": 4, "starting_qty": 1, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
            "Hierophant Bio-Titans": {
                "tier": 3, "cost": 5, "dice": 5, "health": 4,
                "morale": 3, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"R": 1},
            },
        },

        "combat_cards": {
            "Burrowing Organisms": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": [],
                "effect": "-",
            },
            "Genestealer Hybrids": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Gaunts", "Devourer Bio-Ships"],
                "effect": "Force enemy to lose 1 [G], 1 [S], or 1 [M] (whichever he has most of). Then gain the same.",
            },
            "Hive Tyrant": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Warriors", "Leviathan Hive Ships"],
                "effect": "Either rally 1 of your units. Spend 1 [M] to gain either 1 [G] or 1 [S].",
            },
            "Hormagaunt Brood": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Gaunts", "Devourer Bio-Ships"],
                "effect": "Destroy 1 unrouted Gaunt or Devourer to gain 3 (g).",
            },
            "Rain of Spores": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": [],
                "effect": "-",
            },
            "Ripper Swarms": {
                "tier": 0, "cost": 2,
                "icons": {"G": 2, "S": 0, "M": 0},
                "requires": ["Gaunts", "Devourer Bio-Ships"],
                "effect": "At end of this execution round, gain 1 materiel for each unit destroyed (max 2).",
            },
            "Termagaunt Brood": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": [],
                "effect": "-",
            },
            "Warrior Brood": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": ["Warriors", "Leviathan Hive Ships"],
                "effect": "Reroll all of your [G], [S], or [M].",
            },
            "Winged Horror": {
                "tier": 0, "cost": 2,
                "icons": {"G": 2, "S": 0, "M": 0},
                "requires": ["Warriors", "Devourer Bio-Ships"],
                "effect": "Your enemy may allow you to gain 2 (s). If he does not, add 2 to your offence value in the next execution round.",
            },
            "Crushing Claws": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 2, "M": 0},
                "requires": ["Carnifexes", "Leviathan Hive Ships"],
                "effect": "Spend either 1 [G] or 1 [M] to force your enemy to lose 2 [S].",
            },
            "Scything Talons": {
                "tier": 2, "cost": 4,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["Carnifexes", "Leviathan Hive Ships"],
                "effect": "Destroy 1 unrouted Carnifex or Hive Ship to gain 3 (g) and 2 (s).",
            },
            "Synaptic Control": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": ["Warriors", "Leviathan Hive Ships"],
                "effect": "Rally 1 of your units. Gain either 1 (g) or 1 (s) for each of your unrouted units in excess of the enemy's.",
            },
            "Glory of the Swarm": {
                "tier": 3, "cost": 6,
                "icons": {"G": 3, "S": 1, "M": 0},
                "requires": ["Hierophant Bio-Titans", "Leviathan Hive Ships"],
                "effect": "Rally all of your units. During this execution round, you assign damage to your enemy's units and bastions.",
            },
            "Overwhelming Presence": {
                "tier": 3, "cost": 6,
                "icons": {"G": 1, "S": 2, "M": 0},
                "requires": ["Hierophant Bio-Titans", "Leviathan Hive Ships"],
                "effect": "Force your enemy to choose 3 times to either rout 1 of his units or lose 1 die of his choice.",
            },
        },

        "enhanced_orders": [
            {"tier": 0, "name": "Genestealer Infiltration", "cost": 1, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Breeding Chambers",        "cost": 2, "order": "Deploy",     "limit": "Once per round"},
            {"tier": 1, "name": "Capillary Towers",         "cost": 2, "order": "Strategize", "limit": "Once per round"},
            {"tier": 1, "name": "Without Number",           "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 2, "name": "Mycetic Spores",           "cost": 3, "order": "Advance",    "limit": "Orbital Strike, once per round; requires Breeding Chambers"},
        ],

        "event_cards": [
            {"name": "Brood Nests",              "type": "Scheme", "effect": "Before revealing an order, may discard to place 1 free Gaunt on each of 2 different friendly worlds."},
            {"name": "Devourer of Worlds",       "type": "Tactic", "effect": "Choose a system. Gain materiel equal to the materiel value of friendly worlds in that system."},
            {"name": "Hive Mind",                "type": "Scheme", "effect": "While resolving an order, may discard to increase your Tier by 1 for each of your Hive Ships."},
            {"name": "Infiltration Organisms",   "type": "Tactic", "effect": "Purchase 1 combat upgrade, reducing its materiel cost by 1 for each of your Hive Ships."},
            {"name": "Rapid Mutation",           "type": "Tactic", "effect": "Gain 2 (F)."},
            {"name": "Rise of the Faithful",     "type": "Scheme", "effect": "Instead of revealing an order, may discard to place 1 free bastion on a friendly world not containing a structure."},
            {"name": "Shadow in the Warp",       "type": "Scheme", "effect": "May discard when you start a combat. If you do, your enemy cannot use reinforcement tokens during the combat."},
            {"name": "Splinter Fleet",           "type": "Tactic", "effect": "Place 1 free Devourer on any friendly void."},
        ],

        "warp_storm_moves": {
            "Across":                "After you resolve this order, may purchase up to 2 units for each unrouted Hive Ship in the active system.",
            "Sideways":              "Bastions do not prevent orbital strike. Spend up to 2 [G] for each participating Hive Ship. For each [G] spend, purchase 1 unit Tier 2 or less.",
            "Top Right/Bottom Left": "While resolving this order in a system with an unrouted ship, may place 1 free (R) in the contested area at start of reinforce step.",
            "Top Left/Bottom Right": "After resolving this order, may destroy any of your units or structures to temporarily gain materiel equal to their cost, spend only on ships.",
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    "Tau": {
        "dominate_action": (
            "When you resolve a dominate order in a system containing at least 1 of your "
            "units or structures, you may draw 4 cards from the top of your event deck. "
            "Resolve the ability of 1 of those cards and discard the others."
        ),

        "units": {
            "Fire Warriors": {
                "tier": 0, "cost": 2, "dice": 2, "health": 1,
                "morale": 2, "starting_qty": 3, "max_qty": 6,
            },
            "Protector Cruisers": {
                "tier": 0, "cost": 2, "dice": 3, "health": 1,
                "morale": 2, "starting_qty": None, "max_qty": 2,
            },
            "XV8 Crisis Battlesuits": {
                "tier": 1, "cost": 3, "dice": 3, "health": 3,
                "morale": 2, "starting_qty": 2, "max_qty": 6,
            },
            "TX7 Hammerhead Gunships": {
                "tier": 2, "cost": 4, "dice": 4, "health": 4,
                "morale": 2, "starting_qty": None, "max_qty": 3,
            },
            "Custodian Carriers": {
                "tier": 2, "cost": 5, "dice": 5, "health": 4,
                "morale": 4, "starting_qty": None, "max_qty": 2,
                "bonus_tokens": {"F": 1},
            },
            "KX139 Supremacy Armour Battlesuits": {
                "tier": 3, "cost": 5, "dice": 4, "health": 5,
                "morale": 3, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
        },

        "combat_cards": {
            "Crossfire": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Fire Warriors", "XV8 Crisis Battlesuits", "Protector Cruisers"],
                "effect": "Gain 2 (g).",
            },
            "Kroot Hunting Packs": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Fire Warriors", "Protector Cruisers"],
                "effect": "Gain 1 [?].",
            },
            "Pathfinder Teams": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 0},
                "requires": ["Fire Warriors", "Protector Cruisers"],
                "effect": "If you are attacking, look at your enemy's facedown combat card. Play 1 combat card from your hand. Then discard this card.",
            },
            "Stealth Teams": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Fire Warriors", "Protector Cruisers"],
                "effect": "Your enemy may choose and rout 1 of his units. If he does not, force your enemy to lose 1 [G], 1 [S], or 1 [M].",
            },
            "Tactical Retreat": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": ["Fire Warriors", "Protector Cruisers"],
                "effect": "Gain 2 (s).",
            },
            "Evasion": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 1, "M": 1},
                "requires": ["Fire Warriors", "Protector Cruisers"],
                "effect": "During this execution round, if any of your unrouted Tier 0 units become routed or are destroyed, you may take them and place them back at the end of the assess damage step.",
            },
            "Feigned Retreat": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 2, "M": 0},
                "requires": ["Fire Warriors", "XV8 Crisis Battlesuits", "Protector Cruisers"],
                "effect": "If none of your units retreated during this execution round, gain 2 (g).",
            },
            "Kauyon": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 2, "M": 0},
                "requires": [],
                "effect": "-",
            },
            "Mont'ka": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["XV8 Crisis Battlesuits", "Protector Cruisers"],
                "effect": "Spend up to 2 dice. For each dice you spend, gain 2 (g).",
            },
            "Fire and Movement": {
                "tier": 2, "cost": 4,
                "icons": {"G": 2, "S": 1, "M": 0},
                "requires": ["TX7 Hammerhead Gunships", "Custodian Carriers"],
                "effect": "During this execution round, when 1 of your units is destroyed during assess damage step, you may retreat that unit instead.",
            },
            "Firefight": {
                "tier": 2, "cost": 4,
                "icons": {"G": 3, "S": 0, "M": 0},
                "requires": ["XV8 Crisis Battlesuits", "TX7 Hammerhead Gunships", "Custodian Carriers"],
                "effect": "Gain 1 (s). Force your enemy to lose either 1 [G] or 1 [M].",
            },
            "Regroup": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": ["TX7 Hammerhead Gunships", "Custodian Carriers"],
                "effect": "Gain 2 [?].",
            },
            "For the Greater Good": {
                "tier": 3, "cost": 6,
                "icons": {"G": 2, "S": 0, "M": 3},
                "requires": ["KX139 Supremacy Armour Battlesuits", "Custodian Carriers"],
                "effect": "Force your enemy to lose 3 [M]. For each [M] your enemy cannot lose, gain 2 (g).",
            },
            "Supremacy": {
                "tier": 3, "cost": 6,
                "icons": {"G": 3, "S": 1, "M": 0},
                "requires": ["KX139 Supremacy Armour Battlesuits", "Custodian Carriers"],
                "effect": "During this execution round, the health value of your enemy's units is reduced to 3.",
            },
        },

        "enhanced_orders": [
            {"tier": 1, "name": "Gue'vesa Allies",          "cost": 2, "order": "Deploy",     "limit": "Once per round"},
            {"tier": 1, "name": "Mobilised Hunter Cadres",  "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 1, "name": "Precision Strikes",        "cost": 2, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Targeting Array",          "cost": 2, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Teachings of Tau'va",      "cost": 2, "order": "Strategize", "limit": "Once per round"},
        ],

        "event_cards": [
            {"name": "Autonomous Drones",  "type": "Tactic", "effect": "Rout 1 enemy unit of Tier 2 or less that is in a system containing at least 1 of your units."},
            {"name": "Critical Strike",    "type": "Scheme", "effect": "When an enemy unit suffers damage during combat, you may discard this card to destroy that unit."},
            {"name": "Denial of Supplies", "type": "Scheme", "effect": "You may discard at the start of combat. If you do, your enemy cannot place (R) from his play area into the contested area during reinforce step."},
            {"name": "Evacuation",         "type": "Tactic", "effect": "Destroy 1 of your structures in any system to place 1 free structure on a different friendly world not containing a structure in the same or adjacent system."},
            {"name": "Philosophy of War",  "type": "Scheme", "effect": "You may discard at the start of combat to replace any number of pairs of combat cards from your combat deck with pairs of the same or lower Tier from your upgrade deck."},
            {"name": "Rapid Response",     "type": "Tactic", "effect": "Choose a system. Move any of your units between friendly or uncontrolled areas in the chosen system."},
            {"name": "Sabotage",           "type": "Tactic", "effect": "Destroy 1 of your unrouted units in any system to destroy 1 enemy structure in that system."},
            {"name": "War Council",        "type": "Scheme", "effect": "Before revealing an order during the Operations Phase, you may discard this card to rally all of your units in any 1 system."},
        ],

        "warp_storm_moves": {
            "Across":                "Enemy bastions do not prevent this orbital strike. During orbital strike, gain 1 [?].",
            "Sideways":              "Before you resolve this order, you may resolve an additional Advance Order using only 1 of your Tier 0 or Tier 1 units already in the active system.",
            "Top Right/Bottom Left": "When you reveal this order token in a system containing 1 of your units or structures and a friendly or uncontrolled world, you may spend 1 materiel to place 1 free Tier 0 unit.",
            "Top Left/Bottom Right": "When you reveal this order token, you may place 3 of your order tokens from your play area onto the top of your event deck.",
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    "Imperial Guard": {
        "dominate_action": (
            "When you resolve a dominate order, you may resolve a deploy order, only to purchase "
            "2 or more identical units and placing them on either 1 friendly world containing a "
            "structure or 1 friendly or uncontrolled void in the active system. Reduce the materiel "
            "cost of each unit by 1."
        ),

        "units": {
            "Guardsmen": {
                "tier": 0, "cost": 2, "dice": 1, "health": 1,
                "morale": 2, "starting_qty": 3, "max_qty": 12,
            },
            "Lunar-Class Cruisers": {
                "tier": 0, "cost": 2, "dice": 2, "health": 2,
                "morale": 2, "starting_qty": 1, "max_qty": 3,
            },
            "Ogryns": {
                "tier": 1, "cost": 3, "dice": 2, "health": 4,
                "morale": 2, "starting_qty": 2, "max_qty": 6,
            },
            "Leman Russ Battle Tanks": {
                "tier": 2, "cost": 4, "dice": 3, "health": 4,
                "morale": 3, "starting_qty": None, "max_qty": 6,
            },
            "Emperor-Class Battleships": {
                "tier": 2, "cost": 5, "dice": 4, "health": 6,
                "morale": 3, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1},
            },
            "Warhound Titans": {
                "tier": 3, "cost": 5, "dice": 3, "health": 5,
                "morale": 4, "starting_qty": None, "max_qty": 3,
                "bonus_tokens": {"F": 1, "R": 3},
            },
        },

        "combat_cards": {
            "Fire Support": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Guardsmen", "Lunar-Class Cruisers"],
                "effect": "Reroll 1 [S].",
            },
            "For the Emperor!": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Guardsmen", "Lunar-Class Cruisers"],
                "effect": "Gain 1 (g) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
            },
            "Incoming!": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": ["Guardsmen", "Lunar-Class Cruisers"],
                "effect": "Gain 1 (s) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
            },
            "Iron Discipline": {
                "tier": None, "cost": None,
                "icons": {"G": 0, "S": 0, "M": 1},
                "requires": ["Guardsmen", "Lunar-Class Cruisers"],
                "effect": "Rally 1 of your units.",
            },
            "Ratling Marksmen": {
                "tier": None, "cost": None,
                "icons": {"G": 1, "S": 0, "M": 0},
                "requires": ["Guardsmen", "Lunar-Class Cruisers"],
                "effect": "Your enemy chooses and routs 1 of his units unless he spends 1 die of his choice.",
            },
            "Bullgryn Bulwark": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 2, "M": 0},
                "requires": ["Ogryns", "Lunar-Class Cruisers"],
                "effect": "Gain 1 (g) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
            },
            "Mechanised Combat Group": {
                "tier": 0, "cost": 2,
                "icons": {"G": 1, "S": 1, "M": 1},
                "requires": [],
                "effect": "-",
            },
            "Ogryn Shock Troops": {
                "tier": 0, "cost": 2,
                "icons": {"G": 2, "S": 0, "M": 0},
                "requires": ["Ogryns", "Lunar-Class Cruisers"],
                "effect": "Gain 1 (s) for each unrouted Guardsman or Cruiser, to a maximum of 3.",
            },
            "Sentinel Reconnaissance": {
                "tier": 0, "cost": 2,
                "icons": {"G": 0, "S": 1, "M": 0},
                "requires": ["Ogryns", "Lunar-Class Cruisers"],
                "effect": "If you are attacking, look at your enemy's facedown combat. Gain either 2 [G] or 2 [S].",
            },
            "Armoured Spearhead": {
                "tier": 2, "cost": 4,
                "icons": {"G": 3, "S": 0, "M": 0},
                "requires": ["Leman Russ Battle Tanks", "Emperor-Class Battleships"],
                "effect": "Choose 1 of your enemy's Tier 2 or Tier 3 units or bastions. That unit or bastion suffers damage first during this execution round.",
            },
            "Combined Arms": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 1, "M": 0},
                "requires": [],
                "effect": "-",
            },
            "Wyvern Suppression Fire": {
                "tier": 2, "cost": 4,
                "icons": {"G": 1, "S": 2, "M": 0},
                "requires": ["Leman Russ Battle Tanks", "Emperor-Class Battleships"],
                "effect": "Your enemy chooses and destroys 1 of his routed Tier 0 or Tier 1 units.",
            },
            "Hammer of the Emperor": {
                "tier": 3, "cost": 6,
                "icons": {"G": 3, "S": 0, "M": 1},
                "requires": ["Warhound Titans", "Emperor-Class Battleships"],
                "effect": "Warhound Titan: Gain 2 (g) for each of your unrouted units of a different Tier, max 6. Battleship: Gain 3 (g) for each of your unrouted units of a different Tier.",
            },
            "Titan Support": {
                "tier": 3, "cost": 6,
                "icons": {"G": 1, "S": 2, "M": 2},
                "requires": ["Warhound Titans", "Emperor-Class Battleships"],
                "effect": "During this execution round, your units of Tier 2 or less cannot become routed.",
            },
        },

        "enhanced_orders": [
            {"tier": 0, "name": "Saturation Bombing",      "cost": 1, "order": "Advance",    "limit": "Orbital Strike, once per round"},
            {"tier": 1, "name": "Adeptus Astronomica",     "cost": 2, "order": "Advance",    "limit": "Once per round"},
            {"tier": 1, "name": "Departmento Munitorum",   "cost": 2, "order": "Strategize", "limit": "Once per round"},
            {"tier": 1, "name": "Forced Recruitment",      "cost": 2, "order": "Deploy",     "limit": "Once per round; unit capacity increase is persistent"},
            {"tier": 2, "name": "Virus Bombs",             "cost": 3, "order": "Advance",    "limit": "Orbital Strike, once per round"},
        ],

        "event_cards": [
            {"name": "Call of the Astropaths",   "type": "Scheme", "effect": "Choose a friendly world. Gain assets from this world and gain materiel equal to its materiel value."},
            {"name": "Deathstrike Missile",      "type": "Scheme", "effect": "Before you perform an orbital strike, you may discard this card to add 2 to the total damage suffered by your enemy's units."},
            {"name": "Order of the High Command","type": "Tactic", "effect": "Instead of playing a combat card from your hand, you may discard this card to play any card from either your combat deck or your upgrade deck."},
            {"name": "Imperial Tithe",           "type": "Tactic", "effect": "Rout 1 enemy Tier 0 or Tier 1 unit that is either in a system containing at least 1 of your units or in an adjacent system."},
            {"name": "Military Production Shift","type": "Scheme", "effect": "At the end of a reinforce step of combat, if you are defending, you may discard this card to place 2 free (R) in the contested area."},
            {"name": "Lance Strike",             "type": "Scheme", "effect": "You may discard at the start of combat on any world. If you do, either destroy 1 Tier 0 or 1 Tier 1 unit on that world or rout 1 Tier 2 unit at the end of the first assess damage step."},
            {"name": "Tactical Genius",          "type": "Tactic", "effect": "Purchase 1 combat upgrade, reducing its materiel cost by 1 for each friendly world containing a factory."},
            {"name": "Tempestus Scions",         "type": "Tactic", "effect": "Either place 2 free Guardsmen on 1 friendly world in a system containing at least 1 of your factories or place 1 free Guardsman on any friendly world."},
        ],

        "warp_storm_moves": {
            "Across":                "Enemy bastions do not prevent orbital strike. During this orbital strike, the health value of your enemy's units is reduced to 3.",
            "Sideways":              "While resolving this order, you may treat all your cities in the active system as factories capable of deploying Guardsmen only. Unit capacity of worlds with a city increased by 2 (max 4), Guardsmen only.",
            "Top Right/Bottom Left": "While resolving this order, you may purchase 1 upgrade only. Then resolve a limited Deploy, Advance or Dominate order in the active system.",
            "Top Left/Bottom Right": "While resolving this order, you may move up to 6 units to a world, if at least 1 is a Guardsman. After resolving, you may retreat any Guardsmen in excess of that world's unit capacity.",
        },
    },
}


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def get_faction(name: str) -> dict | None:
    """Вернуть данные фракции по имени (регистронезависимо)."""
    for key, value in FACTIONS.items():
        if key.lower() == name.lower():
            return value
    return None


def get_unit(unit_name: str) -> list[dict]:
    """
    Найти юнит по имени во всех фракциях.
    Возвращает список словарей {'faction': ..., 'unit_name': ..., **unit_data}.
    """
    results = []
    for faction, data in FACTIONS.items():
        for uname, udata in data["units"].items():
            if unit_name.lower() in uname.lower():
                results.append({"faction": faction, "unit_name": uname, **udata})
    return results


def get_combat_card(card_name: str) -> list[dict]:
    """
    Найти боевую карту по имени во всех фракциях.
    Возвращает список словарей {'faction': ..., 'card_name': ..., **card_data}.
    """
    results = []
    for faction, data in FACTIONS.items():
        for cname, cdata in data["combat_cards"].items():
            if card_name.lower() in cname.lower():
                results.append({"faction": faction, "card_name": cname, **cdata})
    return results


def search(query: str) -> dict:
    """
    Текстовый поиск по всей базе данных.
    Возвращает {'units': [...], 'combat_cards': [...], 'event_cards': [...]}.
    """
    q = query.lower()
    units = get_unit(q)
    cards = get_combat_card(q)
    events = []
    for faction, data in FACTIONS.items():
        for card in data["event_cards"]:
            if q in card["name"].lower() or q in card["effect"].lower():
                events.append({"faction": faction, **card})
    return {"units": units, "combat_cards": cards, "event_cards": events}


def faction_summary() -> None:
    """Вывести краткую сводку по всем фракциям."""
    for fname, fdata in FACTIONS.items():
        units = fdata["units"]
        cards = fdata["combat_cards"]
        orders = fdata["enhanced_orders"]
        events = fdata["event_cards"]
        print(
            f"{fname:30s}  "
            f"Юниты: {len(units):2d}  "
            f"Боевые карты: {len(cards):2d}  "
            f"Приказы: {len(orders):2d}  "
            f"События: {len(events):2d}"
        )


# ---------------------------------------------------------------------------
# Быстрый тест при запуске напрямую
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Forbidden Stars — база данных ===\n")
    print("Фракции:")
    faction_summary()

    print("\n--- Пример: все юниты Tier 3 ---")
    for fname, fdata in FACTIONS.items():
        for uname, udata in fdata["units"].items():
            if udata["tier"] == 3:
                print(f"  [{fname}] {uname} — {udata['dice']} dice, health {udata['health']}, morale {udata['morale']}")

    print("\n--- Пример: поиск 'titan' ---")
    result = search("titan")
    for u in result["units"]:
        print(f"  Unit: [{u['faction']}] {u['unit_name']}")
    for c in result["combat_cards"]:
        print(f"  Card: [{c['faction']}] {c['card_name']}")

    print("\n--- Пример: карты событий типа 'Tactic' у Eldar ---")
    for e in FACTIONS["Eldar"]["event_cards"]:
        if e["type"] == "Tactic":
            print(f"  {e['name']}: {e['effect'][:60]}...")
