"""Descoberta do catálogo pela listagem real (fixtures HTML gravadas em 03/11/2026)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pgfn_fetcher import catalog
from pgfn_fetcher.catalog import classify_zip, discover_entries
from pgfn_fetcher.client import parse_zip_links

FIX = Path(__file__).parent / "fixtures" / "listagens"


class FakeHttp:
    """Cliente HTTP falso: serve as listagens gravadas por URL."""

    def __init__(self, pages: dict[str, str], fail: set[str] | None = None) -> None:
        self.pages = pages
        self.fail = fail or set()

    def get(self, url: str):
        key = url.rstrip("/").rsplit("/", 1)[-1]
        if url.rstrip("/").endswith("pgfn.gov.br"):
            key = "raiz"
        if key in self.fail or key not in self.pages:
            raise RuntimeError(f"503 {url}")

        class R:
            text = self.pages[key]

        return R()


def _pages() -> dict[str, str]:
    return {p.stem: p.read_text() for p in FIX.glob("*.html")}


def _client(fail: set[str] | None = None):
    from pgfn_fetcher.client import PgfnClient

    return PgfnClient(client=FakeHttp(_pages(), fail))  # type: ignore[arg-type]


def test_classify_zip_nomes_irregulares() -> None:
    assert classify_zip("Dados_abertos_Nao_Previdenciario.zip") == "sida"
    assert classify_zip("Dados_abertos_Nao_Previdenciariozip.zip") == "sida"
    assert classify_zip("Dados_abertos_Sistema_SIDA.zip") == "sida"
    assert classify_zip("Dados_abertos_Previdenciario.zip") == "previdenciario"
    assert classify_zip("Dados_abertos_FGTS.zip") == "fgts"
    assert classify_zip("leiame.zip") is None


def test_parse_zip_links() -> None:
    html = (FIX / "2026_trimestre_03.html").read_text()
    assert parse_zip_links(html) == [
        "Dados_abertos_FGTS.zip",
        "Dados_abertos_Previdenciario.zip",
        "Dados_abertos_Sistema_SIDA.zip",
    ]


def test_discover_usa_nomes_reais() -> None:
    # só as listagens gravadas existem; os demais trimestres caem no fallback
    rep = discover_entries(_client())
    sida = {e.id: e for e in rep.entries["sida"]}
    assert sida["sida_2026-T3"].url.endswith(
        "/2026_trimestre_03/Dados_abertos_Sistema_SIDA.zip"
    )
    assert sida["sida_2022-T4"].url.endswith(
        "/2022_trimestre_04/Dados_abertos_Nao_Previdenciariozip.zip"
    )
    assert sida["sida_2025-T4"].url.endswith(
        "/2025_trimestre_04/Dados_abertos_Nao_Previdenciario.zip"
    )
    # nunca emite o trimestre inexistente na raiz (2026-T4)
    assert "sida_2026-T4" not in sida
    assert rep.missing == []


def test_fallback_por_trimestre_quando_listagem_falha() -> None:
    rep = discover_entries(_client())
    # trimestres sem fixture => a listagem falhou => nome fixo, contado
    assert "2020_trimestre_01" in rep.fallback_trimesters
    previd = {e.id: e for e in rep.entries["previdenciario"]}
    assert previd["previdenciario_2020-T1"].url.endswith(
        "/2020_trimestre_01/Dados_abertos_Previdenciario.zip"
    )


def test_arquivo_esperado_ausente_e_erro_contado() -> None:
    pages = _pages()
    pages["2026_trimestre_03"] = pages["2026_trimestre_03"].replace(
        "Dados_abertos_FGTS.zip", "outro.txt"
    )
    from pgfn_fetcher.client import PgfnClient

    rep = discover_entries(PgfnClient(client=FakeHttp(pages)))  # type: ignore[arg-type]
    assert ("fgts", "2026_trimestre_03") in rep.missing
    assert rep.errors >= 1
    assert all(e.id != "fgts_2026-T3" for e in rep.entries["fgts"])


def test_raiz_indisponivel_cai_no_catalogo_aritmetico() -> None:
    rep = discover_entries(_client({"raiz"}))
    assert rep.root_failed and rep.errors == 1
    assert rep.entries["sida"][0].id == "sida_2020-T1"


def test_list_datasets_serve_descoberta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(catalog, "_REPORT", catalog.discover_entries(_client()))
    ids = [e["id"] for e in catalog.list_datasets("sida")]
    assert "sida_2026-T3" in ids
    monkeypatch.setattr(catalog, "_REPORT", None)
    ids = [e["id"] for e in catalog.list_datasets("sida")]  # PGFN_DISCOVER=0
    assert "sida_2026-T3" in ids  # catálogo aritmético também chega ao T3
