"""
src/stage1_director/script_director.py - Diretor de Roteiro e Orquestrador Narrativo.
Utiliza o 9router local (modelo 'arsenal') para decupagem cinematográfica contextual de alto nível.
Fallback inteligente para LiteLLM (Gemini/Groq/Ollama) e gerador determinístico calibrado.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import urllib.request
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

# Configurações do 9router local
NINEROUTER_URL = "http://localhost:20128/v1/chat/completions"
NINEROUTER_KEY = os.getenv("NINEROUTER_API_KEY", "sk-4c63780906a3c8d8-de7pfy-33201f8c")
NINEROUTER_MODEL = "arsenal"

DIRECTOR_PROMPT_30S = """Você é um Diretor de Cinema e Roteirista Chefe especializado em documentários cinematográficos de alta retenção (estilo Vox, Johnny Harris, Lemmino e BBC).

Sua missão é transformar o TEMA fornecido em um DOCUMENTÁRIO DE TESTE DE BANCADA DE EXATAMENTE 30 SEGUNDOS.
O documentário deve ter exatamente 3 cenas encadeadas:
1. Cena 1 - O Gancho (The Hook): Abertura impactante citando a data e o cenário (20 a 25 palavras).
2. Cena 2 - O Clímax / Catástrofe: O evento central com dados precisos e força dramática (20 a 25 palavras).
3. Cena 3 - O Desfecho e Legado: A consequência histórica duradoura e lição temporal (20 a 25 palavras).
TOTAL DO DOCUMENTÁRIO: 65 a 75 palavras no total.

DIRETRIZES VISUAIS OBRIGATÓRIAS (SHOT LIST CIRÚRGICA):
- Cada cena DEVE ter um "search_query" COMPLETAMENTE DIFERENTE e específico em inglês!
- Para temas históricos/antigos, priorize pinturas clássicas consagradas, afrescos romanos autênticos e ruínas arqueológicas em alta resolução:
  Exemplos de busca precisos:
  * "Pompeii Forum Mount Vesuvius painting landscape"
  * "Eruption of Vesuvius classical painting"
  * "Karl Briullov The Last Day of Pompeii painting"
  * "House of the Vettii Pompeii fresco wall painting"
- NUNCA use termos genéricos como "ancient rome", "italy" ou "volcano". Cite a obra ou o local exato!
- NUNCA repita o mesmo search_query em duas cenas!

