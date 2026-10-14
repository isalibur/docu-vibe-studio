# Blueprint de Arquitetura e Guia de Vibe Coding: Estúdio Automatizado de Documentários Dinâmicos (Local AI + Free APIs)

Este documento é uma **Especificação Técnica e Guia de Direcionamento (PRD + Prompts de Vibe Coding)** projetado para ser entregue diretamente ao seu assistente de programação por IA (Cursor, Windsurf, Claude Code, Cline ou Aider). O objetivo é construir um pipeline modular em Python + TypeScript que transforma um tema ou roteiro em um documentário dinâmico completo (estilo *Vox*, *Johnny Harris* e *Lemmino*), com narração expressiva, corte de silêncio, B-rolls gerados por IA ou buscados em bancos gratuitos, animações gráficas de dados, legendas dinâmicas palavra por palavra e projeto exportável para edição fina.

## 1. Perfil de Hardware Alvo e Regras Rígidas de Memória (Guardrails para a IA)

Toda decisão de código gerada pela IA deve respeitar estritamente a máquina de execução local:

* **CPU:** AMD Ryzen 5 5500 (6 núcleos / 12 threads) — evitar codificação de vídeo pesada em CPU (`libx264` lento) e paralelismo excessivo de processos que travem o sistema.
* **RAM:** 24 GB DDR4 — usar como buffer seguro para *CPU offload* de pesos de modelos quantizados (`GGUF`) e compilação de quadros do Remotion.
* **GPU:** NVIDIA GeForce RTX 3060 com **12 GB de VRAM** (Arquitetura Ampere, suporte a CUDA, FP16, INT8 e encoder dedicado NVENC).

### As 4 Leis de Ouro que a IA Codificadora Deve Seguir

1. **Execução Estritamente Sequencial por Estágio (State-Machine Pipeline):** É proibido instanciar dois motores de IA na VRAM ao mesmo tempo. O pipeline deve operar em fases isoladas salvas em disco (`project_manifest.json`):
   * *Fase 1:* Roteiro e Cue Sheet (LLM) $\rightarrow$ Descarrega VRAM.
   * *Fase 2:* Narração (TTS) + Corte de Silêncio $\rightarrow$ Descarrega VRAM.
   * *Fase 3:* Alinhamento de Legendas (WhisperX) $\rightarrow$ Descarrega VRAM.
   * *Fase 4:* B-Rolls de Imagem e Vídeo (ComfyUI + Stock API) $\rightarrow$ Descarrega VRAM.
   * *Fase 5:* Renderização de Motion Graphics e Gráficos (Remotion / Motion Canvas).
   * *Fase 6:* Mixagem de Áudio, Composição Final (FFmpeg NVENC) e Exportação de Timeline (OpenTimelineIO / Kdenlive).
2. **Limpeza Forçada de VRAM Entre Etapas:** Todo módulo Python que carrega modelos PyTorch ou chama servidores locais deve executar um *teardown* explícito antes de encerrar:
   ```python
   import gc
   import torch
   import requests

   def flush_vram(ollama_url="http://localhost:11434", comfy_url="http://localhost:8188"):
       gc.collect()
       if torch.cuda.is_available():
           torch.cuda.empty_cache()
           torch.cuda.ipc_collect()
       # Força unload no ComfyUI se estiver rodando
       try:
           requests.post(f"{comfy_url}/free", json={"unload_models": True, "free_memory": True}, timeout=3)
       except Exception:
           pass
   ```
3. **Quantização Obrigatória para Modelos Grandes:** Modelos de imagem/vídeo (como Flux.1 ou Wan 2.1) devem usar pesos **GGUF (`Q4_K_M`, `Q5_K_M` ou `Q8_0`)** ou **FP8**, mantendo o pico de VRAM abaixo de **10.5 GB** para deixar margem ao sistema operacional.
4. **Renderização Acelerada por Hardware (NVENC):** Todo comando FFmpeg de exportação de vídeo deve usar o codificador de hardware da RTX 3060 (`-c:v h264_nvenc -preset p4 -rc vbr -cq 19`) em vez de sobrecarregar o Ryzen 5 5500.

