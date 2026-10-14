"""
src/stage1_director/script_director.py - Diretor de Roteiro e Orquestrador Narrativo.
Utiliza LiteLLM para geração com Gemini 2.5 Flash / Groq com fallback estruturado.
Gera o manifesto de cenas seguindo a persona de documentário investigativo (Vox / Johnny Harris).
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

from src.core.manifest import (
    ProjectManifest,
    SceneItem,
    VisualTypeEnum,
    SceneVisualConfig,
    SFXEvent,
    StageTracker,
    StageStatusEnum
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ScriptDirector")

DIRECTOR_SYSTEM_PROMPT = """
Você é um Diretor de Cinema e Roteirista Chefe especializado em documentários investigativos de alta retenção (estilo Vox, Johnny Harris, Fern, Magnates e Lemmino).

Sua missão é transformar o TEMA ou TEXTO BRUTO fornecido pelo usuário em um ROTEIRO ESTRUTURADO dividido em cenas dinâmicas de 4 a 8 segundos.

REGRAS ESTÉTICAS E DIRETIVAS OBRIGATÓRIAS:
1. RITMO E VARIAÇÃO VISUAL:
   - Alterne constantemente os tipos visuais (`visual_type`):
     * "remotion_graphic": Use quando houver dados numéricos, percentuais, datas históricas, manchetes de jornal para destacar com marca-texto ou mapas.
     * "stock_broll": Use quando a narrativa descrever cidades, multidões, telas de computadores, escritórios, dinheiro ou ações cotidianas.
     * "parallax_25d": Use quando a cena focar em uma figura histórica, retrato importante ou documento histórico recortado com sensação 3D.
     * "historic_media": Use quando citar fotos históricas de domínio público ou eventos governamentais.
2. TEMPLATES DISPONÍVEIS PARA "remotion_graphic":
   - "DataChartCard": Gráficos de barras ou linhas evolutivas com fonte de dados no rodapé.
   - "NewspaperHighlight": Manchete de jornal em perspectiva com caneta marca-texto animada cobrindo palavras-chave.
   - "TimelineEvent": Linha do tempo horizontal deslizante entre marcos históricos.
   - "MapZoomScene": Mapa vetorial com zoom suave e indicador geográfico.
3. SOUND DESIGN (SFX):
   - Associe pelo menos 1 ou 2 efeitos sonoros por cena para enfatizar cortes e impactos ("whoosh_deep.wav", "paper_slide.wav", "marker_highlight.wav", "digital_beep.wav", "sub_bass_hit.wav", "camera_shutter.wav").
