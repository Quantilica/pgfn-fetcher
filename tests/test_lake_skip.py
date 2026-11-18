"""O build do lake pula, sem ler o bruto, o que já está em dia."""

from __future__ import annotations

import builtins
import hashlib
import json
import zipfile
from pathlib import Path

import polars as pl
import pytest
import quantilica.core.manifests as manifests_mod

import pgfn_fetcher.lake as lake_mod
from pgfn_fetcher.lake import converter

_HEADER = "CPF_CNPJ;NOME_DEVEDOR;RECEITA_PRINCIPAL;VALOR_CONSOLIDADO\n"


def _zip(path: Path, regioes: tuple[int, ...] = (1, 2, 3), extra: str = "") -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for r in regioes:
            csv = _HEADER + f"0234567800019{r};DEVEDOR AÇÃO {r};IRPJ;10,00\n" + extra
            zf.writestr(f"arquivo_lai_SIDA_{r}_202409.csv", csv.encode("cp1252"))


def _sidecars(raiz: Path) -> None:
    """Sidecar ``.manifest.json`` com o sha256 de cada bruto, como o fetcher grava:
    o hash do bruto sai dele, sem ler o arquivo."""
    for f in sorted(raiz.rglob("*")):
        if f.is_file() and not f.name.endswith(".manifest.json"):
            Path(f"{f}.manifest.json").write_text(
                json.dumps(
                    {
                        "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                        "size_bytes": f.stat().st_size,
                    }
                ),
                encoding="utf-8",
            )


def _bruto(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    (raw / "sida").mkdir(parents=True)
    (raw / "previdenciario").mkdir()
    _zip(raw / "sida" / "sida_2024-T3@20261101.zip")
    with zipfile.ZipFile(
        raw / "previdenciario" / "previdenciario_2024-T3@20261101.zip", "w"
    ) as zf:
        zf.writestr(
            "arquivo_lai_PREV_1_202409.csv",
            (_HEADER + "02345678000195;PREV;FGTS;5,00\n").encode("cp1252"),
        )
    _sidecars(raw)
    return raw


@pytest.fixture
def leituras(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[str]:
    """Registra toda abertura/leitura do bruto: ZIP, open, transcodificação, scan."""
    vistas: list[str] = []
    raiz = str(tmp_path / "raw")

    def espia(nome: str, original):  # noqa: ANN001, ANN202
        def _f(*args, **kwargs):  # noqa: ANN002, ANN003
            vistas.append(nome)
            return original(*args, **kwargs)

        return _f

    original_open = builtins.open

    def open_espiado(file, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        if str(file).startswith(raiz):
            vistas.append(f"open:{file}")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", open_espiado)
    monkeypatch.setattr(zipfile, "ZipFile", espia("zipfile", zipfile.ZipFile))
    for nome in ("_member_as_utf8", "_csv_member_names", "_member_frame"):
        monkeypatch.setattr(lake_mod, nome, espia(nome, getattr(lake_mod, nome)))
    monkeypatch.setattr(pl, "scan_csv", espia("scan_csv", pl.scan_csv))
    monkeypatch.setattr(
        manifests_mod, "sha256_file", espia("hash", manifests_mod.sha256_file)
    )
    return vistas


@pytest.mark.parametrize(
    ("dataset", "convertidos"), [("sida", 3), ("previdenciario", 1), (None, 4)]
)
def test_segunda_rodada_nao_le_o_bruto(
    tmp_path: Path, leituras: list[str], dataset: str | None, convertidos: int
) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    datasets = [dataset] if dataset else None

    r1 = converter.convert(raw, lake, datasets=datasets)
    assert not r1.errors
    assert (r1.converted, r1.skipped) == (convertidos, 0)
    assert leituras  # a primeira rodada le o bruto

    leituras.clear()
    r2 = converter.convert(raw, lake, datasets=datasets)
    assert (r2.converted, r2.skipped, r2.errors) == (0, convertidos, [])
    assert leituras == []


def test_um_dataset_nao_toca_o_bruto_de_outro(
    tmp_path: Path, leituras: list[str]
) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    converter.convert(raw, lake, datasets=["previdenciario"])
    assert not any("sida_2024" in v for v in leituras)


def test_force_reconverte(tmp_path: Path, leituras: list[str]) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    converter.convert(raw, lake, datasets=["sida"])
    leituras.clear()

    r = converter.convert(raw, lake, datasets=["sida"], force=True)
    assert (r.converted, r.skipped, r.errors) == (3, 0, [])
    assert "_member_as_utf8" in leituras


def test_bruto_novo_converte_e_o_antigo_segue_em_dia(
    tmp_path: Path, leituras: list[str]
) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    converter.convert(raw, lake, datasets=["sida"])

    _zip(raw / "sida" / "sida_2024-T4@20261201.zip", regioes=(1,))
    _sidecars(raw)
    leituras.clear()

    r = converter.convert(raw, lake, datasets=["sida"])
    assert (r.converted, r.skipped, r.errors) == (1, 3, [])
    abertos = [v for v in leituras if v.startswith("open:")]
    assert abertos
    assert all("2024-T4" in v for v in abertos)

    leituras.clear()
    r3 = converter.convert(raw, lake, datasets=["sida"])
    assert (r3.converted, r3.skipped, r3.errors) == (0, 4, [])
    assert leituras == []


def test_bruto_alterado_no_lugar_reconverte(tmp_path: Path) -> None:
    raw, lake = _bruto(tmp_path), tmp_path / "lake"
    converter.convert(raw, lake, datasets=["sida"])

    _zip(raw / "sida" / "sida_2024-T3@20261101.zip", extra="***.456.789-**;X;M;1,00\n")
    r = converter.convert(raw, lake, datasets=["sida"])
    assert (r.converted, r.skipped, r.errors) == (3, 0, [])


def test_periodo_nao_inferido_segue_sendo_erro(tmp_path: Path) -> None:
    raw = tmp_path / "raw" / "sida"
    raw.mkdir(parents=True)
    _zip(raw / "sida@20261101.zip")
    r = converter.convert(tmp_path / "raw", tmp_path / "lake", datasets=["sida"])
    assert len(r.errors) == 1
    assert "ano/trimestre" in r.errors[0]
