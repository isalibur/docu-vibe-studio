"""
main.py - Orquestrador Central CLI do Docu-Vibe-Studio.
Executa a esteira ponta a ponta: do Tema Bruto ao Documentário Final Masterizado com NVENC.
Suporta retomada inteligente por manifesto e execução de estágios individuais.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import logging

from src.core.manifest import ProjectManifest, StageStatusEnum, VisualTypeEnum
from src.core.vram_guard import flush_vram
from src.stage1_director.script_director import ScriptDirector
from src.stage2_audio.tts_engine import TTSEngine
from src.stage2_audio.silence_cutter import SilenceCutter
from src.stage3_captions.aligner import AudioAligner
from src.stage3_captions.ass_generator import ASSGenerator
from src.stage4_broll.pexels_fetcher import BrollFetcher
from src.stage4_broll.parallax_segmenter import ParallaxSegmenter
from src.stage5_motion.remotion_bridge import RemotionBridge
from src.stage6_assembler.ffmpeg_composer import FFmpegComposer
from src.stage6_assembler.otio_exporter import OTIOExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DocuVibeOrchestrator")


def run_pipeline(topic: str, project_id: Optional[str] = None, stage: Optional[str] = None):
    project_slug = project_id or f"doc_{abs(hash(topic)) % 100000}"
    workspace_dir = Path("workspace") / project_slug
    manifest_path = workspace_dir / "project_manifest.json"

    # Carrega ou inicializa manifesto
    if manifest_path.exists():
        logger.info("Retomando projeto existente: %s", manifest_path)
        manifest = ProjectManifest.load(manifest_path)
    else:
        logger.info("Iniciando novo documentário: '%s' (Slug: %s)", topic, project_slug)
        manifest = ProjectManifest(project_id=project_slug, title=topic)

    # ---------------------------------------------------------
    # ESTÁGIO 1: Roteiro e Direção
    # ---------------------------------------------------------
    if not stage or stage in ["1", "director"]:
        logger.info("=== ESTÁGIO 1: ROTEIRO E DIREÇÃO VISUAL ===")
        director = ScriptDirector()
        manifest = director.generate_script(topic, project_slug)
        manifest.save(manifest_path)
        logger.info("Roteiro salvo com %d cenas no manifesto.", len(manifest.scenes))

    # ---------------------------------------------------------
    # ESTÁGIO 2: Narração e Ritmo
    # ---------------------------------------------------------
    if not stage or stage in ["2", "audio"]:
        logger.info("=== ESTÁGIO 2: SÍNTESE DE VOZ E CORTE DE SILÊNCIO ===")
        tts = TTSEngine()
        audio_dir = workspace_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Concatena a narração de todas as cenas para o áudio mestre
        full_narration = " ".join([s.narration_text for s in manifest.scenes])
        raw_master = audio_dir / "narration_raw.mp3"
        trimmed_master = audio_dir / "narration_trimmed.wav"

        tts.generate_speech(full_narration, raw_master)

        cutter = SilenceCutter()
        cutter.process_audio(raw_master, trimmed_master)

        manifest.audio_master = str(trimmed_master)
        manifest.stage_status.stage2_audio = StageStatusEnum.COMPLETED
        manifest.save(manifest_path)
        flush_vram()

    # ---------------------------------------------------------
    # ESTÁGIO 3: Legendas Dinâmicas
    # ---------------------------------------------------------
    if not stage or stage in ["3", "captions"]:
        logger.info("=== ESTÁGIO 3: SINCRONIA FONÉTICA E LEGENDAS .ASS ===")
        aligner = AudioAligner(model_size="tiny", device="cpu")
        words = aligner.align_audio(Path(manifest.audio_master))

        captions_path = workspace_dir / "captions" / "dynamic_words.ass"
        gen = ASSGenerator(words_per_block=4)
        gen.generate_ass(words, captions_path)

        manifest.captions_ass = str(captions_path)
        manifest.stage_status.stage3_captions = StageStatusEnum.COMPLETED
        manifest.save(manifest_path)
        flush_vram()

    # ---------------------------------------------------------
    # ESTÁGIO 4 & 5: Renderização de Cenas (B-Roll e Remotion)
    # ---------------------------------------------------------
    if not stage or stage in ["4", "5", "media", "motion"]:
        logger.info("=== ESTÁGIO 4 & 5: GERAÇÃO DE MÍDIA E MOTION GRAPHICS ===")
        broll_fetcher = BrollFetcher()
        bridge = RemotionBridge(concurrency=4)
        renders_dir = workspace_dir / "renders"
        renders_dir.mkdir(parents=True, exist_ok=True)

        for scene in manifest.scenes:
            out_clip = renders_dir / f"scene_{scene.scene_id:02d}.mp4"
            duration_frames = int(max(4.0, scene.duration_sec or 5.0) * manifest.fps)

            if scene.visual_type == VisualTypeEnum.REMOTION_GRAPHIC:
                template = scene.visual_config.template or "DataChartCard"
                bridge.render_template(
                    composition_id=template,
                    output_path=out_clip,
                    props=scene.visual_config.props or {},
                    duration_in_frames=duration_frames
                )
            else:
                query = scene.visual_config.search_query or "financial market traders"
                broll_fetcher.fetch_video(query, out_clip, min_duration_sec=scene.duration_sec or 5.0)

            scene.rendered_clip_path = str(out_clip)

        manifest.stage_status.stage4_broll = StageStatusEnum.COMPLETED
        manifest.stage_status.stage5_motion = StageStatusEnum.COMPLETED
        manifest.save(manifest_path)

    # ---------------------------------------------------------
    # ESTÁGIO 6: Montagem Final NVENC e Exportação
    # ---------------------------------------------------------
    if not stage or stage in ["6", "assembler"]:
        logger.info("=== ESTÁGIO 6: MASTERIZAÇÃO FINAL COM FFmpeg NVENC ===")
        composer = FFmpegComposer()
        final_mp4 = workspace_dir / "output" / f"{manifest.project_id}_MASTER.mp4"
        composer.assemble_documentary(manifest, final_mp4, use_nvenc=True)

        otio = OTIOExporter()
        otio_path = workspace_dir / "output" / f"{manifest.project_id}_timeline.otio"
        otio.export_timeline(manifest, otio_path)

        manifest.final_video_path = str(final_mp4)
        manifest.otio_project_path = str(otio_path)
        manifest.stage_status.stage6_assembler = StageStatusEnum.COMPLETED
        manifest.save(manifest_path)

        logger.info("\n🎉 DOCUMENTÁRIO FINAL GERADO COM SUCESSO!\n👉 Vídeo Final: %s\n👉 Timeline Kdenlive: %s", final_mp4, otio_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docu-Vibe-Studio: Orquestrador de Documentários Inteligentes")
    parser.add_argument("--topic", type=str, default="O Colapso Financeiro de 2008", help="Tema do documentário")
    parser.add_argument("--project-id", type=str, default=None, help="Slug único do projeto")
    parser.add_argument("--stage", type=str, default=None, help="Executa apenas um estágio específico (1 a 6)")
    args = parser.parse_args()

    run_pipeline(topic=args.topic, project_id=args.project_id, stage=args.stage)
