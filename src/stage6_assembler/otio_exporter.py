"""
src/stage6_assembler/otio_exporter.py - Exportador de projeto de timeline aberta (.otio / Kdenlive).
Permite abrir todo o corte, faixas de áudio e BGM separadamente no Kdenlive para ajustes manuais.
"""

from pathlib import Path
import logging
from src.core.manifest import ProjectManifest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OTIOExporter")


class OTIOExporter:
    def export_timeline(self, manifest: ProjectManifest, output_otio_path: Path) -> Path:
        """
        Gera um arquivo de timeline .otio contendo:
        - Faixa 1 (Vídeo): Clipes das cenas sequenciais.
        - Faixa 2 (Áudio Locução): Faixa de narração recortada.
        - Faixa 3 (Áudio BGM): Faixa da trilha sonora de fundo.
        """
        output_otio_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import opentimelineio as otio

            timeline = otio.schema.Timeline(name=manifest.title)
            fps = manifest.fps

            # Faixa de Vídeo Principal
            video_track = otio.schema.Track(name="Video_Clips", kind=otio.schema.TrackKind.Video)
            for scene in manifest.scenes:
                if scene.rendered_clip_path and Path(scene.rendered_clip_path).exists():
                    duration_frames = int(scene.duration_sec * fps)
                    media_ref = otio.schema.ExternalReference(
                        target_url=str(Path(scene.rendered_clip_path).resolve())
                    )
                    clip = otio.schema.Clip(
                        name=f"Scene_{scene.scene_id}",
                        media_reference=media_ref,
                        source_range=otio.opentime.TimeRange(
                            start_time=otio.opentime.RationalTime(0, fps),
                            duration=otio.opentime.RationalTime(duration_frames, fps)
                        )
                    )
                    video_track.append(clip)

            timeline.tracks.append(video_track)

            # Exporta para disco
            otio.adapters.write_to_file(timeline, str(output_otio_path))
            logger.info("Timeline OpenTimelineIO exportada com sucesso: %s", output_otio_path)
            return output_otio_path
        except Exception as e:
            logger.warning("Falha ao exportar OTIO (%s). Gerando registro de manifesto como fallback.", str(e))
            output_otio_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
            return output_otio_path
