"""Dataset catalog for pgfn-fetcher."""

from __future__ import annotations

import datetime as dt
from typing import Any

from ._catalog_base import DatasetEntry, GroupInfo, quarterly_datasets
from .constants import PGFN_BASE_URL, PGFN_DATASETS, PGFN_START_YEAR

__all__ = [
    "DatasetEntry",
    "GroupInfo",
    "GROUPS",
    "GROUP_ALIASES",
    "list_datasets",
]


def _build_quarterly_entries_for_dataset(
    ds_id: str, meta: dict[str, Any]
) -> list[DatasetEntry]:
    """Build quarterly dataset entries for a PGFN dataset.

    A PGFN só publica trimestre **fechado**: o trimestre corrente ainda não
    tem arquivo, então o catálogo para no último trimestre concluído.
    """
    today = dt.date.today()
    quarter = (today.month - 1) // 3 + 1
    if quarter == 1:
        last_year, last_quarter = today.year - 1, 4
    else:
        last_year, last_quarter = today.year, quarter - 1
    kind = meta["file_kind"]
    url_tmpl = (
        f"{PGFN_BASE_URL}/{{year}}_trimestre_{{quarter}}/Dados_abertos_{kind}.zip"
    )
    name_tmpl = f"{meta['name']} ({{year}}-T{{quarter}})"
    return quarterly_datasets(
        group=meta["group"],
        base_id=ds_id,
        name_template=name_tmpl,
        url_template=url_tmpl,
        start_year=PGFN_START_YEAR,
        end_year=last_year,
        end_quarter=last_quarter,
        ext="zip",
    )


def _build_all_groups() -> dict[str, GroupInfo]:
    """Assemble all dataset groups."""
    groups_map: dict[str, GroupInfo] = {}
    for ds_id, meta in PGFN_DATASETS.items():
        entries = _build_quarterly_entries_for_dataset(ds_id, meta)
        groups_map[ds_id] = GroupInfo(name=meta["name"], entries=entries)
    return groups_map


_GROUPS_MAP = _build_all_groups()

GROUPS: dict[str, dict[str, Any]] = {
    grp: info.to_dict() for grp, info in _GROUPS_MAP.items()
}

GROUP_ALIASES: dict[str, str] = {
    "padrao": "sida",
    "nao_previdenciario": "sida",
    "dau": "sida",
    "prev": "previdenciario",
    "tributaria": "sida",
}


def list_datasets(group: str | None = None) -> list[dict[str, Any]]:
    """List datasets for a group or all groups."""
    if group is None:
        entries: list[dict[str, Any]] = []
        for g_data in GROUPS.values():
            entries.extend(g_data["entries"])
        return entries

    canon = GROUP_ALIASES.get(group, group)
    if canon not in GROUPS:
        raise ValueError(f"Grupo desconhecido: {group!r}")
    return list(GROUPS[canon]["entries"])