SCHEMA OBRIGATÓRIO (JSON PURO):
{
  "title": "Título Imersivo do Documentário",
  "scenes": [
    {
      "scene_id": 1,
      "narration_text": "Texto fluído, cinematográfico, natural e dramático em português (20 a 25 palavras).",
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

DIRECTOR_PROMPT_60S = """Você é um Diretor de Cinema e Roteirista Chefe especializado em documentários cinematográficos de alta retenção (estilo Vox, Johnny Harris, Lemmino e BBC).

Sua missão é transformar o TEMA fornecido em um DOCUMENTÁRIO COMPLETO E PROFUNDO de 55 a 65 segundos.
O documentário deve ter exatamente 6 cenas encadeadas, com 25 a 35 palavras por cena (140 a 170 palavras no total).

ESTRUTURA DO ARCO NARRATIVO (6 CENAS OBRIGATÓRIAS):
1. Cena 1 - O Gancho (The Hook): Abertura impactante citando data ou enigma histórico (25-30 palavras).
2. Cena 2 - O Cenário (The Setting): A vida cotidiana e prosperidade antes da catástrofe (25-30 palavras).
3. Cena 3 - Os Primeiros Sinais (The Escalation): Tremores, comportamento animal e aviso da natureza (25-30 palavras).
4. Cena 4 - O Clímax Devastador (The Climax): A explosão piroclástica de 30 km e o fogo no céu (25-30 palavras).
5. Cena 5 - A Sepultura de Cinzas (The Aftermath): A tempestade vulcânica congelando a cidade em segundos (25-30 palavras).
6. Cena 6 - O Legado Eterno (The Legacy): As escavações modernas e a lição atemporal para a humanidade (25-30 palavras).

DIRETRIZES VISUAIS OBRIGATÓRIAS (SHOT LIST CIRÚRGICA):
- Cada cena DEVE ter um "search_query" COMPLETAMENTE DIFERENTE e específico em inglês!
- Para temas históricos/antigos, priorize pinturas clássicas consagradas, afrescos romanos e ruínas arqueológicas:
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
      "narration_text": "Texto fluído, cinematográfico, natural e dramático em português (25 a 35 palavras).",
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

    def _is_9router_available(self) -> bool:
        """Verifica se o servidor 9router local está ativo na porta 20128."""
        try:
            req = urllib.request.Request("http://localhost:20128/v1/models")
            with urllib.request.urlopen(req, timeout=1.5) as r:
                return r.status == 200
        except Exception:
            return False

    def _call_9router(self, system_prompt: str, user_content: str) -> Optional[dict]:
        """Dispara chamada OpenAI-compatible para o 9router local com modelo de alta inteligência 'arsenal'."""
        try:
            payload = {
                "model": NINEROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "stream": False,
                "temperature": 0.3
            }
            req = urllib.request.Request(
                NINEROUTER_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {NINEROUTER_KEY}"
                },
                data=json.dumps(payload).encode("utf-8")
            )
            with urllib.request.urlopen(req, timeout=40) as r:
                res_data = json.loads(r.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"].strip()
                raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                return parsed
        except Exception as e:
            logger.warning("Falha na chamada ao 9router local (%s).", str(e))
            return None

    def _is_ollama_available(self) -> bool:
        """Verifica se o servidor local Ollama está ativo na porta 11434."""
        try:
            import requests
            r = requests.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def generate_script(
        self,
        topic_or_text: str,
        project_id: str,
        title: Optional[str] = None,
        target_duration_sec: int = 30
    ) -> ProjectManifest:
        """
        Dispara decupagem cinematográfica inteligente para o tema indicado.
        Prioriza o 9router local com modelo de fronteira (arsenal).
        """
        load_dotenv(override=True)
        
        # Seleciona prompt calibrado para o alvo de duração
        system_prompt = DIRECTOR_PROMPT_30S if target_duration_sec <= 35 else DIRECTOR_PROMPT_60S
        user_prompt = (
            f"Tema do documentário: {topic_or_text}\n"
            f"Duração desejada: {target_duration_sec} segundos.\n"
            f"Gere o JSON completo de cenas para este tema."
        )

        # 1. Prioridade A: 9router local (modelo de ponta 'arsenal' conectado)
        if self._is_9router_available():
            logger.info("Executando roteirização via 9router local (modelo 'arsenal')...")
            parsed = self._call_9router(system_prompt, user_prompt)
            if parsed and "scenes" in parsed and len(parsed["scenes"]) > 0:
                logger.info("Roteiro contextual e Shot List gerados com sucesso pelo 9router (%d cenas)!", len(parsed["scenes"]))
                return self._build_manifest_from_parsed(parsed, project_id, title or topic_or_text, target_duration_sec)

        # 2. Prioridade B: LiteLLM com Provedores de Nuvem (Gemini / Groq)
        import litellm
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
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.4,
                )
                raw_content = response.choices[0].message.content.strip()
                raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                return self._build_manifest_from_parsed(parsed, project_id, title or topic_or_text, target_duration_sec)
            except Exception as e:
                logger.warning("Falha na chamada LLM em nuvem (%s).", str(e))

        # 3. Prioridade C: Ollama Local
        if self._is_ollama_available():
            try:
                logger.info("Tentando fallback via Ollama local (qwen2.5:3b)...")
                response = litellm.completion(
                    model="ollama_chat/qwen2.5:3b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    api_base="http://127.0.0.1:11434",
                    temperature=0.3,
                )
                raw_content = response.choices[0].message.content.strip()
                raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                return self._build_manifest_from_parsed(parsed, project_id, title or topic_or_text, target_duration_sec)
            except Exception as e:
                logger.warning("Falha no Ollama (%s).", str(e))

        logger.info("Utilizando gerador determinístico inteligente de demonstração.")
        return self._generate_fallback_template(topic_or_text, project_id, title, target_duration_sec)

    def _build_manifest_from_parsed(
        self,
        data: dict,
        project_id: str,
        title: str,
        target_duration_sec: int
    ) -> ProjectManifest:
        scenes = []
        raw_scenes = data.get("scenes", [])
        num_scenes = max(1, len(raw_scenes))
        time_per_scene = target_duration_sec / num_scenes

        current_time = 0.0
        for idx, item in enumerate(raw_scenes, start=1):
            sfx_list = [
                SFXEvent(name=s.get("name", "whoosh_deep.wav"), offset_sec=float(s.get("offset_sec", 0.0)))
                for s in item.get("sfx", [])
            ]
            vis_type = item.get("visual_type", "historic_media")
            # Valida enum
            try:
                valid_vis_type = VisualTypeEnum(vis_type)
            except ValueError:
                valid_vis_type = VisualTypeEnum.HISTORIC_MEDIA

            end_t = round(current_time + time_per_scene, 2)
            scenes.append(
                SceneItem(
                    scene_id=idx,
                    narration_text=item.get("narration_text", "").strip(),
                    start_time=round(current_time, 2),
                    end_time=end_t,
                    visual_type=valid_vis_type,
                    visual_config=SceneVisualConfig(**item.get("visual_config", {})),
                    sfx=sfx_list
                )
            )
            current_time = end_t

        manifest = ProjectManifest(
            project_id=project_id,
            title=title or data.get("title", "Documentário Investigativo"),
            scenes=scenes
        )
        manifest.stage_status.stage1_director = StageStatusEnum.COMPLETED
        return manifest

    def _generate_fallback_template(
        self,
        topic: str,
        project_id: str,
        title: Optional[str],
        target_duration_sec: int
    ) -> ProjectManifest:
        clean_topic = topic.strip()
        lower_t = clean_topic.lower()
        ancient_keywords = [
            "vesúvio", "vesuvio", "pompeia", "pompeii", "roma", "romano",
            "grécia", "grego", "egito", "faraó", "antigo", "antiguidade", "vulcão", "vulcao"
        ]
        is_ancient = any(k in lower_t for k in ancient_keywords)

        if is_ancient:
            if target_duration_sec <= 35:
                # 30 segundos (3 cenas, ~74 palavras)
                scenes = [
                    SceneItem(
                        scene_id=1,
                        narration_text="No verão do ano 79 da nossa era, a próspera cidade romana de Pompeia vivia o auge de sua riqueza, sem imaginar o cataclismo que o Monte Vesúvio preparava nas sombras.",
                        start_time=0.0,
                        end_time=10.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="Pompeii Forum Mount Vesuvius painting landscape",
                            camera_motion="push_in"
                        ),
                        sfx=[SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)]
                    ),
                    SceneItem(
                        scene_id=2,
                        narration_text="Uma coluna colossal de pedra-pomes e gases incandescentes foi ejetada a mais de trinta quilômetros de altura, transformando o meio-dia em trevas e engolindo as ruas romanas.",
                        start_time=10.0,
                        end_time=20.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="Eruption of Vesuvius classical painting",
                            camera_motion="push_in"
                        ),
                        sfx=[SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)]
                    ),
                    SceneItem(
                        scene_id=3,
                        narration_text="Sob seis metros de cinzas vulcânicas, Pompeia desapareceu dos mapas por quase dois mil anos, tornando-se a cápsula do tempo mais fascinante e comovente da humanidade.",
                        start_time=20.0,
                        end_time=30.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="Karl Briullov The Last Day of Pompeii painting",
                            camera_motion="drift_left"
                        ),
                        sfx=[SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)]
                    )
                ]
            else:
                # 60 segundos (6 cenas)
                scenes = [
                    SceneItem(
                        scene_id=1,
                        narration_text="No verão do ano 79 da nossa era, a próspera cidade romana de Pompeia vivia o auge de sua riqueza. Mas nas sombras do horizonte, o Monte Vesúvio preparava o cataclismo mais devastador da história antiga.",
                        start_time=0.0,
                        end_time=10.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="Pompeii Forum Mount Vesuvius painting landscape",
                            camera_motion="push_in"
                        ),
                        sfx=[SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)]
                    ),
                    SceneItem(
                        scene_id=2,
                        narration_text="Mais de vinte mil cidadãos caminhavam por fóruns monumentais de mármore, termas luxuosas e vilas decoradas com afrescos deslumbrantes, completamente alheios à bomba geológica que a montanha sagrada escondia.",
                        start_time=10.0,
                        end_time=20.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="Ancient Roman frescos in Pompeii art",
                            camera_motion="drift_left"
                        ),
                        sfx=[SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)]
                    ),
                    SceneItem(
                        scene_id=3,
                        narration_text="Nas primeiras horas daquele dia fatídico, a terra tremeu violentamente. Uma coluna colossal de pedra-pomes, cinzas e gases incandescentes foi ejetada a mais de trinta quilômetros de altura em direção à estratosfera.",
                        start_time=20.0,
                        end_time=30.0,
                        visual_type=VisualTypeEnum.PARALLAX_25D,
                        visual_config=SceneVisualConfig(
                            search_query="Eruption of Vesuvius classical painting",
                            camera_motion="push_in"
                        ),
                        sfx=[SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)]
                    ),
                    SceneItem(
                        scene_id=4,
                        narration_text="O meio-dia transformou-se em trevas absolutas. Nuvens piroclásticas a centenas de quilômetros por hora e mais de trezentos graus varreram as ruas romanas, selando o destino da cidade em poucos segundos.",
                        start_time=30.0,
                        end_time=40.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="Karl Briullov The Last Day of Pompeii painting",
                            camera_motion="push_in"
                        ),
                        sfx=[SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)]
                    ),
                    SceneItem(
                        scene_id=5,
                        narration_text="Sob uma camada de mais de seis metros de cinzas vulcânicas compactas, Pompeia desapareceu completamente dos mapas, permanecendo intocada e esquecida pelo mundo por quase mil e setecentos anos.",
                        start_time=40.0,
                        end_time=50.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="Pompeii archaeological excavation ruins landscape",
                            camera_motion="drift_left"
                        ),
                        sfx=[SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)]
                    ),
                    SceneItem(
                        scene_id=6,
                        narration_text="Hoje, as escavações arqueológicas revelam os detalhes mais íntimos desse império perdido, servindo como uma das mais fascinantes e comoventes cápsulas do tempo de toda a humanidade.",
                        start_time=50.0,
                        end_time=60.0,
                        visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                        visual_config=SceneVisualConfig(
                            search_query="House of the Vettii Pompeii fresco wall painting",
                            camera_motion="push_in"
                        ),
                        sfx=[SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)]
                    )
                ]
        else:
            scenes = [
                SceneItem(
                    scene_id=1,
                    narration_text=f"Por trás dos registros oficiais sobre {clean_topic}, escondem-se detalhes cruciais que desafiam a versão convencional dos fatos.",
                    start_time=0.0,
                    end_time=10.0,
                    visual_type=VisualTypeEnum.REMOTION_GRAPHIC,
                    visual_config=SceneVisualConfig(
                        template="NewspaperHighlight",
                        props={
                            "headline": f"REVELAÇÃO: O CASO DE {clean_topic.upper()}",
                            "source_label": "Arquivo Investigativo - Edição Especial",
                            "highlight_words": clean_topic.upper(),
                            "date_label": "Dossiê Exclusivo"
                        }
                    ),
                    sfx=[SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)]
                ),
                SceneItem(
                    scene_id=2,
                    narration_text=f"Documentos antes confidenciais revelam que os primeiros sinais de alerta foram sistematicamente ignorados pelas lideranças envolvidas.",
                    start_time=10.0,
                    end_time=20.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query=f"{clean_topic} investigation historical archive",
                        camera_motion="drift_left"
                    ),
                    sfx=[SFXEvent(name="whoosh_deep.wav", offset_sec=0.0)]
                ),
                SceneItem(
                    scene_id=3,
                    narration_text=f"Hoje, o caso permanece como um dos episódios mais estudados e emblemáticos de toda a história contemporânea.",
                    start_time=20.0,
                    end_time=30.0,
                    visual_type=VisualTypeEnum.HISTORIC_MEDIA,
                    visual_config=SceneVisualConfig(
                        search_query=f"{clean_topic} impact aftermath history",
                        camera_motion="push_in"
                    ),
                    sfx=[SFXEvent(name="sub_bass_hit.wav", offset_sec=0.0)]
                )
            ]

        manifest = ProjectManifest(
            project_id=project_id,
            title=title or f"Documentário: {clean_topic}",
            scenes=scenes
        )
        manifest.stage_status.stage1_director = StageStatusEnum.COMPLETED
        return manifest
