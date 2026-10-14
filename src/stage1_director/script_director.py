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

DIRECTOR_SYSTEM_PROMPT = """Você é um Diretor de Cinema e Roteirista Chefe especializado em documentários cinematográficos de alta retenção (estilo Vox, Johnny Harris, Lemmino e BBC).

Sua missão é transformar o TEMA fornecido em um ROTEIRO CINEMATOGRÁFICO com 3 ou 4 cenas dinâmicas (4 a 8 segundos cada).

REGRAS OBRIGATÓRIAS DE COERÊNCIA CONTEXTUAL E VISUAL:
1. SE O TEMA FOR HISTÓRICO ANTIGO, NATURAL OU ARQUEOLÓGICO (ex: Pompeia, Vulcão Vesúvio, Roma Antiga, Grécia, Dinossauros):
   - NUNCA use "remotion_graphic" com templates de "NewspaperHighlight" (jornais modernos impressos com manchetes sensacionalistas NÃO existiam na antiguidade!).
   - NUNCA use "DataChartCard" com cifrões ou trilhões de dólares.
   - USE "historic_media" (afrescos, pinturas clássicas, ruínas arqueológicas, mapas antigos de época).
   - USE "parallax_25d" (estátuas romanas, bustos, o próprio vulcão ou ruínas com efeito de profundidade 3D).
   - USE "stock_broll" (paisagens vulcânicas, cinzas, mar, escavações).
   - Em "search_query", forneça termos em inglês claros e descritivos para o acervo histórico (ex: "Mount Vesuvius ancient eruption painting", "Pompeii archaeological ruins aerial").

2. SE O TEMA FOR MODERNO (século XX e XXI, política, escândalos, crimes contemporâneos):
   - Pode usar "NewspaperHighlight" para manchetes históricas de jornais da época.
   - Pode usar "DataChartCard" para dados numéricos com unidade condizente.

3. SCHEMA OBRIGATÓRIO (JSON PURO):
{
  "title": "Título Imersivo do Documentário",
  "scenes": [
    {
      "scene_id": 1,
      "narration_text": "Texto fluído, cinematográfico, natural e dramático em português.",
      "start_time": 0.0,
      "end_time": 6.5,
      "visual_type": "historic_media",
      "visual_config": {
        "search_query": "Pompeii ancient ruins sunset",
        "camera_motion": "push_in",
        "template": null,
        "props": {}
      },
      "sfx": [{"name": "whoosh_deep.wav", "offset_sec": 0.0}]
    }
  ]
}
Responda EXCLUSIVAMENTE com o JSON válido, sem texto fora das chaves.
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

    def _is_ollama_available(self) -> bool:
        """Verifica se o servidor local Ollama está ativo na porta 11434."""
        try:
            import requests
            r = requests.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def generate_script(self, topic_or_text: str, project_id: str, title: Optional[str] = None) -> ProjectManifest:
        """
        Dispara chamada para IA local (Ollama Qwen 2.5) ou remota (Gemini/Groq)
        para gerar roteiro com fidelidade contextual e estética investigativa.
        """
        load_dotenv(override=True)
        import litellm

        # 1. Prioridade A: IA Local no Hardware (Ollama Qwen 2.5 3B) - Zero custo, 100% privado e veloz
        if self._is_ollama_available():
            try:
                logger.info("Executando roteirização via IA Local no hardware (Ollama: qwen2.5:3b)...")
                response = litellm.completion(
                    model="ollama_chat/qwen2.5:3b",
                    messages=[
                        {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Tema do documentário: {topic_or_text}\n\nGere o JSON completo de cenas para este tema."}
                    ],
                    api_base="http://127.0.0.1:11434",
                    temperature=0.3,
                )
                raw_content = response.choices[0].message.content.strip()
                raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                logger.info("Roteiro contextual gerado com sucesso pela IA Local!")
                return self._build_manifest_from_parsed(parsed, project_id, title or topic_or_text)
            except Exception as e:
                logger.warning("Falha na chamada ao Ollama local (%s). Testando provedores alternativos.", str(e))

        # 2. Prioridade B: LiteLLM com Provedores de Nuvem (Gemini / Groq)
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        has_groq = bool(os.getenv("GROQ_API_KEY"))

        if has_gemini or has_groq:
            try:
                model_name = self.config.get("llm", {}).get("primary_provider", "gemini/gemini-2.5-flash")
                if not has_gemini and has_groq:
                    model_name = self.config.get("llm", {}).get("fallback_provider", "groq/llama-3.3-70b-versatile")

                logger.info("Solicitando roteiro investigativo ao modelo em nuvem: %s", model_name)
                response = litellm.completion(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": DIRECTOR_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Tema do documentário: {topic_or_text}\n\nGere o JSON completo de cenas para este tema."}
                    ],
                    temperature=0.5,
                )
                raw_content = response.choices[0].message.content.strip()
                raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                return self._build_manifest_from_parsed(parsed, project_id, title or topic_or_text)
            except Exception as e:
                logger.warning("Falha na chamada LLM em nuvem (%s).", str(e))

        logger.info("Utilizando gerador determinístico inteligente de demonstração.")
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
        com estrita coerência de época e contexto.
        """
        clean_topic = topic.strip()
        lower_t = clean_topic.lower()
        words = [w for w in re.split(r"\s+", clean_topic) if len(w) > 2]
        clean_query = re.sub(r"[^\w\s]", "", clean_topic)

        # Detecta se é tema histórico antigo, natural ou arqueológico
        ancient_keywords = ["vesúvio", "vesuvio", "pompeia", "pompeii", "roma", "romano", "grécia", "grego", "egito", "faraó", "antigo", "antiguidade", "dinossauro", "vulcão", "vulcao", "arqueolog", "império romano"]
        is_ancient = any(k in lower_t for k in ancient_keywords)

        if is_ancient:
            scenes = [
                SceneItem(
                    scene_id=1,
                    narration_text=f"Sob o céu da Campânia romana, {clean_topic} guardava uma força oculta prestes a transformar para sempre o curso da história.",
                    start_time=0.0,
                    end_time=6.5,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query=f"{clean_query} ancient ruins painting",
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0),
                        SFXEvent(name="whoosh_deep.wav", offset_sec=1.5)
                    ]
                ),
                SceneItem(
                    scene_id=2,
                    narration_text=f"Em questão de horas, a força avassaladora da natureza soterrou cidades inteiras, congelando vidas e monumentos no tempo.",
                    start_time=6.5,
                    end_time=13.0,
                    visual_type=VisualTypeEnum.PARALLAX_25D,
                    visual_config=SceneVisualConfig(
                        search_query=f"{clean_query} volcano eruption",
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                ),
                SceneItem(
                    scene_id=3,
                    narration_text=f"Hoje, os vestígios arqueológicos preservados sob metros de cinzas revelam ao mundo moderno os segredos intactos dessa tragédia.",
                    start_time=13.0,
                    end_time=19.5,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query=f"{clean_query} archaeological excavation ruins",
                        camera_motion="drift_left"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                )
            ]
        else:
            highlight = " ".join(words[:3]).upper() if words else clean_topic.upper()
            scenes = [
                SceneItem(
                    scene_id=1,
                    narration_text=f"Por trás dos registros oficiais sobre {clean_topic}, escondem-se detalhes cruciais que desafiam a versão convencional dos fatos.",
                    start_time=0.0,
                    end_time=6.5,
                    visual_type=VisualTypeEnum.REMOTION_GRAPHIC,
                    visual_config=SceneVisualConfig(
                        template="NewspaperHighlight",
                        props={
                            "headline": f"REVELAÇÃO: O CASO DE {clean_topic.upper()}",
                            "source_label": "Arquivo Investigativo - Edição Especial",
                            "highlight_words": highlight,
                            "date_label": "Dossiê Exclusivo"
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
                    narration_text=f"Para compreender a real dimensão dos acontecimentos em torno de {clean_topic}, os dados apontam para uma progressão dramática.",
                    start_time=6.5,
                    end_time=13.0,
                    visual_type=VisualTypeEnum.PARALLAX_25D,
                    visual_config=SceneVisualConfig(
                        search_query=clean_query,
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0),
                        SFXEvent(name="digital_beep.wav", offset_sec=1.5)
                    ]
                ),
                SceneItem(
                    scene_id=3,
                    narration_text=f"Até os dias de hoje, as consequências e os desdobramentos sobre {clean_topic} continuam a repercutir no cenário global.",
                    start_time=13.0,
                    end_time=19.0,
                    visual_type=VisualTypeEnum.STOCK_BROLL,
                    visual_config=SceneVisualConfig(
                        search_query=clean_query,
                        camera_motion="drift_left"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                )
            ]

        manifest = ProjectManifest(
            project_id=project_id,
            title=title or f"Documentário: {clean_topic}",
            scenes=scenes
        )
        manifest.stage_status.stage1_director = StageStatusEnum.COMPLETED
        return manifest


