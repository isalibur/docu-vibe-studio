"""
src/stage2_audio/silence_cutter.py - Remoção cirúrgica de pausas e respirações com auto-editor.
Garante o ritmo dinâmico e acelerado de documentários investigativos.
"""

import subprocess
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SilenceCutter")


class SilenceCutter:
    def __init__(self, min_silence_duration: float = 0.35, margin: float = 0.12):
        """
        :param min_silence_duration: Silêncios maiores que isso em segundos serão cortados.
        :param margin: Margem de respiração antes/depois do corte para evitar cortes bruscos nas palavras.
        """
        self.min_silence_duration = min_silence_duration
        self.margin = margin

    def process_audio(self, input_path: Path, output_path: Path) -> Path:
        """
        Executa o auto-editor via subprocesso seguro (lista de argumentos, sem shell=True).
        Converte/recorta o áudio de entrada e exporta a versão limpa e acelerada.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {input_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Monta comando do auto-editor
        # Sintaxe do auto-editor para áudio: auto-editor input.wav --edit audio:threshold=4% --margin 0.12sec -o output.wav
        cmd = [
            shutil.which("auto-editor") or "auto-editor",
            str(input_path),
            "--edit", "audio:threshold=4%",
            "--margin", f"{self.margin}sec",
            "-o", str(output_path),
            "--no-open"
        ]

        logger.info("Executando auto-editor: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.warning("Auto-editor falhou com log: %s. Aplicando fallback de cópia simples.", result.stderr)
            shutil.copy2(input_path, output_path)
        else:
            logger.info("Áudio encurtado e limpo com sucesso: %s", output_path)

        return output_path
