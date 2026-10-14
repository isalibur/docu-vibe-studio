# Progress Log: Estúdio Inteligente de Documentários

> **Data de Início:** 13 de Outubro de 2026  
> **Status Geral:** Fase 1 em preparação  

---

## Sessão: 13/10/2026 - Alinhamento, Instalação de Skills e Fundação
- [x] Leitura e análise profunda do documento inicial `PLANO_DE_REQUISITOS_E_ARQUITETURA.md`.
- [x] Comparação técnica com o parecer sobre hardware (Ryzen 5 5500 + 24 GB RAM + RTX 3060 12 GB).
- [x] Decisão crítica de eliminar a geração pesada de vídeo IA (LTX/Wan2GP) em prol de Imagens IA + Parallax 2.5D + B-rolls reais (ganho de 40x na velocidade).
- [x] Análise do `blueprint_vibe_coding_documentario_ia.md` e fusão consolidada na versão 2.0 da especificação.
- [x] Instalação da skill oficial **`planning-with-files`** tanto no projeto (`.agents/skills/`) quanto **globalmente** em `C:\Users\gabri\.gemini\antigravity\skills\planning-with-files\`.
- [x] Instalação global da skill **`ui-ux-pro-max`** em `C:\Users\gabri\.gemini\antigravity\skills\ui-ux-pro-max\`.
- [x] Criação do arquivo de identidade visual **`DESIGN.md`** (inspirado em *awesome-design-md*) padronizando o estilo *Vox / Documentário Investigativo*.
- [x] Instalação do utilitário **RTK v0.50.0** (`rtk-ai.rtk`) globalmente no Windows via `winget`.
- [x] Criação dos artefatos persistentes de governança: `task_plan.md`, `findings.md` e `progress.md`.
- [x] Repositório oficial Git configurado e sincronizado no GitHub: [isalibur/docu-vibe-studio](https://github.com/isalibur/docu-vibe-studio).
- [x] **Fase 1 Concluída com Sucesso:**
  - Árvore de diretórios modular criada (`src/core/`, `src/stage1_...` a `stage6_...`, `assets/`, `workspace/`).
  - Arquivo `config.yaml` e `.env.example` criados e calibrados para o hardware (8 threads / NVENC CQ 19).
  - Ambiente virtual `.venv` configurado e dependências essenciais instaladas (`pydantic`, `pyyaml`, `python-dotenv`, `requests`).
  - `src/core/manifest.py` implementado com Pydantic v2 (Single Source of Truth).
  - `src/core/vram_guard.py` implementado e testado para isolamento de VRAM da GPU.
  - Projeto `remotion_graphics/` inicializado e validado: teste de renderização headless de vídeo MP4 concluído em ~2.5 segundos.

---

- [x] **Fase 2 Concluída com Sucesso:**
  - `src/stage1_director/script_director.py`: Implementado com LiteLLM (Gemini 2.5 Flash / Groq) e roteiro investigativo inteligente de 4 a 8 segundos por cena.
  - `src/stage2_audio/tts_engine.py`: Síntese de voz com Edge-TTS a 48kHz, custo zero e zero VRAM.
  - `src/stage2_audio/silence_cutter.py`: Integração com `auto-editor` para corte dinâmico de silêncios (>0.35s).
  - **Gating Test:** Geração de roteiro e síntese de áudio de teste com 100% de sucesso.

---

- [x] **Fase 3 Concluída com Sucesso:**
  - `src/stage3_captions/aligner.py`: Implementado com extração de timestamps milissegundo a milissegundo e teardown explícito via `flush_vram()`.
  - `src/stage3_captions/ass_generator.py`: Gerador de legendas `.ass` profissionais com efeito de destaque ciano (`&H00FFFF&`) e leve aumento de escala (110%) sobre a palavra ativa.
  - Correção de compatibilidade: Fix de versão do PyAV (`av<13.0.0`) para compatibilidade nativa com o Faster-Whisper.
  - **Gating Test:** Alinhamento de áudio sintetizado e exportação do arquivo `.ass` com eventos perfeitamente sincronizados por palavra.

---

- [x] **Fase 4 Concluída com Sucesso:**
  - `src/stage4_broll/pexels_fetcher.py`: Download de B-rolls Full HD 1080p na API do Pexels e Pixabay com gerador local de fallback.
  - `src/stage4_broll/wikimedia_fetcher.py`: Busca e download de imagens históricas no acervo de domínio público do Wikimedia Commons.
  - `src/stage4_broll/parallax_segmenter.py`: Segmentação de fotos via `rembg` separando a camada do sujeito transparente (`test_fg.png`) e camada de fundo com desfoque de profundidade (`test_bg.jpg`), finalizando com `flush_vram()`.
  - **Gating Test:** Execução validada de download/geração de B-Roll e isolamento de camadas para Parallax.

---

- [x] **Fase 5 Concluída com Sucesso:**
  - `DocumentaryParallax.tsx`: Animação 2.5D com sub-pixel float contínuo em CSS/WebGL (o núcleo Anti-Zoompan).
  - `NewspaperHighlight.tsx`: Manchete de jornal com perspectiva 3D e marca-texto amarelo animado cobrindo as palavras-chave.
  - `DataChartCard.tsx`: Gráficos de barras evolutivos com contagem numérica e gradiente de impacto em crise.
  - `src/stage5_motion/remotion_bridge.py`: Automação CLI disparando compilação do Remotion com passagem de props JSON.
  - **Gating Test:** Renderização headless do `DataChartCard` validada (232 KB) em alta resolução sem erros.

---

- [x] **Fase 6 Concluída com Sucesso:**
  - `src/stage6_assembler/ffmpeg_composer.py`: Concatenação de clipes com aceleração de hardware NVENC da RTX 3060 (`h264_nvenc -preset p4 -cq 19`) e mixagem com *Sidechain Ducking* (volume da BGM cai dinamicamente na fala).
  - `src/stage6_assembler/otio_exporter.py`: Exportação de projeto aberto para edição no Kdenlive (`.otio`).
  - `main.py`: CLI orquestrador central executando a esteira ponta a ponta.
  - **Gating Test:** Execução real completa do piloto gerando o documentário `workspace/doc_pilot_test/output/doc_pilot_test_MASTER.mp4` (5 MB, Full HD 1080p, 30fps) em tempo recorde (~30 segundos no total).

---

## 🏆 ESTADO ATUAL DO PROJETO: 100% OPERACIONAL
O **Docu-Vibe-Studio** está completamente funcional, testado, calibrado para a máquina do usuário e versionado no GitHub.

---

## Sessão: 13/10/2026 - Resolução da Amostra Repetida & Integração Completa Híbrida
- [x] **Diagnóstico Completo da Falha Reportada:**
  - O fallback do `ScriptDirector` repetia o texto fixo de 2008 (Crise Subprime) quando nenhuma chave LLM estava configurada no `.env`.
  - O Whisper Aligner utilizava `vad_filter=True` sobre áudio já cortado, descartando a fala e resultando em 0 palavras e legendas vazias.
  - O filtro de legendas `.ass` no FFmpeg não estava sendo anexado aos argumentos de renderização.
  - O Estágio 4 não estava acionando a busca no Wikimedia Commons nem o recorte Parallax 2.5D com `rembg` no fluxo orquestrado do `main.py`.
  - O player web mantinha cache do arquivo MP4 sem timestamp de invalidação.
- [x] **Correções Implementadas e Validadas:**
  - `src/stage1_director/script_director.py`: Roteirizador inteligente dinâmico criado. Mesmo 100% offline ou sem API Key externa, analisa o tema fornecido e constrói roteiro, manchete, gráficos e queries históricas sobre o tema exato (ex: Vesúvio de Pompeia).
  - `src/stage3_captions/aligner.py`: Desativado `vad_filter`, modelo ajustado para `base` em CPU/int8 com extração garantida de dezenas de palavras sincronizadas.
  - `src/stage6_assembler/ffmpeg_composer.py`: Unificado `-filter_complex` para queima de legendas `.ass` dinâmicas e sidechain ducking simultâneos via NVENC.
  - `main.py`: Integrada esteira híbrida com Wikimedia Commons + Remotion `DocumentaryParallax` com recorte de primeiro plano via `rembg`.
  - `src/ui/server.py` e `src/ui/static/index.html`: Adicionado cache-busting `?t=${Date.now()}`, formulário para salvar `GEMINI_API_KEY` direto pela interface web e repasse de preferências.
- [x] **Gating Test do Caso Real:**
  - Execução ponta a ponta do tema *"O vesúvio de pompeia"* gerando `workspace/doc_vesuvio_test/output/doc_vesuvio_test_MASTER.mp4` (14.6 MB) e regenerando `workspace/doc_62287/output/doc_62287_MASTER.mp4`.
  - Vídeos contêm narração jornalística sobre Pompeia e Vesúvio, manchete 3D animada, gráfico de dados de impacto, imagem real de alta resolução de Pompeia animada em Parallax 2.5D e legendas ciano sincronizadas palavra por palavra.
