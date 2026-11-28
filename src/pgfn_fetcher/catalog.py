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
    "DiscoveryFailure",
    "DiscoveryReport",
    "classify_zip",
    "discover_entries",
    "DatasetEntry",
    "GroupInfo",
    "GROUPS",
    "GROUP_ALIASES",
    "group_failures",
    "last_discovery",
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


@dataclass(frozen=True)
class DiscoveryFailure:
    """Um (dataset, trimestre) que a descoberta não conseguiu resolver."""

    dataset: str
    #: diretório do trimestre (``2026_trimestre_03``).
    item: str
    url: str
    error: str
    error_class: str = "ArquivoAusente"


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
    #: (dataset, trimestre) ambíguo -> arquivos candidatos, em ordem alfabética.
    ambiguous_files: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    root_failed: bool = False
    #: causa da falha da raiz (exceção ou listagem sem diretório de trimestre).
    root_error: str | None = None
    #: um por item de ``missing``, com a causa (falha de descoberta do dataset).
    failures: list[DiscoveryFailure] = field(default_factory=list)

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
      diário), é contado em ``missing`` e registrado em ``failures`` (o plugin o
      leva ao ``check`` e ao ``sync`` como falha de descoberta).
    - Raiz que falha (``root_failed``) segue com o catálogo aritmético, mas a causa
      fica em ``root_error`` e no log (WARNING). O mesmo para ``ambiguous`` e
      ``fallback_trimesters``: o resumo vai ao log, nada some em silêncio.
    """
    log = logger or logging.getLogger(__name__)
    client = client or PgfnClient()
    report = DiscoveryReport(entries={ds: [] for ds in PGFN_DATASETS})
    try:
        found_dirs = client.discover_trimesters()
    except Exception as exc:  # noqa: BLE001 - a causa vai para o relatório e o log
        found_dirs = []
        report.root_error = f"{type(exc).__name__}: {exc}"
    trimesters = [t for t in found_dirs if _TRIMESTER_RE.match(t)]
    trimesters = [t for t in trimesters if int(t[:4]) >= PGFN_START_YEAR]
    if not trimesters:
        report.root_failed = True
        if report.root_error is None:
            report.root_error = (
                "a listagem da raiz não traz nenhum diretório de trimestre "
                f"(a partir de {PGFN_START_YEAR})"
            )
        report.entries = {
            ds: _build_quarterly_entries_for_dataset(ds, meta)
            for ds, meta in PGFN_DATASETS.items()
        }
        _log_summary(report, log)
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
                report.missing.append((ds, tri))
                report.failures.append(
                    DiscoveryFailure(
                        dataset=ds,
                        item=tri,
                        url=f"{PGFN_BASE_URL}/{tri}/",
                        error=(
                            f"nenhum arquivo do dataset {ds} em {tri} "
                            f"(publicados: {', '.join(files) or 'nenhum .zip'})"
                        ),
                    )
                )
                continue
            chosen = sorted(found)[0]
            if len(found) > 1:
                report.ambiguous.append((ds, tri))
                report.ambiguous_files[(ds, tri)] = sorted(found)
            report.entries[ds].append(_entry(ds, meta, year, quarter, chosen))
    _log_summary(report, log)
    return report


def _log_summary(report: DiscoveryReport, log: logging.Logger) -> None:
    """Uma linha de WARNING por tipo de problema, com os itens (nada some)."""
    if report.root_failed:
        log.warning(
            "PGFN: listagem da raiz sem resultado (%s); usando o catálogo "
            "aritmético de reserva (nomes fixos, sem conferir o que a fonte "
            "publica): um arquivo renomeado só aparece como 404 no download",
            report.root_error,
        )
    if report.fallback_trimesters:
        log.warning(
            "PGFN: %d trimestre(s) sem listagem, com nome fixo: %s",
            len(report.fallback_trimesters),
            ", ".join(report.fallback_trimesters),
        )
    if report.missing:
        log.warning(
            "PGFN: %d dataset(s) esperado(s) sem arquivo na listagem do "
            "trimestre (falha de descoberta, fora do catálogo): %s",
            len(report.missing),
            "; ".join(f"{ds} em {tri}" for ds, tri in report.missing),
        )
    if report.ambiguous:
        log.warning(
            "PGFN: %d dataset(s) com mais de um arquivo no trimestre; usa o "
            "primeiro em ordem alfabética: %s",
            len(report.ambiguous),
            "; ".join(
                f"{ds} em {tri}: {', '.join(report.ambiguous_files[(ds, tri)])}"
                for ds, tri in report.ambiguous
            ),
        )


_REPORT: DiscoveryReport | None = None


def refresh_discovery(client: PgfnClient | None = None) -> DiscoveryReport:
    """Executa a descoberta e passa a servir ``list_datasets`` com ela."""
    global _REPORT
    _REPORT = discover_entries(client)
    return _REPORT


def last_discovery() -> DiscoveryReport | None:
    return _REPORT


def group_failures(group: str) -> list[DiscoveryFailure]:
    """Falhas de descoberta do dataset (``missing``) da última listagem."""
    canon = GROUP_ALIASES.get(group, group)
    if _REPORT is None:
        return []
    return [f for f in _REPORT.failures if f.dataset == canon]


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
