"""
faction_defs/__init__.py — реестр всех фракций Stellar Conflict.

Чтобы добавить новую фракцию:
  1. Создайте файл faction_defs/<id_фракции>.py
  2. Определите в нём объект типа Faction (имя — по соглашению заглавными буквами)
  3. Импортируйте его ниже и добавьте в список _ALL_FACTIONS

Больше ничего менять не нужно — FACTIONS и FACTION_CONFIGS строятся автоматически.
"""
from typing import Dict

from faction_base import Faction, UnitConfig

from faction_defs.chaos          import CHAOS
from faction_defs.marine         import MARINE
from faction_defs.orks           import ORKS
from faction_defs.eldar          import ELDAR
from faction_defs.necrons        import NECRONS
from faction_defs.tyranids       import TYRANIDS
from faction_defs.tau            import TAU
from faction_defs.imperial_guard import IMPERIAL_GUARD
# ── Заготовки (TODO: заполнить данные в каждом файле) ─────────────────────────
from faction_defs.theocracy import THEOCRACY
from faction_defs.machines  import MACHINES
from faction_defs.pirates   import PIRATES
from faction_defs.crusaders import CRUSADERS

# ── Список всех зарегистрированных фракций ───────────────────────────────────
_ALL_FACTIONS: list[Faction] = [
    CHAOS,
    MARINE,
    ORKS,
    ELDAR,
    NECRONS,
    TYRANIDS,
    TAU,
    IMPERIAL_GUARD,
    # заготовки:
    THEOCRACY,
    MACHINES,
    PIRATES,
    CRUSADERS,
]

# ── Публичные реестры ─────────────────────────────────────────────────────────

FACTIONS: Dict[str, Faction] = {f.id: f for f in _ALL_FACTIONS}

FACTION_CONFIGS: Dict[str, UnitConfig] = {f.id: f.unit_config for f in _ALL_FACTIONS}
