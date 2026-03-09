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

from faction_defs.chaos import CHAOS
from faction_defs.empire     import EMPIRE
from faction_defs.orks import ORKS
# ── Заготовки (TODO: заполнить данные в каждом файле) ─────────────────────────
# Имя файла и имя переменной можно менять свободно —
# главное чтобы импорт здесь совпадал с именем файла и переменной внутри него.
from faction_defs.nomads    import NOMADS
from faction_defs.theocracy import THEOCRACY
from faction_defs.machines  import MACHINES
from faction_defs.pirates   import PIRATES
from faction_defs.elders    import ELDERS
from faction_defs.traders   import TRADERS
from faction_defs.mutants   import MUTANTS
from faction_defs.crusaders import CRUSADERS

# ── Список всех зарегистрированных фракций ───────────────────────────────────
# Для добавления новой: допишите импорт выше и добавьте объект сюда.
_ALL_FACTIONS: list[Faction] = [
    CHAOS,
    EMPIRE,
    ORKS,
    # заготовки — раскомментируй когда заполнишь данные:
    NOMADS,
    THEOCRACY,
    MACHINES,
    PIRATES,
    ELDERS,
    TRADERS,
    MUTANTS,
    CRUSADERS,
]

# ── Публичные реестры ─────────────────────────────────────────────────────────

FACTIONS: Dict[str, Faction] = {f.id: f for f in _ALL_FACTIONS}

FACTION_CONFIGS: Dict[str, UnitConfig] = {f.id: f.unit_config for f in _ALL_FACTIONS}
