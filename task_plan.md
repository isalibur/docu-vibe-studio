# Task Plan: Estúdio Inteligente de Documentários (Remotion + IA)

> **Status do Projeto:** Ativo  
> **Workspace:** `D:\IA\editor_inteligente`  
> **Hardware Alvo:** AMD Ryzen 5 5500 | 24 GB RAM | NVIDIA RTX 3060 (12 GB VRAM)  
> **Metodologia:** Planning with Files (`task_plan.md`, `findings.md`, `progress.md`)

---

## 🎯 Meta Geral
Construir um estúdio automatizado em Python + Remotion (React/TypeScript) que transforma um tema ou roteiro em documentários cinematográficos dinâmicos (estilo *Vox*, *Johnny Harris*, *Fern*, *Magnates*), com sincronia fonética milissegundo, gráficos animados, efeitos sonoros (SFX), B-rolls contextuais e efeito Parallax 2.5D, respeitando estritamente os 12 GB de VRAM da máquina e a **proibição estrita do `zoompan` do FFmpeg**.

---

## 📋 Fases de Desenvolvimento

### Fase 1: Fundação do Ambiente, Manifesto e Core Guardrails
- [x] Criar estrutura oficial de diretórios (`src/core/`, `src/stage1_...` a `stage6_...`, `assets/`, `remotion_graphics/`, `workspace/`)
- [x] Configurar `config.yaml` calibrado para o hardware e `.env.example`
- [x] Criar `requirements.txt` com versões pinadas e compatíveis com PyTorch CUDA
- [x] Implementar `src/core/manifest.py` com modelos Pydantic v2 para o `project_manifest.json`
- [x] Implementar `src/core/vram_guard.py` (rotinas de limpeza CUDA, gc, unload Ollama e ComfyUI)
- [x] Inicializar o projeto `remotion_graphics/` (TypeScript, React, Remotion CLI configurado e testado)
- [x] **Gating Test:** Validação dos schemas Pydantic, teste unitário do `vram_guard.py` e renderização headless de teste no Remotion concluídos com 100% de sucesso.

### Fase 2: Roteiro, Narração e Ritmo (Estágios 1 e 2)
- [ ] Implementar `src/stage1_director/script_director.py` com LiteLLM (Gemini 2.5 Flash / Groq) e fallback Ollama
- [ ] Implementar prompt de Persona "Diretor de Cinema" gerando schema estrito de cenas
- [ ] Implementar `src/stage2_audio/tts_engine.py` (Edge-TTS grátis / Chatterbox local)
- [ ] Implementar `src/stage2_audio/silence_cutter.py` integrando `auto-editor` para corte de tempos mortos (>0.35s)
- [ ] **Gating Test:** Teste de geração de áudio de uma cena demo com remoção de pausas e verificação de VRAM limpa

### Fase 3: Sincronia Fonética e Legendas Dinâmicas (Estágio 3)
- [ ] Implementar `src/stage3_captions/aligner.py` com WhisperX (`int8_float16`) + alinhamento Wav2Vec2
- [ ] Implementar `src/stage3_captions/ass_generator.py` gerando legendas `.ass` com destaque cinético de palavras
- [ ] **Gating Test:** Alinhamento de áudio demo e inspeção do arquivo `.ass` com tags de zoom/cor

### Fase 4: Mídia Híbrida e Parallax 2.5D (Estágio 4)
- [ ] Implementar `src/stage4_broll/pexels_fetcher.py` e fallback Pixabay
- [ ] Implementar `src/stage4_broll/wikimedia_fetcher.py` para mídias históricas/documentais
- [ ] Implementar `src/stage4_broll/comfy_client.py` para geração de ilustrações conceituais FLUX GGUF
- [ ] Implementar `src/stage4_broll/parallax_segmenter.py` com RMBG-2.0 via `rembg` (separação sujeito/fundo)
- [ ] **Gating Test:** Download de B-roll demo e recorte transparente de imagem

### Fase 5: Templates Cinematográficos no Remotion (Estágio 5)
- [ ] Desenvolver `DocumentaryParallax.tsx` (câmera contínua 2.5D com sub-pixel float - Anti-Zoompan)
- [ ] Desenvolver `NewspaperHighlight.tsx` (manchete 3D com caneta marca-texto animada)
- [ ] Desenvolver `DataChartCard.tsx` (gráficos estatísticos Vox)
- [ ] Desenvolver `MapZoomScene.tsx` (mapas vetoriais SVG)
- [ ] Desenvolver `TimelineEvent.tsx` e `LowerThirdTitle.tsx`
- [ ] Implementar `src/stage5_motion/remotion_bridge.py` para disparar renders CLI via manifesto
- [ ] **Gating Test:** Renderização headless de cada componente via Remotion CLI em MP4

### Fase 6: Montagem Final NVENC, Ducking e CLI Mestre (Estágio 6)
- [ ] Implementar `src/stage6_assembler/ffmpeg_composer.py` (mixagem de áudio com sidechain ducking, inserção de SFX, queima de legendas `.ass` e renderização NVENC)
- [ ] Implementar `src/stage6_assembler/otio_exporter.py` (timeline OpenTimelineIO / Kdenlive)
- [ ] Implementar `main.py` com CLI unificada (`--topic`, `--stage`, `--resume`)
- [ ] **Gating Test:** Renderização ponta a ponta de um documentário piloto de 1 minuto

---

## 🛑 Guardrails & Regras de Ouro
1. **Zero Zoompan do FFmpeg:** Movimentos de imagem apenas no Remotion.
2. **Zero Vídeo IA Pesado (LTX/Wan):** Somente imagens estáticas FLUX + Parallax 2.5D + B-rolls reais.
3. **Isolamento de Memória:** Chamar `flush_vram()` obrigatoriamente ao final de cada estágio.
4. **Respeito ao Hardware:** Máximo de 8 threads no Ryzen 5 5500 e limites seguros na RTX 3060.
