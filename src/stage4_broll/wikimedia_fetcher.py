"""
src/stage4_broll/wikimedia_fetcher.py - Busca e download de imagens e documentos históricos no acervo de domínio público.
Utiliza a API oficial do Wikimedia Commons (MediaWiki Action API).
"""

from pathlib import Path
from typing import Optional
import urllib.parse
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WikimediaFetcher")


class WikimediaFetcher:
    def __init__(self, user_agent: str = "DocuVibeStudio/1.0 (contact@docuvibe.studio)"):
        self.headers = {"User-Agent": user_agent}
        self.endpoint = "https://commons.wikimedia.org/w/api.php"

    def fetch_image(self, search_query: str, output_path: Path) -> Optional[Path]:
        """
        Busca a imagem histórica mais relevante para a query e faz o download.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # 1. Busca arquivos relevantes
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {search_query}",
                "gsrnamespace": "6",  # Namespace de Arquivos
                "gsrlimit": "3",
                "prop": "imageinfo",
                "iiprop": "url|mime|size",
                "iiurlwidth": "1920"  # Pede versão redimensionada para até 1920px
            }
            res = requests.get(self.endpoint, params=params, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                pages = data.get("query", {}).get("pages", {})
                for _, page in pages.items():
                    imageinfo = page.get("imageinfo", [])
                    if imageinfo:
                        img_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
                        if img_url:
                            logger.info("Mídia histórica localizada no Wikimedia: %s", img_url)
                            self._download(img_url, output_path)
                            return output_path

            logger.info("Nenhuma imagem histórica encontrada para a busca: '%s'", search_query)
            return None
        except Exception as e:
            logger.warning("Erro ao consultar Wikimedia Commons (%s)", str(e))
            return None

    def _download(self, url: str, target: Path) -> None:
        with requests.get(url, headers=self.headers, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
