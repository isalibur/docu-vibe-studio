"""
src/stage4_broll/parallax_segmenter.py - Recorte de primeiro plano para animações 2.5D.
Utiliza rembg (RMBG-1.4 / RMBG-2.0 via ONNX) para isolar o sujeito do fundo.
Gera a camada transparente (foreground) e a camada de fundo desfocada (background).
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageFilter
import logging
from src.core.vram_guard import flush_vram

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ParallaxSegmenter")


class ParallaxSegmenter:
    def __init__(self, model_name: str = "briaai/RMBG-1.4"):
        self.model_name = model_name

    def process_image_for_parallax(
        self,
        input_image_path: Path,
        output_fg_path: Path,
        output_bg_path: Path,
        bg_blur_radius: float = 6.0
    ) -> Tuple[Path, Path]:
        """
        Processa a imagem estática:
        1. Recorta o primeiro plano transparente usando rembg -> salva em output_fg_path.
        2. Gera uma versão de fundo suavemente desfocada -> salva em output_bg_path.
        """
        if not input_image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada para segmentação: {input_image_path}")

        output_fg_path.parent.mkdir(parents=True, exist_ok=True)
        output_bg_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from rembg import remove, new_session
            
            logger.info("Executando recorte de primeiro plano com rembg: %s", input_image_path)
            input_image = Image.open(input_image_path).convert("RGBA")

            # 1. Recorte do sujeito em primeiro plano
            session = new_session("u2net")
            fg_image = remove(input_image, session=session)
            fg_image.save(output_fg_path, format="PNG")

            # 2. Processamento do fundo (fundo recebe desfoque para dar profundidade de campo)
            bg_image = input_image.convert("RGB").filter(ImageFilter.GaussianBlur(radius=bg_blur_radius))
            bg_image.save(output_bg_path, format="JPEG", quality=92)

            logger.info("Parallax pre-processado: FG -> %s | BG -> %s", output_fg_path, output_bg_path)
        finally:
            flush_vram()

        return output_fg_path, output_bg_path
