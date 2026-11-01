"""Tests for pgfn-fetcher lake converter."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl
from quantilica.analytics.lake import check_dataset

from pgfn_fetcher.lake import converter


def test_converter_metadata() -> None:
    assert converter.source_id == "pgfn"
    datasets = converter.datasets()
    assert "sida" in datasets
    assert "previdenciario" in datasets
    assert "fgts" in datasets


def test_converter_empty_dir(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    res = converter.convert(raw_dir, lake_dir)
    assert res.converted == 0
    assert not res.errors


def test_convert_pgfn_datasets(tmp_path: Path) -> None:
    """Test conversion of sida, previdenciario, and fgts ZIP files."""
    raw_dir = tmp_path / "raw"
    sida_dir = raw_dir / "sida"
    prev_dir = raw_dir / "previdenciario"
    fgts_dir = raw_dir / "fgts"
    sida_dir.mkdir(parents=True)
    prev_dir.mkdir(parents=True)
    fgts_dir.mkdir(parents=True)

    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    # 1. SIDA (cp1252, region 1)
    csv_sida = (
        "CPF_CNPJ;NOME_DEVEDOR;RECEITA_PRINCIPAL;VALOR_CONSOLIDADO\n"
        "12345678000195;EMPRESA ABC;IRPJ;50000,50\n"
        "XXX123.456XX;FULANO SILVA;MULTA;1500,00\n"
    )
    zip_sida = sida_dir / "sida_2024-T3@20261101.zip"
    with zipfile.ZipFile(zip_sida, "w") as zf:
        zf.writestr("arquivo_lai_SIDA_1_202409.csv", csv_sida.encode("cp1252"))

    # 2. Previdenciário (utf-8, region 2)
    csv_prev = (
        "CPF_CNPJ;NOME_DEVEDOR;TIPO_CREDITO;VALOR_CONSOLIDADO\n"
        "98765432000188;EMPRESA XYZ;PREVIDENCIARIO;25000,00\n"
    )
    zip_prev = prev_dir / "previdenciario_2024-T3@20261101.zip"
    with zipfile.ZipFile(zip_prev, "w") as zf:
        zf.writestr("arquivo_lai_PREV_2_202409.csv", csv_prev.encode("utf-8"))

    # 3. FGTS (cp1252, region NA)
    csv_fgts = (
        "CPF_CNPJ;NOME_DEVEDOR;ENTIDADE_RESPONSAVEL;VALOR_CONSOLIDADO\n"
        "11223344000155;EMPRESA FGTS;CAIXA;8000,00\n"
    )
    zip_fgts = fgts_dir / "fgts_2024-T3@20261101.zip"
    with zipfile.ZipFile(zip_fgts, "w") as zf:
        zf.writestr("arquivo_lai_FGTS_NA_202409.csv", csv_fgts.encode("cp1252"))

    res = converter.convert(raw_dir, lake_dir)
    assert res.converted == 3
    assert not res.errors

    # Verify SIDA
    ds_sida = lake_dir / "pgfn" / "sida"
    errors_sida = check_dataset(ds_sida)
    assert not errors_sida, f"check_dataset errors sida: {errors_sida}"
    (part_sida,) = list((ds_sida / "ano=2024" / "trimestre=3").glob("*.parquet"))
    df_sida = pl.read_parquet(part_sida)
    assert df_sida["cnpj_basico"].to_list() == ["12345678", None]
    assert df_sida["regiao_pgfn"].to_list() == ["1", "1"]
    assert df_sida["valor_consolidado"].to_list() == [50000.5, 1500.0]

    # Verify Previdenciário
    ds_prev = lake_dir / "pgfn" / "previdenciario"
    errors_prev = check_dataset(ds_prev)
    assert not errors_prev, f"check_dataset errors prev: {errors_prev}"
    (part_prev,) = list((ds_prev / "ano=2024" / "trimestre=3").glob("*.parquet"))
    df_prev = pl.read_parquet(part_prev)
    assert df_prev["regiao_pgfn"][0] == "2"

    # Verify FGTS
    ds_fgts = lake_dir / "pgfn" / "fgts"
    errors_fgts = check_dataset(ds_fgts)
    assert not errors_fgts, f"check_dataset errors fgts: {errors_fgts}"
    (part_fgts,) = list((ds_fgts / "ano=2024" / "trimestre=3").glob("*.parquet"))
    df_fgts = pl.read_parquet(part_fgts)
    assert df_fgts["regiao_pgfn"][0] == "NA"
