"""
src/core/manifest.py - Modelos Pydantic v2 do Contrato Central do Projeto.
Single Source of Truth para todas as 6 etapas do pipeline.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StageStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class VisualTypeEnum(str, Enum):
    REMOTION_GRAPHIC = "remotion_graphic"  # Gráficos de dados, mapas, manchetes, timeline
    STOCK_BROLL = "stock_broll"            # Vídeos reais do Pexels / Pixabay
    HISTORIC_MEDIA = "historic_media"      # Mídia histórica do Wikimedia Commons
    PARALLAX_25D = "parallax_25d"          # Imagem estática IA/foto + recorte RMBG + Parallax Remotion


class SFXEvent(BaseModel):
    name: str = Field(..., description="Nome do arquivo em assets/sfx/ (ex: whoosh_deep.wav)")
    offset_sec: float = Field(0.0, description="Segundo exato da cena em que o efeito toca")


class SceneVisualConfig(BaseModel):
    template: Optional[str] = Field(None, description="Nome do componente Remotion (ex: DataChartCard)")
    props: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Propriedades React passadas para o componente")
    search_query: Optional[str] = Field(None, description="Termo de busca em inglês para B-Roll de estoque")
    source: Optional[str] = Field(None, description="Fonte de mídia (pexels, pixabay, wikimedia, comfyui)")
    image_prompt: Optional[str] = Field(None, description="Prompt detalhado se a cena demandar imagem IA estática")
    camera_motion: Optional[str] = Field("push_in", description="Tipo de movimento de câmera 2.5D no Remotion")


class SceneItem(BaseModel):
    scene_id: int = Field(..., description="Identificador sequencial da cena (1, 2, 3...)")
    narration_text: str = Field(..., description="Texto da locução para esta cena")
    start_time: float = Field(0.0, description="Timestamp de início em segundos no áudio mestre")
    end_time: float = Field(0.0, description="Timestamp de término em segundos no áudio mestre")
    visual_type: VisualTypeEnum = Field(..., description="Tipo de elemento visual primário da cena")
    visual_config: SceneVisualConfig = Field(default_factory=SceneVisualConfig)
    sfx: List[SFXEvent] = Field(default_factory=list, description="Lista de efeitos sonoros associados")
    raw_audio_path: Optional[str] = Field(None, description="Caminho do áudio individual da cena")
    rendered_clip_path: Optional[str] = Field(None, description="Caminho do vídeo/animação renderizado para esta cena")

    @property
    def duration_sec(self) -> float:
        return max(0.0, self.end_time - self.start_time)


class StageTracker(BaseModel):
    stage1_director: StageStatusEnum = StageStatusEnum.PENDING
    stage2_audio: StageStatusEnum = StageStatusEnum.PENDING
    stage3_captions: StageStatusEnum = StageStatusEnum.PENDING
    stage4_broll: StageStatusEnum = StageStatusEnum.PENDING
    stage5_motion: StageStatusEnum = StageStatusEnum.PENDING
    stage6_assembler: StageStatusEnum = StageStatusEnum.PENDING


class ResolutionConfig(BaseModel):
    width: int = 1920
    height: int = 1080


class ProjectManifest(BaseModel):
    project_id: str = Field(..., description="Slug único do projeto (ex: doc_crise_subprime_2008)")
    title: str = Field(..., description="Título formal do documentário")
    fps: int = Field(30, description="Taxa de quadros por segundo")
    resolution: ResolutionConfig = Field(default_factory=ResolutionConfig)
    stage_status: StageTracker = Field(default_factory=StageTracker)
    
    # Arquivos Mestres
    audio_master: Optional[str] = Field(None, description="Caminho do áudio narrado mestre (após auto-editor)")
    captions_ass: Optional[str] = Field(None, description="Caminho do arquivo de legendas .ass compilado")
    bgm_track: Optional[str] = Field(None, description="Caminho da música de fundo em assets/bgm/")
    final_video_path: Optional[str] = Field(None, description="Caminho do vídeo final MP4 renderizado")
    otio_project_path: Optional[str] = Field(None, description="Caminho da timeline exportada para o Kdenlive (.otio)")

    # Cenas
    scenes: List[SceneItem] = Field(default_factory=list)

    def save(self, filepath: Path) -> None:
        """Salva o manifesto em disco formatado com indentação legível."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, filepath: Path) -> "ProjectManifest":
        """Carrega e valida o manifesto a partir do disco."""
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())
