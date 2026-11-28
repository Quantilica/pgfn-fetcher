"""HTTP client and discovery for PGFN open data."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from quantilica.core.http import HttpClient, resolve_verify_from_env
from quantilica.core.logging import get_logger
from quantilica.core.storage import ExpectedFormat, expected_format_for_path

from .constants import PGFN_BASE_URL

logger = get_logger(__name__)


def _default_http_client() -> HttpClient:
    """Cliente padrão do host (``QUANTILICA_HTTP_*``, SSL, CA), com plano B do core."""
    try:
        from quantilica.cli.sdk import default_client
    except ImportError:  # CLI autônoma, sem o host instalado
        return HttpClient(verify=resolve_verify_from_env(), emulate_browser=True)
    return default_client()


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
        self.client = client or _default_http_client()
        self.logger = logger or get_logger(__name__)

    def discover_trimesters(self) -> list[str]:
        """Discover available trimester directories from Apache autoindex.

        Levanta a exceção do cliente HTTP se a listagem da raiz falhar: lista
        vazia quer dizer que a raiz respondeu e não traz nenhum diretório de
        trimestre. Quem chama decide entre o catálogo de reserva e o erro.
        """
        resp = self.client.get(self.base_url)
        dirs = re.findall(r'href="(\d{4}_trimestre_\d{2}/?)"', resp.text)
        return sorted(set(d.strip("/") for d in dirs))

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
        dataset_id: str,
        source_id: str = "pgfn",
        producer: str = "pgfn-fetcher",
        force: bool = False,
        expected_format: ExpectedFormat | None = None,
    ) -> Path:
        """Baixa um arquivo da PGFN com manifesto lateral.

        O manifesto (``<dest>.manifest.json``) traz o SHA-256. O formato esperado
        sai da extensão de ``dest`` quando não é informado, e a assinatura do
        conteúdo é conferida antes de gravar (página de erro com HTTP 200 não
        substitui o arquivo).

        Returns:
            Path: O caminho do arquivo baixado (ou já em dia).
        """
        return self.client.download_with_manifest(
            url,
            dest,
            source_id=source_id,
            dataset_id=dataset_id,
            producer=producer,
            force=force,
            expected_format=expected_format or expected_format_for_path(dest),
        )