## 2. As 2 Melhores Ferramentas Eleitas por Etapa

Para cada uma das 6 etapas do pipeline, foram eleitas **2 ferramentas complementares** (uma focada em qualidade/controle local na RTX 3060 de 12 GB e outra focada em velocidade, API gratuita ou complementaridade técnica).

| Etapa do Pipeline | Ferramenta Eleita #1 (Motor Principal) | Ferramenta Eleita #2 (Complemento / Fallback Grátis) | Por que essa dupla é a melhor para Vibe Coding na sua máquina? |
| :--- | :--- | :--- | :--- |
| **1. Roteiro e Direção Visual (JSON Cue Sheet)** | **[LiteLLM](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FBerriAI%2Flitellm)** | **[Ollama](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Follama%2Follama)** | O LiteLLM padroniza chamadas para APIs gratuitas (Gemini Flash/Pro Free Tier, Groq) com validação Pydantic JSON, enquanto o Ollama garante fallback 100% offline rodando Qwen 2.5 ou Llama 3.1 (8B/14B Q4) nos 12 GB de VRAM. |
| **2. Narração e Expressão Vocal (TTS)** | **[Chatterbox](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fresemble-ai%2Fchatterbox)** | **[edge-tts](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Frany2%2Fedge-tts)** | O Chatterbox (0.5B da Resemble AI) consome apenas ~3.5 GB de VRAM, clona vozes zero-shot e aceita tags dramáticas (`[pause]`, `[sigh]`). O `edge-tts` gera vozes neurais PT-BR gratuitas na nuvem com **0% de uso de GPU** para testes rápidos. |
| **3. Legendas Dinâmicas (Word-by-Word)** | **[WhisperX](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fm-bain%2Fwhisperx)** | **[Faster-Whisper](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSYSTRAN%2Ffaster-whisper)** | O Faster-Whisper transcreve em precisão `int8_float16` usando < 4 GB de VRAM, e o WhisperX aplica alinhamento fonético Wav2Vec2 para gerar *timestamps* exatos ao milissegundo por palavra. |
| **4. B-Rolls (Geração Visual IA + Stock Real)** | **[ComfyUI](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fcomfy-org%2Fcomfyui)** + **[ComfyUI-GGUF](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fcity96%2FComfyUI-GGUF)** | **[LTX-Video](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FLightricks%2Fltx-video)** / **[Wan2GP](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FDecentralised-AI%2FWan2GP)** (+ API Pexels estilo **[MoneyPrinterTurbo](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fharry0703%2FMoneyPrinterTurbo)**) | O ComfyUI em modo API headless gera imagens históricas/conceituais em Flux GGUF e as anima em vídeos de 5s com LTX-Video nos 12 GB de VRAM; já a API gratuita do Pexels fornece B-rolls reais sem custo de GPU. |
| **5. Animações e Gráficos de Documentário** | **[Remotion](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fremotion-dev%2Fremotion)** | **[Motion Canvas](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fmotion-canvas%2Fmotion-canvas)** | LLMs de Vibe Coding são excelentes escrevendo React/TypeScript/Tailwind no Remotion para criar mapas com zoom, linhas do tempo, *stat cards*, *lower thirds* e gráficos animados sincronizados por frame, enquanto o Motion Canvas brilha em diagramas vetoriais fluidos. |
| **6. Corte Dinâmico, Composição e Edição Final** | **[FFmpeg](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fffmpeg%2Fffmpeg)** + **[Auto-Editor](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fwyattblue%2Fauto-editor)** | **[OpenTimelineIO](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FAcademySoftwareFoundation%2FOpenTimelineIO)** + **[Kdenlive](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fkde%2Fkdenlive)** | O Auto-Editor elimina silêncios mortos da locução; o FFmpeg faz *audio ducking* e renderiza via NVENC; e o OpenTimelineIO gera a timeline aberta `.otio`/`.kdenlive` para ajustes manuais no Kdenlive. |

## 3. Arquitetura do Sistema e Estrutura de Diretórios

