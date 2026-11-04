"""Pytest configuration and fixtures for pgfn-fetcher."""

import os

# Os testes são offline: a descoberta de catálogo (rede) fica desligada por padrão.
os.environ.setdefault("PGFN_DISCOVER", "0")
