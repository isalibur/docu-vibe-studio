"""
src/stage4_broll/wikimedia_fetcher.py - Busca curada de imagens e obras de arte históricas em domínio público.
Filtra estritamente livros escaneados, arquivos DJVU, placas inadequadas e gráficos modernos.
Exige formato landscape (16:9 / horizontal) em alta resolução e impede repetição de imagens.
"""

from pathlib import Path
from typing import Optional, Set, List
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WikimediaFetcher")

# Termos proibidos para evitar páginas escaneadas, capas de livros, diagramas e ícones
EXCLUDED_KEYWORDS = [
    "djvu", "book", "page", "scan", "cover", "sign", "lupanar",
    "map", "diagram", "satellite", "weather", "coin", "stamp",
    "icon", "logo", "flag", "chart", "graph", "text", "edition",
    "title_page", "frontispiece", "preface", "manuscript"
]


class WikimediaFetcher:
    def __init__(self, user_agent: str = "DocuVibeStudio/2.0 (contact@docuvibe.studio)"):
        self.headers = {"User-Agent": user_agent}
        self.endpoint = "https://commons.wikimedia.org/w/api.php"
        self.seen_urls: Set[str] = set()

    def reset_cache(self):
        """Limpa o rastreador de duplicatas para um novo projeto."""
        self.seen_urls.clear()

    def fetch_image(self, search_query: str, output_path: Path) -> Optional[Path]:
        """
        Busca a imagem histórica mais relevante e estética em formato landscape (horizontal).
        Garante que a imagem nunca seja repetida no mesmo documentário.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Lista de tentativas: query original, variações e simplificações
            queries_to_try = [search_query]
            words = search_query.split()
            if len(words) > 3:
                queries_to_try.append(f"{words[0]} {words[1]} {words[2]}")
                queries_to_try.append(f"{words[0]} {words[1]}")

            for q in queries_to_try:
                params = {
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": q,
                    "gsrnamespace": "6",  # Namespace de Arquivos
                    "gsrlimit": "15",
                    "prop": "imageinfo",
                    "iiprop": "url|mime|size|dimensions",
                    "iiurlwidth": "1920"
                }
                res = requests.get(self.endpoint, params=params, headers=self.headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    pages = data.get("query", {}).get("pages", {})
                    
                    # Coleta candidatos válidos
                    candidates = []
                    for _, page in pages.items():
                        title = page.get("title", "").lower()
                        imageinfo = page.get("imageinfo", [])
                        if not imageinfo:
                            continue
                        
                        info = imageinfo[0]
                        mime = info.get("mime", "")
                        width = info.get("width", 0)
                        height = info.get("height", 0)
                        img_url = info.get("thumburl") or info.get("url")

                        if not img_url or img_url in self.seen_urls:
                            continue

                        # Validações estritas de qualidade e estética
                        if not mime.startswith("image/") or "svg" in mime:
                            continue

                        # 1. Filtro de lixo de arquivo (livros escaneados, djvu, etc.)
                        url_lower = img_url.lower()
                        if any(kw in title or kw in url_lower for kw in EXCLUDED_KEYWORDS):
                            continue

                        # 2. Exigência de formato horizontal (landscape) em boa resolução
                        if width > 0 and height > 0:
                            aspect = width / height
                            # Aceita apenas imagens horizontais (aspect ratio >= 1.1) e largura >= 800
                            if aspect < 1.1 or width < 800:
                                continue

                        candidates.append((title, width, height, img_url))

                    # Se encontrou candidatos válidos, seleciona o melhor
                    if candidates:
                        # Ordena priorizando imagens de maior resolução
                        candidates.sort(key=lambda c: c[1] * c[2], reverse=True)
                        best_title, best_w, best_h, best_url = candidates[0]
                        logger.info("Obra histórica selecionada (%s, %dx%d): %s", best_title, best_w, best_h, best_url)
                        self.seen_urls.add(best_url)
                        self._download(best_url, output_path)
                        return output_path

            logger.warning("Nenhuma imagem histórica landscape aceitável para: '%s'", search_query)
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