Peça para a IA estruturar o repositório exatamente neste formato modular:

```text
docu-vibe-studio/
├── .env.example                 # Chaves gratuitas (GEMINI_API_KEY, GROQ_API_KEY, PEXELS_API_KEY)
├── config.yaml                  # Parâmetros de hardware (NVENC, resoluções, caminhos do ComfyUI)
├── main.py                      # CLI Orquestrador com máquina de estados e retomada (checkpoint)
├── requirements.txt             # Dependências Python
├── src/
│   ├── core/
│   │   ├── manifest.py          # Modelos Pydantic do project_manifest.json
│   │   └── vram_guard.py        # Limpeza de CUDA, unload do Ollama e ComfyUI
│   ├── stage1_director/
│   │   └── script_director.py   # LiteLLM + Ollama: Gera roteiro e divide em cenas visuais
│   ├── stage2_audio/
│   │   ├── tts_engine.py        # Wrapper Chatterbox (local GPU) e edge-tts (cloud grátis)
│   │   └── silence_cutter.py    # Wrapper Auto-Editor para ritmo dinâmico de documentário
│   ├── stage3_captions/
│   │   ├── aligner.py           # WhisperX + Faster-Whisper (word-level timestamps)
│   │   └── ass_generator.py     # Gerador de legendas .ass com animação pop/highlight
│   ├── stage4_broll/
│   │   ├── pexels_fetcher.py    # Busca e download de vídeos HD gratuitos via API Pexels/Pixabay
│   │   └── comfy_client.py      # Cliente WebSocket/HTTP para ComfyUI (Flux GGUF + LTX-Video)
│   ├── stage5_motion/
│   │   └── remotion_bridge.py   # Passa JSON de dados para o Remotion e dispara renderização
│   └── stage6_assembler/
│       ├── ffmpeg_composer.py   # Mixagem de áudio (sidechain ducking), overlays e NVENC
│       └── otio_exporter.py     # Exporta timeline .otio / .kdenlive para edição manual
├── remotion_graphics/           # Projeto React/TypeScript (Remotion) para gráficos de documentário
│   ├── package.json
│   └── src/
│       ├── templates/
│       │   ├── MapZoomScene.tsx       # Mapa estilizado com pino, rota e zoom de câmera
│       │   ├── TimelineEvent.tsx      # Linha do tempo histórica com scroll horizontal
│       │   ├── DataChartCard.tsx      # Gráfico de barras/linhas animado estilo Vox
│       │   ├── NewspaperHighlight.tsx # Recorte de manchete com efeito marca-texto animado
│       │   └── LowerThirdTitle.tsx    # Identificação de personagem/local com barra cinética
└── workspace/                   # Pasta gerada por projeto (ex: workspace/doc_001/)
    ├── project_manifest.json    # Estado central do vídeo (Single Source of Truth)
    ├── audio/
    ├── brolls/
    ├── motion_renders/
    ├── captions/
    └── output/
```

## 4. O Contrato de Dados Central (`project_manifest.json`)

O segredo para que o código gerado por IA não quebre entre diferentes ferramentas é exigir que **todas as etapas leiam e escrevam neste único JSON validado por Pydantic**:

