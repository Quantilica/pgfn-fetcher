"""Falha de descoberta vira erro do ``sync`` e item do plano do ``check`` (sem rede)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from quantilica.cli import sdk
from quantilica.cli.sdk import CheckPlanItem, FetcherApp
from test_discovery import FakeHttp, _pages
from typer.testing import CliRunner

from pgfn_fetcher import catalog, plugin
from pgfn_fetcher.client import PgfnClient
from pgfn_fetcher.plugin import app, fetcher

runner = CliRunner()

# O host de 0.30.1 em diante conta o item ``listing-error`` do plano como erro.
host_conta_listing_error = pytest.mark.skipif(
    not hasattr(sdk, "plan_listing_errors"),
    reason="quantilica-cli < 0.30.1 não conta o item listing-error no --from-plan",
)


@pytest.fixture(autouse=True)
def estado_limpo(monkeypatch: pytest.MonkeyPatch) -> None:
    """O app é um singleton: ``list``/``check`` de outros testes anotam falhas."""
    fetcher._falhas_descoberta.clear()
    monkeypatch.setattr(catalog, "_REPORT", None)


@pytest.fixture
def fgts_sumiu(monkeypatch: pytest.MonkeyPatch) -> None:
    """Descoberta em que o FGTS de 2026-T3 deixou de estar na listagem."""
    pages = _pages()
    pages["2026_trimestre_03"] = pages["2026_trimestre_03"].replace(
        "Dados_abertos_FGTS.zip", "FGTS_novo.txt"
    )
    report = catalog.discover_entries(
        PgfnClient(client=FakeHttp(pages))  # type: ignore[arg-type]
    )
    monkeypatch.setattr(catalog, "_REPORT", report)


@pytest.fixture
def download_simulado(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Sem rede: o download de cada entrada dá certo e anota o id."""
    baixados: list[str] = []

    def baixa(self: Any, entry: dict, output_dir: Path, **kw: Any) -> Path:
        baixados.append(entry["id"])
        return output_dir / entry["id"]

    monkeypatch.setattr(FetcherApp, "download_entry", baixa)
    return baixados


