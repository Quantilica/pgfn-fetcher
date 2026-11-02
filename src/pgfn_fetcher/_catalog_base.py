"""Shared types and helper constructors for pgfn-fetcher catalogs."""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DatasetEntry:
    """Represents a single dataset entry to be downloaded."""

    id: str
    base_id: str
    name: str
    url: str
    ext: str
    group: str
    source: str = "pgfn"
    year: int | None = None
    quarter: int | None = None
    month: int | None = None
    slug: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dict."""
        return asdict(self)


@dataclass(frozen=True)
class GroupInfo:
    """Represents a logical group of dataset entries."""

    name: str
    entries: list[DatasetEntry]

    def to_dict(self) -> dict[str, Any]:
        """Convert group to dict."""
        return {
            "name": self.name,
            "entries": [e.to_dict() for e in self.entries],
        }


def static_dataset(
    group: str,
    *,
    id: str,
    name: str,
    url: str,
    ext: str = "csv",
) -> DatasetEntry:
    """Construct a static (single-file) dataset entry."""
    return DatasetEntry(
        id=id,
        base_id=id,
        name=name,
        url=url,
        ext=ext,
        group=group,
    )


def annual_datasets(
    group: str,
    *,
    base_id: str,
    name_template: str,
    url_template: str,
    start_year: int,
    end_year: int | None = None,
    ext: str = "csv",
) -> list[DatasetEntry]:
    """Construct annual dataset entries."""
    end = end_year or dt.date.today().year
    return [
        DatasetEntry(
            id=f"{base_id}_{y}",
            base_id=base_id,
            name=name_template.format(year=y),
            url=url_template.format(year=y),
            ext=ext,
            group=group,
            year=y,
        )
        for y in range(start_year, end + 1)
    ]


def quarterly_datasets(
    group: str,
    *,
    base_id: str,
    name_template: str,
    url_template: str,
    start_year: int,
    end_year: int | None = None,
    end_quarter: int | None = None,
    ext: str = "zip",
) -> list[DatasetEntry]:
    """Construct quarterly dataset entries.

    ``end_quarter`` limita os trimestres do ano final (útil para fontes que só
    publicam trimestre fechado, como a PGFN).
    """
    end = end_year or dt.date.today().year
    entries: list[DatasetEntry] = []
    for y in range(start_year, end + 1):
        max_q = 4
        if end_quarter is not None and y == end:
            max_q = end_quarter
        for q in range(1, max_q + 1):
            entries.append(
                DatasetEntry(
                    id=f"{base_id}_{y}-T{q}",
                    base_id=base_id,
                    name=name_template.format(year=y, quarter=q),
                    url=url_template.format(year=y, quarter=f"{q:02d}"),
                    ext=ext,
                    group=group,
                    year=y,
                    quarter=q,
                )
            )
    return entries
