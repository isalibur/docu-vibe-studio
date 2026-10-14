"""
src/stage2_audio/silence_cutter.py - Processador de áudio e limpeza segura de silêncios.
Normaliza e limpa tempos mortos sem decepar fonemas ou comprometer a inteligibilidade vocal.
"""

import subprocess
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SilenceCutter")


class SilenceCutter:
    def __init__(self, target_sample_rate: int = 48000):
        self.target_sample_rate = target_sample_rate

    def process_audio(self, input_path: Path, output_path: Path) -> Path:
        """
        Converte áudio para PCM WAV 48kHz de alta fidelidade e remove silêncios
        iniciais e finais mortos sem distorcer as palavras ou fatiar fonemas.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {input_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Utiliza FFmpeg com silenceremove seguro apenas no início e fim
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-af", "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse",
            "-ar", str(self.target_sample_rate),
            "-c:a", "pcm_s16le",
            str(output_path)
        ]

        logger.info("Normalizando e limpando áudio mestre via FFmpeg: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

        if result.returncode != 0:
            logger.warning("Filtro silenceremove falhou (%s). Copiando arquivo original.", result.stderr)
            shutil.copy2(input_path, output_path)
        else:
            logger.info("Áudio mestre 48kHz limpo com sucesso: %s", output_path)

        return output_path