@pytest.fixture(autouse=True)
def head_simulado(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem rede: o veredito do host para uma entrada normal é 'baixar'."""

    def veredito(self: Any, entry: dict, output_dir: Path) -> CheckPlanItem:
        return CheckPlanItem(
            dataset=str(entry["group"]),
            id=str(entry["id"]),
            url=str(entry["url"]),
            partition=None,
            local_path="",
            remote_etag=None,
            remote_last_modified=None,
            remote_size=None,
            local_exists=False,
            action="download",
            reason="not-present",
            entry=dict(entry),
        )

    monkeypatch.setattr(FetcherApp, "check_entry", veredito)


def _sync(tmp_path: Path, *grupos: str):
    resumo = tmp_path / "resumo.json"
    res = runner.invoke(
        app,
        ["sync", *grupos, "-o", str(tmp_path / "bruto"), "--summary-json", str(resumo)],
    )
    dados = json.loads(resumo.read_text()) if resumo.exists() else None
    return res, dados


def _check(tmp_path: Path, *grupos: str):
    plano = tmp_path / "plano.json"
    res = runner.invoke(
        app, ["check", *grupos, "-o", str(tmp_path / "bruto"), "--out", str(plano)]
    )
    return res, plano


def test_sync_sem_falha_sai_0(tmp_path: Path, download_simulado: list[str]) -> None:
    res, resumo = _sync(tmp_path, "fgts")
    assert res.exit_code == 0, res.output
    assert resumo is not None and resumo["errors"] == []


@pytest.mark.usefixtures("fgts_sumiu")
def test_sync_com_trimestre_sumido_sai_3_com_o_erro(
    tmp_path: Path, download_simulado: list[str]
) -> None:
    res, resumo = _sync(tmp_path, "fgts")
    assert res.exit_code == 3, res.output
    assert download_simulado  # os demais trimestres do dataset baixaram
    assert "fgts_2026-T3" not in download_simulado
    assert resumo is not None
    (erro,) = resumo["errors"]
    assert erro["id"] == "descoberta:fgts:2026_trimestre_03"
    assert "Dados_abertos_Previdenciario.zip" in erro["message"]
    assert resumo["failed"] == 1


@pytest.mark.usefixtures("fgts_sumiu")
def test_falha_so_vale_para_o_dataset_pedido(
    tmp_path: Path, download_simulado: list[str]
) -> None:
    res, resumo = _sync(tmp_path, "sida")  # o sumido é o FGTS
    assert res.exit_code == 0, res.output
    assert resumo is not None and resumo["errors"] == []


@pytest.mark.usefixtures("fgts_sumiu")
def test_apelido_do_grupo_tambem_conta(
    tmp_path: Path, download_simulado: list[str]
) -> None:
    fetcher._falhas_descoberta.clear()
    assert fetcher.listar_grupo("fgts")
    assert list(fetcher._falhas_descoberta) == ["fgts"]
    fetcher._falhas_descoberta.clear()
    fetcher.listar_grupo("tributaria")  # alias de sida: sem falha
    assert fetcher._falhas_descoberta == {}


@pytest.mark.usefixtures("fgts_sumiu")
def test_falha_nao_vaza_para_o_download_seguinte(tmp_path: Path) -> None:
    fetcher.listar_grupo("fgts")
    assert fetcher._falhas_descoberta
    _, total, erros = fetcher.download_datasets([], tmp_path)
    assert total == 1 and len(erros) == 1
    assert fetcher._falhas_descoberta == {}
    assert fetcher.download_datasets([], tmp_path) == (0, 0, [])


@pytest.mark.usefixtures("fgts_sumiu")
def test_check_com_falha_sai_0_e_grava_o_item_no_plano(tmp_path: Path) -> None:
    """A falha vira ``skip-unavailable``/``listing-error``; o plano dos demais fica."""
    res, plano = _check(tmp_path, "fgts")
    assert res.exit_code == 0, res.output
    itens = json.loads(plano.read_text())["items"]
    por_id = {i["id"]: i for i in itens}
    erro = por_id["listing-error:fgts:2026_trimestre_03"]
    assert erro["action"] == "skip-unavailable"
    assert erro["reason"] == "listing-error"
    assert erro["dataset"] == "fgts"
    assert erro["url"].endswith("/2026_trimestre_03/")
    assert erro["entry"]["error_class"] == "ArquivoAusente"
    assert "Dados_abertos_Previdenciario.zip" in erro["entry"]["error"]
    assert any(i["action"] == "download" for i in itens)  # plano dos demais
    assert fetcher._falhas_descoberta == {}  # o check não deixa pendência


@host_conta_listing_error
@pytest.mark.usefixtures("fgts_sumiu")
def test_plano_e_sync_from_plan_saem_3_com_o_erro(
    tmp_path: Path, download_simulado: list[str]
) -> None:
    res, plano = _check(tmp_path, "fgts")
    assert res.exit_code == 0
    fetcher._falhas_descoberta.clear()
    resumo = tmp_path / "resumo.json"
    res = runner.invoke(
        app,
        [
            "sync",
            "--from-plan",
            str(plano),
            "-o",
            str(tmp_path / "bruto"),
            "--summary-json",
            str(resumo),
        ],
    )
    assert res.exit_code == 3, res.output
    assert download_simulado
    (erro,) = json.loads(resumo.read_text())["errors"]
    assert erro["id"] == "listing-error:fgts:2026_trimestre_03"
    assert erro["message"].startswith("ArquivoAusente: ")


@pytest.mark.usefixtures("fgts_sumiu")
def test_tolerancia_so_vale_dentro_do_check(tmp_path: Path) -> None:
    assert plugin._TOLERANT_LISTING is False
    _check(tmp_path, "fgts")
    assert plugin._TOLERANT_LISTING is False  # restaurada
    entradas = fetcher.listar_grupo("fgts")
    assert all(e.get("type") != "listing-error" for e in entradas)


def test_check_sem_falha_nao_tem_item_de_erro(tmp_path: Path) -> None:
    res, plano = _check(tmp_path, "fgts")
    assert res.exit_code == 0, res.output
    itens = json.loads(plano.read_text())["items"]
    assert itens and all(i["reason"] != "listing-error" for i in itens)
