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


def _lake_rows(dataset_dir: Path) -> pl.DataFrame:
    parts = sorted(dataset_dir.rglob("*.parquet"))
    return pl.concat([pl.read_parquet(p) for p in parts], how="diagonal")


def _multi_member_zip(raw_dir: Path) -> Path:
    header = "CPF_CNPJ;NOME_DEVEDOR;RECEITA_PRINCIPAL;VALOR_CONSOLIDADO\n"
    zip_path = raw_dir / "sida_2024-T3@20261101.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for regiao in (1, 2, 3):
            csv = (
                header
                + f"0234567800019{regiao};DEVEDOR AÇÃO {regiao};IRPJ;10,00\n"
                + f"***.456.789-**;PESSOA {regiao};MULTA;20,50\n"
            )
            zf.writestr(f"arquivo_lai_SIDA_{regiao}_202409.csv", csv.encode("cp1252"))
    return zip_path


def test_zip_multi_membro_preserva_todas_as_linhas(tmp_path: Path) -> None:
    """Regressao A1: membros do mesmo ZIP nao podem se pular entre si."""
    raw_dir = tmp_path / "raw" / "sida"
    raw_dir.mkdir(parents=True)
    _multi_member_zip(raw_dir)
    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    res = converter.convert(tmp_path / "raw", lake_dir)
    assert not res.errors
    assert res.converted == 3
    assert res.skipped == 0

    ds = lake_dir / "pgfn" / "sida"
    assert not check_dataset(ds)
    df = _lake_rows(ds)
    assert df.height == 6
    assert sorted(df["regiao_pgfn"].unique().to_list()) == ["1", "2", "3"]
    # texto como texto: o zero a esquerda do CNPJ sobrevive e o cp1252 e decodificado
    assert "02345678000191" in df["cpf_cnpj"].to_list()
    assert "02345678" in df["cnpj_basico"].to_list()
    assert "DEVEDOR AÇÃO 2" in df["nome_devedor"].to_list()
    assert "�" not in "".join(df["nome_devedor"].to_list())
    assert df["valor_consolidado"].sum() == 3 * 30.5

    # idempotente: segunda rodada pula os 3 membros e nao reconta como convertido
    res2 = converter.convert(tmp_path / "raw", lake_dir)
    assert not res2.errors
    assert (res2.converted, res2.skipped) == (0, 3)
    assert _lake_rows(ds).height == 6


def test_membro_com_byte_invalido_vira_erro_e_nao_substitui(tmp_path: Path) -> None:
    """Previdenciario e UTF-8: byte invalido e erro contado, nunca U+FFFD."""
    raw_dir = tmp_path / "raw" / "previdenciario"
    raw_dir.mkdir(parents=True)
    ok = "CPF_CNPJ;NOME_DEVEDOR;VALOR_CONSOLIDADO\n98765432000188;EMPRESA;1,00\n"
    ruim = b"CPF_CNPJ;NOME_DEVEDOR;VALOR_CONSOLIDADO\n98765432000189;A\xc7\xc3O;1,00\n"
    with zipfile.ZipFile(raw_dir / "previdenciario_2024-T3@20261101.zip", "w") as zf:
        zf.writestr("arquivo_lai_PREV_1_202409.csv", ok.encode("utf-8"))
        zf.writestr("arquivo_lai_PREV_2_202409.csv", ruim)
    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    res = converter.convert(tmp_path / "raw", lake_dir)
    assert res.converted == 1
    assert len(res.errors) == 1
    assert "PREV_2" in res.errors[0]
    df = _lake_rows(lake_dir / "pgfn" / "previdenciario")
    assert df.height == 1
    assert df["regiao_pgfn"].to_list() == ["1"]


def test_leitura_nao_carrega_o_membro_inteiro(tmp_path: Path, monkeypatch) -> None:
    """O membro e lido em blocos (zf.open), nunca com ZipFile.read."""

    def _proibido(self, *args, **kwargs):
        raise AssertionError("ZipFile.read carrega o membro inteiro na memoria")

    monkeypatch.setattr(zipfile.ZipFile, "read", _proibido)
    raw_dir = tmp_path / "raw" / "sida"
    raw_dir.mkdir(parents=True)
    _multi_member_zip(raw_dir)
    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    res = converter.convert(tmp_path / "raw", lake_dir)
    assert not res.errors
    assert res.converted == 3


def test_periodo_nao_inferido_e_erro_e_nao_2020_t1(tmp_path: Path) -> None:
    raw_dir = tmp_path / "raw" / "sida"
    raw_dir.mkdir(parents=True)
    with zipfile.ZipFile(raw_dir / "sida_sem_periodo@20261101.zip", "w") as zf:
        zf.writestr("arquivo_lai_SIDA_1_x.csv", b"CPF_CNPJ;VALOR_CONSOLIDADO\n1;2\n")
    lake_dir = tmp_path / "lake"
    lake_dir.mkdir()

    res = converter.convert(tmp_path / "raw", lake_dir)
    assert res.converted == 0
    assert len(res.errors) == 1
    assert not list(lake_dir.rglob("*.parquet"))
