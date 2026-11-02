"""Tests for pgfn-fetcher catalog."""

from __future__ import annotations

import datetime as dt

import pytest

from pgfn_fetcher.catalog import GROUP_ALIASES, GROUPS, list_datasets


def test_nao_cataloga_trimestre_futuro() -> None:
    """O catálogo para no último trimestre fechado (a PGFN publica depois)."""
    today = dt.date.today()
    quarter = (today.month - 1) // 3 + 1
    if quarter == 1:
        esperado = f"{today.year - 1}-T4"
    else:
        esperado = f"{today.year}-T{quarter - 1}"
    for group in GROUPS:
        ultimo = list_datasets(group)[-1]["id"]
        assert ultimo.endswith(esperado), (group, ultimo, esperado)


def test_list_datasets_all() -> None:
    """Test listing all datasets."""
    datasets = list_datasets()
    assert isinstance(datasets, list)


def test_list_datasets_by_group() -> None:
    """Test listing datasets by valid and invalid group."""
    for group in GROUPS:
        entries = list_datasets(group)
        assert isinstance(entries, list)

    for alias in GROUP_ALIASES:
        entries = list_datasets(alias)
        assert isinstance(entries, list)

    with pytest.raises(ValueError, match="Grupo desconhecido"):
        list_datasets("grupo_inexistente_xyz")