```json
{
  "project_id": "doc_crise_2008",
  "title": "O Efeito Dominó Invisível",
  "fps": 30,
  "resolution": {"width": 1920, "height": 1080},
  "audio_master": "workspace/doc_crise_2008/audio/narration_trimmed.wav",
  "captions_ass": "workspace/doc_crise_2008/captions/dynamic_words.ass",
  "bgm_track": "assets/bgm/dark_investigative_ambient.mp3",
  "scenes": [
    {
      "scene_id": 1,
      "narration_text": "[sigh] Em setembro de 2008, um único gráfico escondeu o colapso de trilhões de dólares.",
      "start_time": 0.0,
      "end_time": 6.4,
      "visual_type": "remotion_graphic",
      "visual_config": {
        "template": "DataChartCard",
        "props": {
          "headline": "Exposição Subprime Global (US$ Trilhões)",
          "source_label": "Fonte: Relatório da Comissão de Inquérito Financeiro",
          "data_points": [
            {"year": "2004", "value": 1.2},
            {"year": "2006", "value": 4.8},
            {"year": "2008", "value": 11.4}
          ],
          "theme": "vox_dark_grid"
        }
      },
      "sfx": "whoosh_deep.wav",
      "rendered_clip_path": "workspace/doc_crise_2008/motion_renders/scene_01.mp4"
    },
    {
      "scene_id": 2,
      "narration_text": "Nas ruas de Nova York, o pânico se espalhou antes da abertura das bolsas.",
      "start_time": 6.4,
      "end_time": 11.2,
      "visual_type": "ai_broll_video",
      "visual_config": {
        "source_preference": "comfyui_ltx",
        "fallback_stock_query": "Wall Street rain night financial district cinematic",
        "image_prompt": "Cinematic documentary photography, Wall Street financial district at dawn in heavy rain, 35mm lens, moody dark blue grading, photorealistic",
        "motion_prompt": "Slow dolly forward camera movement, rain falling, reflections on wet asphalt",
        "camera_effect": "ken_burns_zoom_in"
      },
      "sfx": "rain_thunder_subtle.wav",
      "rendered_clip_path": "workspace/doc_crise_2008/brolls/scene_02.mp4"
    }
  ]
}
```

## 5. Guia de Prompts para Vibe Coding (Passo a Passo)

> **Dica de Ouro para Vibe Coding:** Não peça para a IA programar as 6 etapas de uma só vez. Crie o arquivo `SPEC.md` na raiz do seu projeto com o conteúdo deste documento e envie os **6 Prompts Sequenciais** abaixo, testando um módulo por vez.

### Prompt 1: Fundação, Gerenciador de VRAM e Diretor de Roteiro (Etapa 1)

```text
Leia o arquivo SPEC.md na raiz do projeto. Vamos implementar a base do projeto e a Etapa 1:
1. Crie a estrutura de diretórios completa definida no SPEC.md, o requirements.txt e o arquivo src/core/manifest.py usando Pydantic v2 para validar e salvar/carregar o `project_manifest.json` com suporte a checkpoints (saber quais cenas já foram processadas).
2. Crie `src/core/vram_guard.py` para gerenciar minha RTX 3060 de 12GB VRAM e 24GB RAM: inclua funções para limpar cache CUDA (`torch.cuda.empty_cache()`), descarregar modelos do Ollama (`keep_alive=0`) e chamar o endpoint `/free` do ComfyUI.
3. Crie `src/stage1_director/script_director.py` usando `litellm` (com suporte a Gemini/Groq grátis via `.env` e fallback local para `ollama/qwen2.5:7b`). O módulo deve receber um tema ou texto bruto e gerar o `project_manifest.json` dividindo a narrativa em cenas de 4 a 8 segundos, alternando inteligentemente entre `visual_type`:
   - `remotion_graphic` (quando houver números, datas, mapas, citações de jornais ou linhas do tempo)
   - `ai_broll_video` (quando pedir atmosfera cinematográfica ou reconstituição histórica)
   - `stock_broll` (quando pedir cenas cotidianas ou urbanas via API do Pexels)
```

### Prompt 2: Motor de Narração Expressiva e Corte de Ritmo (Etapa 2)

```text
Seguindo o SPEC.md, vamos implementar a Etapa 2 (`src/stage2_audio/`):
1. Crie `tts_engine.py` com dois provedores selecionáveis no `config.yaml`:
   - Provedor A (Local GPU): Integração com `resemble-ai/chatterbox` rodando em FP16 na RTX 3060, suportando áudio de referência (`voice_clone_sample.wav`) e preservando tags paralinguísticas.
   - Provedor B (Zero-VRAM / Rápido): Integração assíncrona com `edge-tts` (ex: voz `pt-BR-AntonioNeural` ou `pt-BR-FranciscaNeural`) sem necessidade de API key.
2. Gere o áudio individual por cena E o áudio concatenado mestre.
3. Crie `silence_cutter.py` integrando o `auto-editor` via subprocesso CLI para remover pausas excessivas (> 0.35s) mantendo margem suave (`--margin 0.12sec`), atualizando os tempos `start_time` e `end_time` de cada cena no `project_manifest.json`.
4. Ao finalizar a etapa, chame obrigatoriamente `flush_vram()`.
```

