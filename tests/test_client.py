"""Tests for PgfnClient."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from quantilica.core.manifests import DownloadManifest

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


def test_download_file(tmp_path) -> None:
    client = PgfnClient()
    target = tmp_path / "test.zip"
    mock_manifest = MagicMock(spec=DownloadManifest)
    with patch.object(
        client.client, "download_with_manifest", return_value=mock_manifest
    ):
        res = client.download_file("https://pgfn/test.zip", target)
        assert res == mock_manifest
