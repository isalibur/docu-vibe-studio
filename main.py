"""
main.py - Orquestrador Central CLI do Docu-Vibe-Studio.
Executa a esteira ponta a ponta: do Tema Bruto ao Documentário Final Masterizado com NVENC.
Suporta retomada inteligente por manifesto e execução de estágios individuais.
"""

import argparse
import sys
import shutil
import subprocess
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
from src.stage4_broll.wikimedia_fetcher import WikimediaFetcher
from src.stage4_broll.parallax_segmenter import ParallaxSegmenter
from src.stage5_motion.remotion_bridge import RemotionBridge
from src.stage6_assembler.ffmpeg_composer import FFmpegComposer
from src.stage6_assembler.otio_exporter import OTIOExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DocuVibeOrchestrator")


def run_pipeline(
    topic: str,
    project_id: Optional[str] = None,
    stage: Optional[str] = None,
    voice: Optional[str] = None,
    tone: Optional[str] = None,
    local_assets_folder: Optional[str] = None
):
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
    # ESTÁGIO 2: Narração e Ritmo Cinematográfico
    # ---------------------------------------------------------
    if not stage or stage in ["2", "audio"]:
        logger.info("=== ESTÁGIO 2: SÍNTESE DE VOZ E RITMO CINEMATOGRÁFICO ===")
        tts = TTSEngine(voice=voice or "pt-BR-AntonioNeural", rate="+6%")
        audio_dir = workspace_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        cutter = SilenceCutter(target_sample_rate=48000)

        # 1. Sintetiza áudio de cada cena individualmente para sincronia temporal exata
        scene_wav_paths = []
        current_time = 0.0

        for scene in manifest.scenes:
            sc_raw = audio_dir / f"scene_{scene.scene_id:02d}_raw.mp3"
            sc_wav = audio_dir / f"scene_{scene.scene_id:02d}.wav"
            tts.generate_speech(scene.narration_text, sc_raw)
            cutter.process_audio(sc_raw, sc_wav)
            dur = tts.get_duration(sc_wav)
            
            # Margem suave de 0.3s para respiração cinematográfica da cena
            scene_duration = round(dur + 0.3, 2)
            scene.start_time = round(current_time, 2)
            scene.end_time = round(current_time + scene_duration, 2)
            current_time = scene.end_time
            scene_wav_paths.append(sc_wav)

        # 2. Concatena os áudios das cenas no áudio mestre contínuo a 48kHz
        trimmed_master = audio_dir / "narration_trimmed.wav"
        concat_inputs = []
        filter_inputs = []
        for i, sw in enumerate(scene_wav_paths):
            concat_inputs.extend(["-i", str(sw.resolve())])
            filter_inputs.append(f"[{i}:a]")
        
        filter_str = f"{''.join(filter_inputs)}concat=n={len(scene_wav_paths)}:v=0:a=1[aout]"
        cmd = ["ffmpeg", "-y"] + concat_inputs + ["-filter_complex", filter_str, "-map", "[aout]", "-c:a", "pcm_s16le", str(trimmed_master)]
        subprocess.run(cmd, check=True)

        manifest.audio_master = str(trimmed_master)
        manifest.stage_status.stage2_audio = StageStatusEnum.COMPLETED
        manifest.save(manifest_path)
        flush_vram()

    # ---------------------------------------------------------
    # ESTÁGIO 3: Legendas Dinâmicas com Guia Fonético
    # ---------------------------------------------------------
    if not stage or stage in ["3", "captions"]:
        logger.info("=== ESTÁGIO 3: SINCRONIA FONÉTICA E LEGENDAS .ASS ===")
        aligner = AudioAligner(model_size="base", device="cpu", compute_type="int8")
        full_narration = " ".join([s.narration_text for s in manifest.scenes])
        words = aligner.align_audio(Path(manifest.audio_master), language="pt", reference_text=full_narration)

        captions_path = workspace_dir / "captions" / "dynamic_words.ass"
        gen = ASSGenerator(words_per_block=4)
        gen.generate_ass(words, captions_path)

        manifest.captions_ass = str(captions_path)
        manifest.stage_status.stage3_captions = StageStatusEnum.COMPLETED
        manifest.save(manifest_path)
        flush_vram()

    # ---------------------------------------------------------
    # ESTÁGIO 4 & 5: Renderização de Cenas (Mídia Híbrida e Remotion)
    # ---------------------------------------------------------
    if not stage or stage in ["4", "5", "media", "motion"]:
        logger.info("=== ESTÁGIO 4 & 5: GERAÇÃO DE MÍDIA E MOTION GRAPHICS ===")
        broll_fetcher = BrollFetcher()
        wiki_fetcher = WikimediaFetcher()
        segmenter = ParallaxSegmenter()
        bridge = RemotionBridge(concurrency=4)
        
        renders_dir = workspace_dir / "renders"
        renders_dir.mkdir(parents=True, exist_ok=True)
        media_dir = workspace_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        remotion_public_assets = Path("remotion_graphics/public/assets")
        remotion_public_assets.mkdir(parents=True, exist_ok=True)

        for scene in manifest.scenes:
            out_clip = renders_dir / f"scene_{scene.scene_id:02d}.mp4"
            duration_frames = int(max(4.0, (scene.end_time - scene.start_time)) * manifest.fps)
            query = scene.visual_config.search_query or topic

            if scene.visual_type == VisualTypeEnum.REMOTION_GRAPHIC:
                template = scene.visual_config.template or "NewspaperHighlight"
                bridge.render_template(
                    composition_id=template,
                    output_path=out_clip,
                    props=scene.visual_config.props or {},
                    duration_in_frames=duration_frames
                )
            elif scene.visual_type == VisualTypeEnum.PARALLAX_25D:
                # 1. Verifica pasta local indicada pelo usuário
                img_path = None
                if local_assets_folder and Path(local_assets_folder).exists():
                    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                        matches = list(Path(local_assets_folder).glob(ext))
                        if matches:
                            img_path = matches[0]
                            break

                # 2. Se não houver arquivo local, consulta o acervo do Wikimedia Commons
                if not img_path:
                    raw_wiki = media_dir / f"scene_{scene.scene_id:02d}_wiki.jpg"
                    img_path = wiki_fetcher.fetch_image(query, raw_wiki)

                if img_path and Path(img_path).exists():
                    fg_temp = media_dir / f"scene_{scene.scene_id:02d}_fg.png"
                    bg_temp = media_dir / f"scene_{scene.scene_id:02d}_bg.jpg"
                    segmenter.process_image_for_parallax(img_path, fg_temp, bg_temp)

                    # Copia para os assets públicos do Remotion
                    public_fg = remotion_public_assets / f"{project_slug}_s{scene.scene_id:02d}_fg.png"
                    public_bg = remotion_public_assets / f"{project_slug}_s{scene.scene_id:02d}_bg.jpg"
                    shutil.copyfile(fg_temp, public_fg)
                    shutil.copyfile(bg_temp, public_bg)

                    bridge.render_template(
                        composition_id="DocumentaryParallax",
                        output_path=out_clip,
                        props={
                            "backgroundSrc": f"/assets/{public_bg.name}",
                            "foregroundCutoutSrc": f"/assets/{public_fg.name}",
                            "cameraMotion": scene.visual_config.camera_motion or "push_in"
                        },
                        duration_in_frames=duration_frames
                    )
                else:
                    broll_fetcher.fetch_video(query, out_clip, min_duration_sec=scene.duration_sec or 5.0)

            elif scene.visual_type == VisualTypeEnum.HISTORIC_MEDIA:
                raw_wiki = media_dir / f"scene_{scene.scene_id:02d}_hist.jpg"
                img_path = wiki_fetcher.fetch_image(query, raw_wiki)
                if img_path and Path(img_path).exists():
                    public_bg = remotion_public_assets / f"{project_slug}_s{scene.scene_id:02d}_hist.jpg"
                    shutil.copyfile(img_path, public_bg)
                    bridge.render_template(
                        composition_id="DocumentaryParallax",
                        output_path=out_clip,
                        props={
                            "backgroundSrc": f"/assets/{public_bg.name}",
                            "cameraMotion": scene.visual_config.camera_motion or "push_in"
                        },
                        duration_in_frames=duration_frames
                    )
                else:
                    broll_fetcher.fetch_video(query, out_clip, min_duration_sec=scene.duration_sec or 5.0)

            else:  # STOCK_BROLL
                # Se há chaves para Pexels/Pixabay, tenta vídeo
                if broll_fetcher.pexels_api_key or broll_fetcher.pixabay_api_key:
                    broll_fetcher.fetch_video(query, out_clip, min_duration_sec=scene.duration_sec or 5.0)
                else:
                    # Sem chaves externas: busca foto histórica e anima com Ken Burns 2.5D
                    raw_wiki = media_dir / f"scene_{scene.scene_id:02d}_broll_wiki.jpg"
                    img_path = wiki_fetcher.fetch_image(query, raw_wiki)
                    if img_path and Path(img_path).exists():
                        public_bg = remotion_public_assets / f"{project_slug}_s{scene.scene_id:02d}_broll.jpg"
                        shutil.copyfile(img_path, public_bg)
                        bridge.render_template(
                            composition_id="DocumentaryParallax",
                            output_path=out_clip,
                            props={
                                "backgroundSrc": f"/assets/{public_bg.name}",
                                "cameraMotion": "drift_left"
                            },
                            duration_in_frames=duration_frames
                        )
                    else:
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
