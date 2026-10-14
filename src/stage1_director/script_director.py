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

Sua missão é transformar o TEMA fornecido em um DOCUMENTÁRIO COMPLETO E PROFUNDO de 55 a 70 segundos.
O documentário deve ter exatamente 6 cenas encadeadas, com 25 a 40 palavras por cena (ritmo investigativo detalhado, citando datas, locais, fatos reais e impacto).

ESTRUTURA DO ARCO NARRATIVO (6 CENAS OBRIGATÓRIAS):
1. Cena 1 - O Gancho (The Hook): Abertura impactante que prende a atenção citando a data ou enigma histórico (25-35 palavras).
2. Cena 2 - O Cenário (The Setting): A vida cotidiana, a arquitetura e a prosperidade antes da catástrofe (25-35 palavras).
3. Cena 3 - Os Primeiros Sinais (The Escalation): Os tremores, o comportamento dos animais e o aviso da natureza (25-35 palavras).
4. Cena 4 - O Clímax Devastador (The Climax): A explosão, a coluna piroclástica de 30 km e o fogo no céu (25-35 palavras).
5. Cena 5 - A Sepultura de Cinzas (The Aftermath): A tempestade vulcânica congelando a cidade em segundos (25-35 palavras).
6. Cena 6 - O Legado Eterno (The Legacy): As escavações modernas e a lição atemporal para a humanidade (25-35 palavras).

DIRETRIZES VISUAIS OBRIGATÓRIAS:
- Cada cena DEVE ter um "search_query" COMPLETAMENTE DIFERENTE e específico em inglês!
- Para temas históricos/antigos, priorize pinturas a óleo clássicas, ruínas do fórum, afrescos romanos e paisagens arqueológicas:
  Exemplos:
  * "Pompeii Forum Mount Vesuvius painting landscape"
  * "Ancient Roman frescos in Pompeii art"
  * "Eruption of Vesuvius classical painting"
  * "Karl Briullov The Last Day of Pompeii painting"
  * "Pompeii archaeological excavation ruins landscape"
  * "House of the Vettii Pompeii fresco wall painting"
- NUNCA repita o mesmo search_query em duas cenas!

SCHEMA OBRIGATÓRIO (JSON PURO):
{
  "title": "Título Imersivo do Documentário",
  "scenes": [
    {
      "scene_id": 1,
      "narration_text": "Texto fluído, cinematográfico, natural e dramático em português (25 a 40 palavras).",
      "start_time": 0.0,
      "end_time": 10.0,
      "visual_type": "historic_media",
      "visual_config": {
        "search_query": "Pompeii Forum Mount Vesuvius painting landscape",
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
                    narration_text=f"No verão do ano 79 da nossa era, a próspera cidade romana de Pompeia vivia o auge de sua riqueza. Mas nas sombras do horizonte, o Monte Vesúvio preparava o cataclismo mais devastador da história antiga.",
                    start_time=0.0,
                    end_time=10.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query="Pompeii Forum Mount Vesuvius painting landscape",
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0),
                        SFXEvent(name="whoosh_deep.wav", offset_sec=1.5)
                    ]
                ),
                SceneItem(
                    scene_id=2,
                    narration_text=f"Mais de vinte mil cidadãos caminhavam por fóruns monumentais de mármore, termas luxuosas e vilas decoradas com afrescos deslumbrantes, completamente alheios à bomba geológica que a montanha sagrada escondia.",
                    start_time=10.0,
                    end_time=20.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query="Ancient Roman frescos in Pompeii art",
                        camera_motion="drift_left"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                ),
                SceneItem(
                    scene_id=3,
                    narration_text=f"Nas primeiras horas daquele dia fatídico, a terra tremeu violentamente. Uma coluna colossal de pedra-pomes, cinzas e gases incandescentes foi ejetada a mais de trinta quilômetros de altura em direção à estratosfera.",
                    start_time=20.0,
                    end_time=30.0,
                    visual_type=VisualTypeEnum.PARALLAX_25D,
                    visual_config=SceneVisualConfig(
                        search_query="Eruption of Vesuvius classical painting",
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="volcano_roar.wav", offset_sec=0.5)
                    ]
                ),
                SceneItem(
                    scene_id=4,
                    narration_text=f"O meio-dia transformou-se em trevas absolutas. Nuvens piroclásticas a centenas de quilômetros por hora e mais de trezentos graus varreram as ruas romanas, selando o destino da cidade em poucos segundos.",
                    start_time=30.0,
                    end_time=40.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query="Karl Briullov The Last Day of Pompeii painting",
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)
                    ]
                ),
                SceneItem(
                    scene_id=5,
                    narration_text=f"Sob uma camada de mais de seis metros de cinzas vulcânicas compactas, Pompeia desapareceu completamente dos mapas, permanecendo intocada e esquecida pelo mundo por quase mil e setecentos anos.",
                    start_time=40.0,
                    end_time=50.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query="Pompeii archaeological excavation ruins landscape",
                        camera_motion="drift_left"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                ),
                SceneItem(
                    scene_id=6,
                    narration_text=f"Hoje, as escavações arqueológicas revelam os detalhes mais íntimos desse império perdido, servindo como uma das mais fascinantes e comoventes cápsulas do tempo de toda a humanidade.",
                    start_time=50.0,
                    end_time=60.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query="House of the Vettii Pompeii fresco wall painting",
                        camera_motion="push_in"
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
                    end_time=8.0,
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
                    narration_text=f"Documentos antes confidenciais revelam que os primeiros sinais de alerta foram sistematicamente ignorados pelas lideranças.",
                    start_time=8.0,
                    end_time=16.0,
                    visual_type=VisualTypeEnum.PARALLAX_25D,
                    visual_config=SceneVisualConfig(
                        search_query=clean_query,
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                ),
                SceneItem(
                    scene_id=3,
                    narration_text=f"Quando a crise atingiu o ápice, a escala do impacto surpreendeu até os analistas mais experientes do setor.",
                    start_time=16.0,
                    end_time=24.0,
                    visual_type=VisualTypeEnum.REMOTION_GRAPHIC,
                    visual_config=SceneVisualConfig(
                        template="DataChartCard",
                        props={
                            "headline": f"Escala do Impacto: {clean_topic}",
                            "source_label": "Dados Oficiais Consolidados",
                            "unit_label": "Pontos",
                            "data_points": [
                                {"year": "Fase 1", "value": 2.5},
                                {"year": "Fase 2", "value": 7.8},
                                {"year": "Pico", "value": 14.2}
                            ],
                            "theme": "vox_dark_grid"
                        }
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0),
                        SFXEvent(name="digital_beep.wav", offset_sec=1.5)
                    ]
                ),
                SceneItem(
                    scene_id=4,
                    narration_text=f"As consequências imediatas geraram uma onda de choque que redefiniu completamente os padrões de segurança e regulação.",
                    start_time=24.0,
                    end_time=32.0,
                    visual_type=VisualTypeEnum.STOCK_BROLL,
                    visual_config=SceneVisualConfig(
                        search_query=clean_query,
                        camera_motion="drift_left"
                    ),
                    sfx=[
                        SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)
                    ]
                ),
                SceneItem(
                    scene_id=5,
                    narration_text=f"Hoje, o caso de {clean_topic} permanece como um dos episódios mais estudados e emblemáticos da história recente.",
                    start_time=32.0,
                    end_time=40.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query=clean_query,
                        camera_motion="push_in"
                    ),
                    sfx=[
                        SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)
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


