"""Constants and definitions for pgfn-fetcher."""

from __future__ import annotations

from typing import Any

PGFN_BASE_URL = "https://dadosabertos.pgfn.gov.br"
PGFN_START_YEAR = 2020

PGFN_DATASETS: dict[str, dict[str, Any]] = {
    "sida": {
        "name": "Dívida Ativa Não-Previdenciária (SIDA)",
        "file_kind": "Nao_Previdenciario",
        "encoding": "cp1252",
        "group": "sida",
    },
    "previdenciario": {
        "name": "Dívida Ativa Previdenciária",
        "file_kind": "Previdenciario",
        "encoding": "utf-8",
        "group": "previdenciario",
    },
    "fgts": {
        "name": "Dívida Ativa do FGTS",
        "file_kind": "FGTS",
        "encoding": "cp1252",
        "group": "fgts",
    },
}