### Prompt 3: Alinhamento Fonético e Legendas Dinâmicas `.ass` (Etapa 3)

```text
Seguindo o SPEC.md, vamos implementar a Etapa 3 (`src/stage3_captions/`):
1. Crie `aligner.py` usando `whisperx` com backend `faster-whisper` configurado especificamente para minha RTX 3060 12GB (`compute_type="int8_float16"`, `batch_size=16`). Carregue o áudio mestre, gere a transcrição, execute o modelo de alinhamento Wav2Vec2 para obter timestamps exatos por palavra (word-level) e chame `flush_vram()` imediatamente após salvar o JSON de palavras.
2. Crie `ass_generator.py` que converte o JSON word-level em um arquivo SubStation Alpha (`.ass`) estilizado para documentários:
   - Agrupe de 3 a 5 palavras por linha na parte inferior central (com margem segura).
   - Aplique tags de override `.ass` (`{\c&H00FFFF&\fscx110\fscy110}`) na palavra ativa que está sendo falada no momento exato, mantendo as demais palavras do bloco em branco com contorno escuro suave e sombra projetada.
   - Permita desativar a legenda automaticamente nos trechos em que `visual_type == "remotion_graphic"` do tipo `LowerThirdTitle` para não poluir a tela.
```

### Prompt 4: B-Rolls Híbridos — API Pexels + ComfyUI Local em 12 GB VRAM (Etapa 4)

```text
Seguindo o SPEC.md, vamos implementar a Etapa 4 (`src/stage4_broll/`):
1. Crie `pexels_fetcher.py`: busca vídeos gratuitos em Full HD na API do Pexels (com fallback na API do Pixabay) usando `fallback_stock_query` da cena, filtra vídeos horizontais (16:9) com duração mínima e faz o download para `workspace/<id>/brolls/`.
2. Crie `comfy_client.py`: cliente WebSocket/HTTP que se conecta ao ComfyUI local (`127.0.0.1:8188`).
   - Ele deve carregar um template de workflow JSON da pasta `comfy_workflows/`, injetar o `image_prompt` (usando Flux.1 Dev GGUF Q4_K_M via ComfyUI-GGUF) e, opcionalmente, passar a imagem gerada para um workflow Image-to-Video do `LTX-Video` (ou aplicar efeito de câmera 2.5D/Ken Burns fluido via filtro `zoompan` do FFmpeg em 60fps interpolado se o modo rápido estiver ativo).
   - Se o ComfyUI não estiver aberto ou falhar, faça fallback automático para o `pexels_fetcher.py`.
   - Ao terminar a fila de B-rolls, envie POST para `/free` no ComfyUI com `{"unload_models": true, "free_memory": true}`.
```

### Prompt 5: Gráficos e Animações Estilo Documentário com Remotion (Etapa 5)

```text
Seguindo o SPEC.md, vamos implementar a Etapa 5 (`remotion_graphics/` e `src/stage5_motion/remotion_bridge.py`):
1. Inicialize um projeto Remotion em TypeScript dentro de `remotion_graphics/` com estética de documentário investigativo moderno (fundo de textura de papel escuro/grid sutil, tipografia limpa estilo Inter/JetBrains Mono, animação física com `spring()` e `interpolate()`, vinheta suave e efeito de scanline/grão leve).
2. Crie 4 componentes reutilizáveis parametrizados via `inputProps` JSON:
   - `DataChartCard.tsx`: Gráfico de barras ou linha que cresce sincronizado com os frames, com título de impacto e fonte no rodapé.
   - `TimelineEvent.tsx`: Linha do tempo horizontal que desliza suavemente entre anos/eventos com destaque luminoso no evento atual.
   - `NewspaperHighlight.tsx`: Simulação de recorte de documento/jornal com câmera em leve perspectiva 3D e um marca-texto amarelo animando sobre a frase-chave da cena.
   - `MapZoomScene.tsx`: Mapa vetorial SVG com zoom suave de câmera até uma coordenada/país, pulso de radar e rótulo caligráfico.
3. Crie `src/stage5_motion/remotion_bridge.py` que lê todas as cenas com `visual_type == "remotion_graphic"` no `project_manifest.json` e executa `npx remotion render` passando as `props` da cena e a duração exata (`end_time - start_time`), salvando o `.mp4` em `workspace/<id>/motion_renders/`.
```

