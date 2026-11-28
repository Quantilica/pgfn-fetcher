"""Typer plugin for quantilica-cli integration."""

from __future__ import annotations

import datetime as dt
import functools
from pathlib import Path
from typing import Any

from quantilica.cli.sdk import CheckPlanItem, FetcherApp, make_resolve_groups
from quantilica.core.registry import FetcherInfo
from quantilica.core.sync import FreshnessPolicy

from .catalog import (
    GROUP_ALIASES,
    GROUPS,
    DiscoveryFailure,
    group_failures,
    list_datasets,
)
from .storage import DataRepository

LISTING_ERROR_TYPE = "listing-error"
# Mesmo valor de ``quantilica.cli.sdk.LISTING_ERROR_REASON`` (host >= 0.30.1), que
# conta o item como erro no ``sync --from-plan``; definido aqui para não exigir
# o nome do host mais novo.
LISTING_ERROR_REASON = "listing-error"
# Verdadeiro só dentro do ``check`` (ver ``_tolerar_falha_de_descoberta``): lá cada
# dataset/trimestre sem arquivo na listagem vira uma entrada sentinela, que o
# ``check_entry`` devolve como ``skip-unavailable``/``listing-error``. No ``sync``
# direto a falha vira o erro ``descoberta:<dataset>:<trimestre>`` do
# ``download_datasets``.
_TOLERANT_LISTING = False

resolve_groups = make_resolve_groups(
    GROUPS, {alias: [canon] for alias, canon in GROUP_ALIASES.items()}
)


def path_builder(
    output_dir: Path, entry: dict[str, Any], last_modified: dt.date | None
) -> Path:
    """Build local storage path for a dataset entry."""
    return DataRepository(output_dir).path_for_entry(entry, last_modified=last_modified)


def _sentinela(falha: DiscoveryFailure) -> dict[str, Any]:
    """Entrada sentinela de uma descoberta que falhou (vai ao plano do ``check``)."""
    return {
        "id": f"{LISTING_ERROR_TYPE}:{falha.dataset}:{falha.item}",
        "group": falha.dataset,
        "dataset": falha.dataset,
        "url": falha.url,
        "type": LISTING_ERROR_TYPE,
        "error": falha.error,
        "error_class": falha.error_class,
    }


