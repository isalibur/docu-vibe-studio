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

        # 2. Constrói entradas de vídeo e filtros de normalização
        cmd = ["ffmpeg", "-y"]
        filter_parts = []

        v_tags = []
        for idx, clip in enumerate(clip_paths):
            cmd.extend(["-i", str(clip.resolve())])
            filter_parts.append(
                f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
                f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{idx}]"
            )
            v_tags.append(f"[v{idx}]")

        # Concatena todos os clipes de vídeo normalizados
        concat_input = "".join(v_tags)
        filter_parts.append(f"{concat_input}concat=n={len(clip_paths)}:v=1:a=0[vconcat]")

        video_map = "[vconcat]"
        captions_ass = manifest.captions_ass
        if captions_ass and Path(captions_ass).exists():
            ass_escaped = str(Path(captions_ass).resolve()).replace("\\", "/").replace(":", "\\:")
            filter_parts.append(f"[vconcat]subtitles='{ass_escaped}'[vout]")
            video_map = "[vout]"

        # 3. Entradas de áudio e masterização sonora
        audio_master = manifest.audio_master
        bgm_track = manifest.bgm_track or "assets/bgm/dark_investigative_ambient.mp3"
        video_encoder = self.encoder if use_nvenc else "libx264"
        audio_map = None

        if audio_master and Path(audio_master).exists():
            audio_idx = len(clip_paths)
            cmd.extend(["-i", str(audio_master)])
            if bgm_track and Path(bgm_track).exists():
                bgm_idx = audio_idx + 1
                cmd.extend(["-i", str(bgm_track)])
                filter_parts.append(
                    f"[{audio_idx}:a]loudnorm=I=-14:TP=-1.5:LRA=7,asplit=2[voice_for_sc][voice_for_mix];"
                    f"[{bgm_idx}:a]volume=0.07[bgm];"
                    f"[bgm][voice_for_sc]sidechaincompress=threshold=0.04:ratio=8:attack=50:release=400[ducked_bgm];"
                    f"[voice_for_mix][ducked_bgm]amix=inputs=2:duration=first:normalize=0[aout]"
                )
                audio_map = "[aout]"
            else:
                filter_parts.append(f"[{audio_idx}:a]loudnorm=I=-14:TP=-1.5:LRA=7[aout]")
                audio_map = "[aout]"

        if filter_parts:
            cmd.extend(["-filter_complex", ";".join(filter_parts)])

        cmd.extend(["-map", video_map])
        if audio_map:
            cmd.extend(["-map", audio_map])

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

        logger.info("Executando montagem mestre via FFmpeg: %s", " ".join(cmd))

        subprocess.run(cmd, check=True)
        logger.info("Documentário final masterizado com sucesso: %s", output_file)

        return output_file