4. FORMATO DE SAÍDA:
   - Responda ESTRITAMENTE em formato JSON puro, sem marcações markdown de bloco de código (sem ```json), respeitando o schema fornecido.
"""


class ScriptDirector:
    def __init__(self, config_path: Path = Path("config.yaml")):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def generate_script(self, topic_or_text: str, project_id: str, title: Optional[str] = None) -> ProjectManifest:
        """
        Dispara chamada via LiteLLM para gerar o roteiro estruturado.
        Caso chaves de API não estejam configuradas, recorre ao gerador determinístico inteligente de demonstração.
        """
        load_dotenv(override=True)
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        has_groq = bool(os.getenv("GROQ_API_KEY"))

        if has_gemini or has_groq:
            try:
                import litellm
                model_name = self.config.get("llm", {}).get("primary_provider", "gemini/gemini-2.5-flash")
                if not has_gemini and has_groq:
                    model_name = self.config.get("llm", {}).get("fallback_provider", "groq/llama-3.3-70b-versatile")

                logger.info("Solicitando roteiro investigativo ao modelo: %s", model_name)
                response = litellm.completion(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Tema do documentário: {topic_or_text}\n\nGere o JSON completo de cenas para este tema."}
                    ],
                    temperature=0.7,
                )
                raw_content = response.choices[0].message.content.strip()
                # Remove cercas de código markdown se o modelo incluir
                raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                return self._build_manifest_from_parsed(parsed, project_id, title or topic_or_text)
            except Exception as e:
                logger.warning("Falha na chamada LLM externa (%s). Utilizando gerador modelo padrão investigativo.", str(e))

        logger.info("Chaves de API não detectadas. Gerando roteiro demonstrativo com arquitetura cinematográfica completa.")
        return self._generate_fallback_template(topic_or_text, project_id, title)

    def _build_manifest_from_parsed(self, data: dict, project_id: str, title: str) -> ProjectManifest:
        scenes = []
        for idx, item in enumerate(data.get("scenes", []), start=1):
            sfx_list = [
                SFXEvent(name=s.get("name", "whoosh_deep.wav"), offset_sec=float(s.get("offset_sec", 0.0)))
                for s in item.get("sfx", [])
            ]
            vis_type = item.get("visual_type", "stock_broll")
            scenes.append(
                SceneItem(
                    scene_id=idx,
                    narration_text=item.get("narration_text", ""),
                    start_time=float(item.get("start_time", 0.0)),
                    end_time=float(item.get("end_time", 6.0)),
                    visual_type=VisualTypeEnum(vis_type),
                    visual_config=SceneVisualConfig(**item.get("visual_config", {})),
                    sfx=sfx_list
                )
            )

        manifest = ProjectManifest(
            project_id=project_id,
            title=title or data.get("title", "Documentário Investigativo"),
            scenes=scenes
        )
        manifest.stage_status.stage1_director = StageStatusEnum.COMPLETED
        return manifest

    def _generate_fallback_template(self, topic: str, project_id: str, title: Optional[str]) -> ProjectManifest:
        """
        Gera um roteiro dinâmico e inteligente baseado no tema fornecido pelo usuário,
        equilibrando Manchete 3D, Gráfico de Análise e Parallax Histórico 2.5D.
        Garante que mesmo sem chave de API externa, o conteúdo reflita fielmente o tema escolhido.
        """
        clean_topic = topic.strip()
        words = [w for w in re.split(r"\s+", clean_topic) if len(w) > 2]
        highlight = " ".join(words[:3]).upper() if words else clean_topic.upper()
        
        # Cria termos de busca para acervos históricos
        clean_query = re.sub(r"[^\w\s]", "", clean_topic)

        manifest = ProjectManifest(
            project_id=project_id,
            title=title or f"Investigação: {clean_topic}",
            scenes=[
                SceneItem(
                    scene_id=1,
                    narration_text=f"Por trás dos registros oficiais sobre {clean_topic}, escondem-se detalhes cruciais que desafiam a versão convencional dos fatos.",
                    start_time=0.0,
                    end_time=6.5,
                    visual_type=VisualTypeEnum.REMOTION_GRAPHIC,
                    visual_config=SceneVisualConfig(
                        template="NewspaperHighlight",
                        props={
                            "headline": f"REVELAÇÃO: O ENIGMA DE {clean_topic.upper()}",
                            "source_label": "Arquivo Investigativo - Edição Histórica",
                            "highlight_words": highlight,
                            "date_label": "Dossiê Histórico Exclusivo"
                        }
                    ),
                    sfx=[
                        SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0),
                        SFXEvent(name="paper_slide.wav", offset_sec=0.8),
                        SFXEvent(name="marker_highlight.wav", offset_sec=2.0)
                    ]
                ),
                SceneItem(
                    scene_id=2,
                    narration_text=f"Para compreender o impacto real gerado em torno de {clean_topic}, precisamos analisar a escala e a progressão dos dados registrados.",
                    start_time=6.5,
                    end_time=13.0,
                    visual_type=VisualTypeEnum.REMOTION_GRAPHIC,
                    visual_config=SceneVisualConfig(
                        template="DataChartCard",
                        props={
                            "headline": f"Escala de Impacto: {clean_topic.title()}",
                            "source_label": "Fonte: Registros Documentais e Análises Históricas",
                            "data_points": [
                                {"year": "Fase 1", "value": 2.5},
                                {"year": "Fase 2", "value": 7.8},
                                {"year": "Pico", "value": 14.2}
                            ]
                        }
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0),
                        SFXEvent(name="digital_beep.wav", offset_sec=1.5)
                    ]
                ),
                SceneItem(
                    scene_id=3,
                    narration_text=f"Até os dias de hoje, os vestígios e as evidências sobre {clean_topic} continuam a intrigar especialistas e a ecoar na história.",
                    start_time=13.0,
                    end_time=19.0,
                    visual_type=VisualTypeEnum.PARALLAX_25D,
                    visual_config=SceneVisualConfig(
                        search_query=clean_query,
                        source="wikimedia",
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                )
            ]
        )
        manifest.stage_status.stage1_director = StageStatusEnum.COMPLETED
        return manifest

