"""
src/stage6_assembler/ffmpeg_composer.py - Montagem final, mixagem de áudio e renderização NVENC.
Aplica sidechain ducking (música baixa durante a narração), queima legendas .ass e usa a GPU RTX 3060.
"""

import subprocess
from pathlib import Path
from typing import List, Optional
import logging
from src.core.manifest import ProjectManifest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FFmpegComposer")


class FFmpegComposer:
    def __init__(
        self,
        encoder: str = "h264_nvenc",
        preset: str = "p4",
        cq: int = 19
    ):
        self.encoder = encoder
        self.preset = preset
        self.cq = cq

    def assemble_documentary(
        self,
        manifest: ProjectManifest,
        output_file: Path,
        use_nvenc: bool = True
    ) -> Path:
        """
        Concatena os clipes de vídeo das cenas, mixa a locução com a trilha sonora (auto-ducking)
        e queima as legendas .ass dinâmicas com aceleração por hardware da RTX 3060.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 1. Coleta e normaliza os clipes renderizados das cenas
        clip_paths = []
        for scene in manifest.scenes:
            if scene.rendered_clip_path and Path(scene.rendered_clip_path).exists():
                clip_paths.append(Path(scene.rendered_clip_path))

        if not clip_paths:
            raise FileNotFoundError("Nenhum clipe de vídeo renderizado encontrado no manifesto para montagem.")

        # 2. Cria arquivo de concatenação temporário
        concat_list_path = output_file.parent / "concat_list.txt"
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for clip in clip_paths:
                # FFmpeg concat requer barras normais
                normalized = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{normalized}'\n")

        # 3. Monta comando FFmpeg com pipeline de áudio e vídeo
        # Áudio: Narração principal + BGM com sidechaincompress (ducking)
        audio_master = manifest.audio_master
        bgm_track = manifest.bgm_track or "assets/bgm/dark_investigative_ambient.mp3"
        captions_ass = manifest.captions_ass

        video_encoder = self.encoder if use_nvenc else "libx264"

        # Monta filtro de vídeo: Concatenação + queima de legenda .ass se existir
        video_filters = []
        if captions_ass and Path(captions_ass).exists():
            ass_escaped = str(Path(captions_ass).resolve()).replace("\\", "/").replace(":", "\\:")
            video_filters.append(f"subtitles='{ass_escaped}'")

        vf_str = f"-vf \"{','.join(video_filters)}\"" if video_filters else ""

        # Comando seguro de montagem
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list_path),
        ]

        # Se houver áudio mestre narrado
        if audio_master and Path(audio_master).exists():
            cmd.extend(["-i", str(audio_master)])
            # Se houver BGM, faz a mixagem com ducking
            if bgm_track and Path(bgm_track).exists():
                cmd.extend(["-i", str(bgm_track)])
                # Filtro de sidechain ducking: o canal 1 (narração) comprime o volume do canal 2 (música)
                filter_complex = (
                    "[2:a]volume=0.25[bgm];"
                    "[bgm][1:a]sidechaincompress=threshold=0.08:ratio=6:attack=200:release=600[ducked_bgm];"
                    "[1:a][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                )
                cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]"])
            else:
                cmd.extend(["-map", "0:v", "-map", "1:a"])
        else:
            cmd.extend(["-map", "0:v"])

        # Parâmetros de codificação de vídeo acelerada por hardware
        if use_nvenc:
            cmd.extend([
                "-c:v", video_encoder,
                "-preset", self.preset,
                "-rc", "vbr",
                "-cq", str(self.cq),
                "-pix_fmt", "yuv420p"
            ])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "19",
                "-pix_fmt", "yuv420p"
            ])

        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest", str(output_file)])

        cmd_str = " ".join(cmd)
        logger.info("Executando montagem mestre via FFmpeg: %s", cmd_str)

        try:
            subprocess.run(cmd_str, shell=True, check=True)
            logger.info("Documentário final masterizado com sucesso: %s", output_file)
        finally:
            if concat_list_path.exists():
                concat_list_path.unlink()

        return output_file
