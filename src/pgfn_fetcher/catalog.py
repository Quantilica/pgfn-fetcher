"""Dataset catalog for pgfn-fetcher."""

from __future__ import annotations

import datetime as dt
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

from ._catalog_base import DatasetEntry, GroupInfo, quarterly_datasets
from .client import PgfnClient
from .constants import PGFN_BASE_URL, PGFN_DATASETS, PGFN_START_YEAR

__all__ = [
    "DiscoveryReport",
    "classify_zip",
    "discover_entries",
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


def classify_zip(filename: str) -> str | None:
    """Mapeia o nome real de um ``.zip`` da PGFN para o id do dataset.

    A PGFN nomeia de forma irregular (``Nao_Previdenciariozip.zip`` em 2022-T4,
    ``Sistema_SIDA.zip`` em 2026-T3), então o casamento é por tokens, não por nome
    fixo. Devolve ``None`` para arquivos que não pertencem a nenhum dataset.
    """
    s = filename.lower()
    if "fgts" in s:
        return "fgts"
    if "nao_previdenciario" in s or "nao-previdenciario" in s or "sida" in s:
        return "sida"
    if "previdenciario" in s:
        return "previdenciario"
    return None


@dataclass
class DiscoveryReport:
    """Resultado da descoberta: entradas, erros contados e uso de fallback."""

    entries: dict[str, list[DatasetEntry]] = field(default_factory=dict)
    #: (dataset, trimestre) esperados que a listagem não traz (arquivo inexistente).
    missing: list[tuple[str, str]] = field(default_factory=list)
    #: trimestres cuja listagem falhou e usaram o nome fixo (fallback).
    fallback_trimesters: list[str] = field(default_factory=list)
    #: trimestres com mais de um arquivo para o mesmo dataset (ambíguo, usa o 1º).
    ambiguous: list[tuple[str, str]] = field(default_factory=list)
    root_failed: bool = False

    @property
    def errors(self) -> int:
        return len(self.missing) + len(self.ambiguous) + int(self.root_failed)


_TRIMESTER_RE = re.compile(r"^(\d{4})_trimestre_(\d{2})$")


def _fallback_name(meta: dict[str, Any]) -> str:
    return f"Dados_abertos_{meta['file_kind']}.zip"


def _entry(
    ds_id: str, meta: dict[str, Any], year: int, quarter: int, filename: str
) -> DatasetEntry:
    return DatasetEntry(
        id=f"{ds_id}_{year}-T{quarter}",
        base_id=ds_id,
        name=f"{meta['name']} ({year}-T{quarter})",
        url=f"{PGFN_BASE_URL}/{year}_trimestre_{quarter:02d}/{filename}",
        ext="zip",
        group=meta["group"],
        year=year,
        quarter=quarter,
    )


def discover_entries(
    client: PgfnClient | None = None,
    *,
    logger: logging.Logger | None = None,
) -> DiscoveryReport:
    """Monta o catálogo a partir da listagem real da PGFN.

    - Trimestres vêm de ``discover_trimesters`` (raiz); se a raiz falhar, cai no
      catálogo aritmético (``root_failed``).
    - Para cada trimestre, os nomes reais vêm da listagem do diretório. Se a
      listagem do trimestre falhar, usa o nome fixo (``fallback_trimesters``).
    - Dataset esperado sem arquivo na listagem **não** vira entrada (evita 404
      diário) e é contado em ``missing``.
    """
    log = logger or logging.getLogger(__name__)
    client = client or PgfnClient()
    report = DiscoveryReport(entries={ds: [] for ds in PGFN_DATASETS})
    trimesters = [t for t in client.discover_trimesters() if _TRIMESTER_RE.match(t)]
    trimesters = [t for t in trimesters if int(t[:4]) >= PGFN_START_YEAR]
    if not trimesters:
        log.warning("PGFN: listagem da raiz vazia/indisponível; usando fallback")
        report.root_failed = True
        report.entries = {
            ds: _build_quarterly_entries_for_dataset(ds, meta)
            for ds, meta in PGFN_DATASETS.items()
        }
        return report
    for tri in trimesters:
        m = _TRIMESTER_RE.match(tri)
        assert m
        year, quarter = int(m.group(1)), int(m.group(2))
        try:
            files = client.list_trimester_files(tri)
        except Exception as exc:
            log.warning("PGFN: listagem de %s falhou (%s); nome fixo", tri, exc)
            report.fallback_trimesters.append(tri)
            for ds, meta in PGFN_DATASETS.items():
                report.entries[ds].append(
                    _entry(ds, meta, year, quarter, _fallback_name(meta))
                )
            continue
        by_ds: dict[str, list[str]] = {}
        for f in files:
            ds = classify_zip(f)
            if ds is not None:
                by_ds.setdefault(ds, []).append(f)
        for ds, meta in PGFN_DATASETS.items():
            found = by_ds.get(ds)
            if not found:
                log.warning("PGFN: %s sem arquivo de %s em %s", ds, tri, files)
                report.missing.append((ds, tri))
                continue
            if len(found) > 1:
                log.warning("PGFN: %s ambíguo em %s: %s", ds, tri, found)
                report.ambiguous.append((ds, tri))
            report.entries[ds].append(_entry(ds, meta, year, quarter, sorted(found)[0]))
    return report


_REPORT: DiscoveryReport | None = None


def refresh_discovery(client: PgfnClient | None = None) -> DiscoveryReport:
    """Executa a descoberta e passa a servir ``list_datasets`` com ela."""
    global _REPORT
    _REPORT = discover_entries(client)
    return _REPORT


def last_discovery() -> DiscoveryReport | None:
    return _REPORT


def _discovery_enabled() -> bool:
    return os.environ.get("PGFN_DISCOVER", "1") not in ("0", "false", "no")


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
    if _REPORT is None and _discovery_enabled():
        refresh_discovery()
    if group is None:
        entries: list[dict[str, Any]] = []
        for g in GROUPS:
            entries.extend(_group_entries(g))
        return entries

    canon = GROUP_ALIASES.get(group, group)
    if canon not in GROUPS:
        raise ValueError(f"Grupo desconhecido: {group!r}")
    return _group_entries(canon)


def _group_entries(group: str) -> list[dict[str, Any]]:
    """Entradas do grupo: da descoberta quando existe, senão do catálogo fixo."""
    if _REPORT is not None and not _REPORT.root_failed:
        return [e.to_dict() for e in _REPORT.entries.get(group, [])]
    return list(GROUPS[group]["entries"])
