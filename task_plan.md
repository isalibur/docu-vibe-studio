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
- [x] Implementar `src/stage1_director/script_director.py` com LiteLLM (Gemini 2.5 Flash / Groq) e fallback estruturado
- [x] Implementar prompt de Persona "Diretor de Cinema" gerando schema estrito de cenas
- [x] Implementar `src/stage2_audio/tts_engine.py` (Edge-TTS grátis, 48kHz broadcast, zero VRAM)
- [x] Implementar `src/stage2_audio/silence_cutter.py` integrando `auto-editor` para corte de tempos mortos (>0.35s)
- [x] **Gating Test:** Teste de geração de roteiro estruturado e síntese de áudio de alta qualidade concluído com sucesso.

### Fase 3: Sincronia Fonética e Legendas Dinâmicas (Estágio 3)
- [x] Implementar `src/stage3_captions/aligner.py` com Faster-Whisper / WhisperX e liberação obrigatória de VRAM (`flush_vram`)
- [x] Implementar `src/stage3_captions/ass_generator.py` gerando legendas `.ass` com destaque cinético e escala em ciano
- [x] **Gating Test:** Alinhamento de áudio demo e compilação de arquivo `.ass` com eventos sincronizados por palavra validado com 100% de sucesso.

### Fase 4: Mídia Híbrida e Parallax 2.5D (Estágio 4)
- [x] Implementar `src/stage4_broll/pexels_fetcher.py` e fallback Pixabay com geração suave de clipe
- [x] Implementar `src/stage4_broll/wikimedia_fetcher.py` para mídias históricas/documentais de domínio público
- [x] Implementar `src/stage4_broll/parallax_segmenter.py` com RMBG via `rembg` (separação sujeito/fundo)
- [x] **Gating Test:** Download/geração de B-roll e separação das camadas FG transparente e BG com blur concluídos com sucesso.

### Fase 5: Templates Cinematográficos no Remotion (Estágio 5)
- [x] Desenvolver `DocumentaryParallax.tsx` (câmera contínua 2.5D com sub-pixel float - Anti-Zoompan)
- [x] Desenvolver `NewspaperHighlight.tsx` (manchete 3D com caneta marca-texto animada)
- [x] Desenvolver `DataChartCard.tsx` (gráficos estatísticos estilo Vox)
- [x] Registrar templates no `src/index.tsx` do Remotion com tipagens estritas
- [x] Implementar `src/stage5_motion/remotion_bridge.py` para disparar renders CLI via manifesto
- [x] **Gating Test:** Renderização headless do template `DataChartCard` via Remotion CLI validada em 232 KB com 100% de sucesso.

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