### Prompt 6: Montagem Final NVENC, Audio Ducking e Exportação para Kdenlive (Etapa 6)

```text
Seguindo o SPEC.md, vamos implementar a Etapa 6 (`src/stage6_assembler/`) e o `main.py`:
1. Crie `ffmpeg_composer.py`:
   - Normaliza todos os clipes de B-roll e animações do Remotion para 1920x1080 a 30fps (`sar=1:1`).
   - Aplica transições suaves e insere os efeitos sonoros (`sfx`) nos timestamps de mudança de cena.
   - Mixa a narração principal com a trilha sonora de fundo (`bgm_track`) aplicando filtro `sidechaincompress` (audio ducking automático: a música abaixa suavemente quando há voz e sobe nas pausas dramáticas).
   - Queima as legendas `.ass` dinâmicas e exporta o vídeo final usando aceleração de hardware da minha RTX 3060 (`-c:v h264_nvenc -preset p4 -rc vbr -cq 19 -pix_fmt yuv420p`).
2. Crie `otio_exporter.py` usando a biblioteca `opentimelineio` para gerar um arquivo `.otio` (e projeto compatível com o Kdenlive) contendo a faixa de narração, a faixa de B-rolls/Gráficos cortados e a faixa de BGM separadas, permitindo que eu abra o projeto no Kdenlive para ajustes manuais sem precisar re-renderizar tudo do zero.
3. Crie o `main.py` com argumentos CLI (`--topic`, `--resume-project`, `--stage`, `--fast-mode`) para rodar o pipeline completo ou apenas reexecutar uma etapa específica.
```

## 6. Recomendações de Configuração para Sua Máquina (`config.yaml` Sugerido)

Ao pedir para a IA gerar o `config.yaml`, utilize estes parâmetros calibrados para o conjunto **Ryzen 5 5500 + 24 GB RAM + RTX 3060 12 GB**:

```yaml
hardware:
  gpu_vram_gb: 12
  system_ram_gb: 24
  cpu_threads_limit: 8          # Deixa 4 threads livres no Ryzen 5 5500 para o SO não engasgar
  ffmpeg_encoder: "h264_nvenc"  # Usa o chip NVENC dedicado da RTX 3060
  ffmpeg_cq: 19

llm:
  primary_provider: "gemini/gemini-2.5-flash" # API Gratuita (rápida e zero VRAM)
  fallback_local_model: "ollama/qwen2.5:7b-instruct-q4_K_M"
  ollama_keep_alive: 0          # Descarrega da VRAM imediatamente após gerar o JSON

tts:
  engine: "chatterbox"          # Opções: "chatterbox" (local GPU) ou "edge-tts" (cloud grátis)
  device: "cuda"
  edge_voice_fallback: "pt-BR-AntonioNeural"

captions:
  whisper_model: "large-v3-turbo"
  compute_type: "int8_float16"  # Consome apenas ~3.2 GB de VRAM na RTX 3060
  batch_size: 16
  words_per_caption_block: 4

visuals:
  comfyui_url: "http://127.0.0.1:8188"
  flux_gguf_quant: "Q4_K_M"     # Roda confortavelmente com 12GB VRAM + 24GB RAM
  video_generator: "ltx_video"  # "ltx_video", "wan2gp" ou "ffmpeg_ken_burns" (modo rápido)
  remotion_concurrency: 4       # Ideal para 6 núcleos / 12 threads e 24GB RAM
```
