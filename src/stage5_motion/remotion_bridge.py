"""
src/stage5_motion/remotion_bridge.py - Ponte de orquestração entre Python e Remotion CLI.
Renderiza clipes individuais MP4 baseando-se nas propriedades de cena do project_manifest.json.
Aplica as diretrizes de concorrência calibrada para o hardware (Ryzen 5 5500 + NVENC).
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RemotionBridge")


class RemotionBridge:
    def __init__(
        self,
        remotion_dir: Path = Path("remotion_graphics"),
        concurrency: int = 4
    ):
        self.remotion_dir = remotion_dir
        self.concurrency = concurrency

    def render_template(
        self,
        composition_id: str,
        output_path: Path,
        props: Dict[str, Any],
        duration_in_frames: int = 150,
        fps: int = 30
    ) -> Path:
        """
        Dispara `npx remotion render` passando as props serializadas em JSON e duração customizada.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        props_json = json.dumps(props)

        # Monta caminho relativo do arquivo de entrada e saída
        entry_file = "src/index.tsx"
        rel_output = Path("..") / output_path

        cmd = [
            "npx", "remotion", "render",
            entry_file,
            composition_id,
            str(rel_output),
            f"--props={props_json}",
            f"--concurrency={self.concurrency}",
            f"--frames=0-{duration_in_frames - 1}"
        ]

        logger.info("Disparando Remotion CLI: Composição '%s' -> '%s' (%d frames)", composition_id, output_path, duration_in_frames)
        result = subprocess.run(cmd, cwd=str(self.remotion_dir), capture_output=True, text=True, shell=True)

        if result.returncode != 0:
            logger.error("Erro na compilação do Remotion: %s", result.stderr)
            raise RuntimeError(f"Remotion render falhou com código {result.returncode}: {result.stderr}")

        logger.info("Clipe Remotion renderizado com sucesso: %s", output_path)
        return output_path
