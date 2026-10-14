"""
src/stage4_broll/pexels_fetcher.py - Download automatizado de B-rolls reais em Full HD (1080p).
Consulta as APIs do Pexels e Pixabay com fallback inteligente para mídias de demonstração offline.
"""

import os
from pathlib import Path
from typing import Optional
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PexelsFetcher")


class BrollFetcher:
    def __init__(self, pexels_api_key: Optional[str] = None, pixabay_api_key: Optional[str] = None):
        self.pexels_api_key = pexels_api_key or os.getenv("PEXELS_API_KEY", "")
        self.pixabay_api_key = pixabay_api_key or os.getenv("PIXABAY_API_KEY", "")

    def fetch_video(self, query: str, output_path: Path, min_duration_sec: float = 4.0) -> Path:
        """
        Busca e faz o download de um vídeo horizontal (16:9) em 1080p correspondente à query.
        Caso nenhuma chave esteja configurada ou a API falhe, gera clipe placeholder de alta resolução.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.pexels_api_key:
            try:
                video_url = self._search_pexels(query, min_duration_sec)
                if video_url:
                    self._download_file(video_url, output_path)
                    logger.info("Vídeo Pexels baixado com sucesso para: %s", output_path)
                    return output_path
            except Exception as e:
                logger.warning("Erro ao buscar no Pexels (%s). Tentando Pixabay...", str(e))

        if self.pixabay_api_key:
            try:
                video_url = self._search_pixabay(query)
                if video_url:
                    self._download_file(video_url, output_path)
                    logger.info("Vídeo Pixabay baixado com sucesso para: %s", output_path)
                    return output_path
            except Exception as e:
                logger.warning("Erro ao buscar no Pixabay (%s).", str(e))

        logger.info("Chaves de API ausentes ou busca sem resultado. Criando fallback para a cena: '%s'", query)
        self._generate_placeholder_video(query, output_path, duration=min_duration_sec)
        return output_path

    def _search_pexels(self, query: str, min_duration: float) -> Optional[str]:
        headers = {"Authorization": self.pexels_api_key}
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=landscape&size=medium&per_page=5"
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            videos = data.get("videos", [])
            for v in videos:
                if v.get("duration", 0) >= min_duration:
                    files = v.get("video_files", [])
                    # Prioriza Full HD (1920x1080)
                    for f in files:
                        if f.get("width") == 1920 and f.get("height") == 1080:
                            return f.get("link")
                    if files:
                        return files[0].get("link")
        return None

    def _search_pixabay(self, query: str) -> Optional[str]:
        url = f"https://pixabay.com/api/videos/?key={self.pixabay_api_key}&q={query}&video_type=film"
        res = requests.get(url, timeout=8)
        if res.status_code == 200:
            data = res.json()
            hits = data.get("hits", [])
            if hits:
                videos = hits[0].get("videos", {})
                large = videos.get("large", {}).get("url") or videos.get("medium", {}).get("url")
                return large
        return None

    def _download_file(self, url: str, target_path: Path) -> None:
        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

    def _generate_placeholder_video(self, query: str, output_path: Path, duration: float = 5.0) -> None:
        """Gera um vídeo suave de cor sólida com FFmpeg acelerado quando offline."""
        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=#161920:s=1920x1080:d={duration}:r=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