class PgfnApp(FetcherApp):
    """``FetcherApp`` da PGFN.

    Faz a falha de descoberta (trimestre cujo ZIP do dataset não está mais na
    listagem, por exemplo porque mudou de nome) aparecer: sem isso o trimestre
    simplesmente saía do catálogo e o ``sync`` saía 0.

    - ``sync`` direto: soma ao resultado um erro ``descoberta:<dataset>:<trimestre>``
      por falha (saída 3 se algo baixou, 1 se nada baixou).
    - ``check``: cada falha vira um item ``skip-unavailable``/``listing-error`` do
      plano (o ``check`` sai 0 e grava o plano dos demais); o ``sync --from-plan``
      do host (``quantilica-cli`` 0.30.1) conta o item como erro.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        #: dataset -> falhas de descoberta vistas ao listar os grupos pedidos.
        self._falhas_descoberta: dict[str, list[DiscoveryFailure]] = {}
        self.list_datasets = self.listar_grupo

    def listar_grupo(self, group: str) -> list[dict[str, Any]]:
        """``list_datasets`` que registra as falhas de descoberta do grupo pedido."""
        entries = list_datasets(group)
        canon = GROUP_ALIASES.get(group, group)
        falhas = group_failures(canon)
        if not falhas:
            self._falhas_descoberta.pop(canon, None)
        elif _TOLERANT_LISTING:
            entries = [*entries, *(_sentinela(f) for f in falhas)]
        else:
            self._falhas_descoberta[canon] = falhas
        return entries

    def download_datasets(
        self,
        entries: list[dict[str, Any]],
        output_dir: Path,
        workers: int = 4,
        *,
        force: bool = False,
    ) -> tuple[int, int, list[tuple[str, str]]]:
        """Baixa as entradas e soma, aos erros, as falhas de descoberta pendentes."""
        pendentes, self._falhas_descoberta = self._falhas_descoberta, {}
        downloaded, total, errors = super().download_datasets(
            entries, output_dir, workers, force=force
        )
        erros = [
            (f"descoberta:{f.dataset}:{f.item}", f.error)
            for grupo in sorted(pendentes)
            for f in pendentes[grupo]
        ]
        return downloaded, total + len(erros), [*errors, *erros]

    def check_entry(self, entry: dict[str, Any], output_dir: Path) -> CheckPlanItem:
        """Veredito do host; a sentinela de descoberta vira ``listing-error``."""
        if entry.get("type") == LISTING_ERROR_TYPE:
            # Sobrevive à reclassificação do plano (``skip-unavailable`` é mantido)
            # e é contado como erro pelo ``sync --from-plan`` do host.
            return CheckPlanItem(
                dataset=str(entry.get("group") or "datasets"),
                id=str(entry.get("id", "unknown")),
                url=str(entry.get("url", "")),
                partition=None,
                local_path="",
                remote_etag=None,
                remote_last_modified=None,
                remote_size=None,
                local_exists=False,
                action="skip-unavailable",
                reason=LISTING_ERROR_REASON,
                entry=dict(entry),
            )
        return super().check_entry(entry, output_dir)


fetcher = PgfnApp(
    name="pgfn",
    help="Coletor e conversor Lake Hive de dados abertos da dívida ativa da PGFN",
    info=FetcherInfo(
        id="pgfn",
        nome="PGFN - Dívida Ativa da União e FGTS",
        orgao="Procuradoria-Geral da Fazenda Nacional (PGFN)",
        licenca=(
            "Sem licença declarada; dados públicos pela Lei 12.527/2011 (LAI) "
            "e Decreto 8.777/2016"
        ),
        homepage="https://dadosabertos.pgfn.gov.br",
        cadencia="quarterly",
        dominio="fiscal",
    ),
    groups_dict=GROUPS,
    aliases_dict=GROUP_ALIASES,
    list_datasets=list_datasets,
    path_builder=path_builder,
    default_output=Path("/data/pgfn"),
    freshness_policy=FreshnessPolicy.HEAD_FALLBACK_GET,
)


def _tolerar_falha_de_descoberta(callback: Any) -> Any:
    """Roda o ``check`` do host com a falha de descoberta tolerada.

    O ``check`` é a primeira etapa da coleta em modo de plano: se um trimestre
    cujo arquivo mudou de nome derrubasse o ``check``, não haveria plano e a coleta
    cairia no ``sync`` completo. Com a tolerância, a falha vira um item
    ``skip-unavailable``/``listing-error``; o plano dos demais é gravado e o
    ``sync --from-plan`` conta a falha nos erros (saída 3 ou 1).
    """

    @functools.wraps(callback)
    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        global _TOLERANT_LISTING
        anterior, _TOLERANT_LISTING = _TOLERANT_LISTING, True
        try:
            return callback(*args, **kwargs)
        finally:
            _TOLERANT_LISTING = anterior

    return _wrapper


for _info in fetcher.app.registered_commands:
    if _info.name == "check" and _info.callback is not None:
        _info.callback = _tolerar_falha_de_descoberta(_info.callback)


def convert(
    input_dir: Path,
    lake_dir: Path,
    *,
    dataset: list[str] | None = None,
    force: bool = False,
) -> Any:
    """Converte arquivos brutos de pgfn para o lake Hive (Parquet)."""
    try:
        from pgfn_fetcher import lake
    except ImportError as exc:
        raise ImportError(
            "Conversão para o lake requer o extra 'analysis'. "
            "Instale com: quantilica install pgfn --extra analysis"
        ) from exc
    return lake.converter.convert(input_dir, lake_dir, datasets=dataset, force=force)


fetcher.command_convert(convert)
fetcher.command_pipeline(convert)


app = fetcher.app
