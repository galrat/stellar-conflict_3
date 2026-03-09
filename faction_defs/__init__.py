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

from faction_defs.federation import FEDERATION
from faction_defs.empire     import EMPIRE
from faction_defs.syndicate  import SYNDICATE
from faction_defs.collective import COLLECTIVE

# ── Список всех зарегистрированных фракций ───────────────────────────────────
# Для добавления новой: допишите импорт выше и добавьте объект сюда.
_ALL_FACTIONS: list[Faction] = [
    FEDERATION,
    EMPIRE,
    SYNDICATE,
    COLLECTIVE,
]

# ── Публичные реестры ─────────────────────────────────────────────────────────

FACTIONS: Dict[str, Faction] = {f.id: f for f in _ALL_FACTIONS}

FACTION_CONFIGS: Dict[str, UnitConfig] = {f.id: f.unit_config for f in _ALL_FACTIONS}
