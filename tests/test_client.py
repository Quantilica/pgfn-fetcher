"""Tests for PgfnClient."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx2
import pytest
from quantilica.core.exceptions import CorruptPayloadError
from quantilica.core.http import HttpClient

from pgfn_fetcher.client import PgfnClient


def test_client_init() -> None:
    client = PgfnClient()
    assert client.base_url == "https://dadosabertos.pgfn.gov.br"


def test_discover_trimesters() -> None:
    client = PgfnClient()
    html_sample = (
        "<html><body>"
        '<a href="2020_trimestre_01/">2020_trimestre_01/</a>'
        '<a href="2024_trimestre_03/">2024_trimestre_03/</a>'
        "</body></html>"
    )
    mock_resp = MagicMock()
    mock_resp.text = html_sample
    with patch.object(client.client, "get", return_value=mock_resp):
        res = client.discover_trimesters()
        assert res == ["2020_trimestre_01", "2024_trimestre_03"]


def test_discover_trimesters_levanta_quando_a_raiz_falha() -> None:
    """Falha não é lista vazia: quem chama decide (catálogo de reserva + aviso)."""
    client = PgfnClient()
    with (
        patch.object(client.client, "get", side_effect=RuntimeError("503")),
        pytest.raises(RuntimeError),
    ):
        client.discover_trimesters()


def test_discover_trimesters_raiz_sem_diretorios_e_lista_vazia() -> None:
    client = PgfnClient()
    mock_resp = MagicMock()
    mock_resp.text = "<html><body>manutenção</body></html>"
    with patch.object(client.client, "get", return_value=mock_resp):
        assert client.discover_trimesters() == []


def test_cliente_padrao_respeita_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    """O cliente da descoberta vem do cliente padrão do host (``QUANTILICA_HTTP_*``)."""
    monkeypatch.setenv("QUANTILICA_HTTP_TIMEOUT", "12")
    monkeypatch.setenv("QUANTILICA_HTTP_ATTEMPTS", "2")
    client = PgfnClient()
    assert client.client.timeout == 12.0
    assert client.client.attempts == 2


def _client_with(handler) -> PgfnClient:
    http = HttpClient(
        attempts=1, retry_base_delay=0.0, transport=httpx2.MockTransport(handler)
    )
    return PgfnClient(client=http)


def _zip_bytes(path: Path) -> bytes:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("arquivo_lai_SIDA_1_202409.csv", "CPF_CNPJ;VALOR\n1;2\n")
    return path.read_bytes()


def test_download_file_real_sem_mock_do_core(tmp_path: Path) -> None:
    """A assinatura chama o ``download_with_manifest`` de verdade (sem mock)."""
    body = _zip_bytes(tmp_path / "origem.zip")
    client = _client_with(
        lambda request: httpx2.Response(
            200,
            content=body,
            headers={"Last-Modified": "Wed, 01 Jan 2025 00:00:00 GMT"},
        )
    )
    target = tmp_path / "sida_2026-T03@20250101.zip"
    path = client.download_file(
        "https://pgfn.test/2026_trimestre_03/Dados_abertos_Sistema_SIDA.zip",
        target,
        dataset_id="sida",
    )
    assert path == target
    assert target.read_bytes() == body
    manifest = json.loads(
        (tmp_path / "sida_2026-T03@20250101.zip.manifest.json").read_text()
    )
    assert manifest["source_id"] == "pgfn"
    assert manifest["dataset_id"] == "sida"
    assert manifest["producer"] == "pgfn-fetcher"
    assert manifest["sha256"] == hashlib.sha256(body).hexdigest()


def test_download_file_rejeita_pagina_de_erro(tmp_path: Path) -> None:
    """HTML com HTTP 200 no lugar do ZIP não vira arquivo nem manifesto."""
    client = _client_with(
        lambda request: httpx2.Response(
            200, content=b"<html>erro</html>", headers={"Content-Type": "text/html"}
        )
    )
    target = tmp_path / "x.zip"
    with pytest.raises(CorruptPayloadError):
        client.download_file("https://pgfn.test/x.zip", target, dataset_id="sida")
    assert not target.exists()
    assert not (tmp_path / "x.zip.manifest.json").exists()
