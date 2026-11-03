"""Tests for pgfn-fetcher storage module."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from pgfn_fetcher.storage import DataRepository


def test_path_for_entry_fallback_timestamp() -> None:
    """When last_modified=None, the filename gets today's @YYYYMMDD timestamp."""
    repo = DataRepository(Path("/tmp/test"))
    entry = {
        "group": "pgfn",
        "base_id": "test_dataset",
        "ext": "csv",
    }
    today = dt.date.today()
    expected_stamp = today.strftime("%Y%m%d")

    path = repo.path_for_entry(entry, last_modified=None)

    # The filename should contain today's date as @YYYYMMDD
    assert f"@{expected_stamp}.csv" in path.name
    assert path.name == f"test_dataset@{expected_stamp}.csv"


def test_path_for_entry_with_year_month() -> None:
    """When entry has year and month, partition includes them with timestamp."""
    repo = DataRepository(Path("/tmp/test"))
    entry = {
        "group": "pgfn",
        "base_id": "test_dataset",
        "ext": "csv",
        "year": 2024,
        "month": 3,
    }
    today = dt.date.today()
    expected_stamp = today.strftime("%Y%m%d")

    path = repo.path_for_entry(entry, last_modified=None)

    assert path.name == f"test_dataset_2024-03@{expected_stamp}.csv"


def test_path_for_entry_with_year_quarter() -> None:
    """When entry has year and quarter, partition includes them with timestamp."""
    repo = DataRepository(Path("/tmp/test"))
    entry = {
        "group": "pgfn",
        "base_id": "test_dataset",
        "ext": "csv",
        "year": 2024,
        "quarter": 1,
    }
    today = dt.date.today()
    expected_stamp = today.strftime("%Y%m%d")

    path = repo.path_for_entry(entry, last_modified=None)

    assert path.name == f"test_dataset_2024-T01@{expected_stamp}.csv"


def test_path_for_entry_with_year_only() -> None:
    """When entry has only year, partition is the year with timestamp."""
    repo = DataRepository(Path("/tmp/test"))
    entry = {
        "group": "pgfn",
        "base_id": "test_dataset",
        "ext": "csv",
        "year": 2024,
    }
    today = dt.date.today()
    expected_stamp = today.strftime("%Y%m%d")

    path = repo.path_for_entry(entry, last_modified=None)

    assert path.name == f"test_dataset_2024@{expected_stamp}.csv"


def test_path_for_entry_with_slug() -> None:
    """When entry has slug, it's included in partition with timestamp."""
    repo = DataRepository(Path("/tmp/test"))
    entry = {
        "group": "pgfn",
        "base_id": "test_dataset",
        "ext": "csv",
        "year": 2024,
        "month": 3,
        "slug": "custom",
    }
    today = dt.date.today()
    expected_stamp = today.strftime("%Y%m%d")

    path = repo.path_for_entry(entry, last_modified=None)

    assert path.name == f"test_dataset_2024-03_custom@{expected_stamp}.csv"


def test_path_for_entry_explicit_timestamp() -> None:
    """When last_modified is provided, it's used instead of today."""
    repo = DataRepository(Path("/tmp/test"))
    entry = {
        "group": "pgfn",
        "base_id": "test_dataset",
        "ext": "csv",
    }
    explicit_date = dt.date(2023, 6, 15)

    path = repo.path_for_entry(entry, last_modified=explicit_date)

    assert path.name == "test_dataset@20230615.csv"