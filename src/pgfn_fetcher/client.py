"""HTTP client and discovery for PGFN open data."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from quantilica.core.http import HttpClient
from quantilica.core.logging import get_logger
from quantilica.core.manifests import DownloadManifest

from .constants import PGFN_BASE_URL

logger = get_logger(__name__)


def parse_zip_links(html: str) -> list[str]:
    """Extrai os nomes de arquivo ``.zip`` dos links de uma página autoindex."""
    names = re.findall(r'href="([^"/?#]+\.zip)"', html, flags=re.IGNORECASE)
    return sorted(set(names))


class PgfnClient:
    """Client for downloading PGFN open data ZIP files."""

    def __init__(
        self,
        *,
        base_url: str = PGFN_BASE_URL,
        client: HttpClient | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or HttpClient()
        self.logger = logger or get_logger(__name__)

    def discover_trimesters(self) -> list[str]:
        """Discover available trimester directories from Apache autoindex."""
        try:
            resp = self.client.get(self.base_url)
            html = resp.text
            dirs = re.findall(r'href="(\d{4}_trimestre_\d{2}/?)"', html)
            return sorted(set(d.strip("/") for d in dirs))
        except Exception as exc:
            self.logger.warning("Erro ao listar autoindex PGFN: %s", exc)
            return []

    def list_trimester_files(self, trimester: str) -> list[str]:
        """Lista os ``.zip`` realmente publicados em um diretório de trimestre.

        Levanta a exceção do cliente HTTP se a listagem falhar: quem chama decide
        entre o fallback e o erro contado.
        """
        resp = self.client.get(f"{self.base_url}/{trimester}/")
        return parse_zip_links(resp.text)

    def download_file(
        self,
        url: str,
        dest: Path,
        *,
        manifest_path: Path | None = None,
    ) -> DownloadManifest:
        """Download PGFN file with SHA-256 manifest sidecar."""
        return self.client.download_with_manifest(
            url,
            dest,
            manifest_path=manifest_path,
        )
