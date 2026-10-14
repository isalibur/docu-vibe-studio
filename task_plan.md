# Task Plan: Fábrica Modular de Documentários com IA (Protocolo Guardião v3.0)

> **Status:** Em Planejamento Aprovado / Pronto para Execução  
> **Workspace:** `D:\IA\editor_inteligente`  
> **Hardware:** AMD Ryzen 5 5500 | 24 GB RAM | NVIDIA RTX 3060 (12 GB VRAM)  
> **Documento Guardião Oficial:** [GUARDIAN_EXECUTION_PLAN.md](file:///d:/IA/editor_inteligente/GUARDIAN_EXECUTION_PLAN.md)  
> **Metodologia:** Planning with Files (`task_plan.md`, `findings.md`, `progress.md`)

---

## 🎯 Meta Geral
Transformar o pipeline de vídeo em uma **esteira de produção cinematográfica automatizada e modular**, eliminando atalhos amadores, voz genérica acelerada, legendas dessincronizadas e mídias desconexas:
1. **Inteligência Contextual via 9router (`http://localhost:20128/v1`):** Usar o modelo `arsenal` para decupagem cirúrgica de roteiro e *Shot List*.
2. **Voz Local de Qualidade / Clonagem:** Integrar a síntese local de `D:\IA\audio_factory` (F5-TTS / Kokoro / Clonagem local) com ritmo pausado de documentário.
3. **Legendas Sintáticas:** Agrupamento por pontuação gramatical e pausas (nunca por blocos fixos de 4 palavras), eliminando cortes de orações no meio da tela.
4. **Visual Híbrido Dosado:** Mesclar obras de arte históricas reais em alta resolução, imagens conceituais locais e animações dinâmicas do Remotion (manchetes em perspectiva 3D, cartões de gráficos).
5. **Duração Parametrizada:** Suporte explícito a durações de 30s (teste ágil) ou 60s (completo).

---

## 📋 Fases Sequenciais de Execução (Quality Gate Checklist)

### Fase 1: Integração do 9router (`http://localhost:20128/v1`)
- [ ] Atualizar `src/stage1_director/script_director.py` para chamar o endpoint `http://localhost:20128/v1/chat/completions` com a chave do 9router (`sk-4c637809...`) e modelo `arsenal`.
- [ ] Implementar prompt rigoroso de *Shot List* contextual e schema JSON estrito.
- [ ] **Gating Test 1:** Gerar roteiro para teste de 30s e validar consistência semântica e formato JSON.
- [ ] **Atualizar Guardião:** Registrar métricas e status no `GUARDIAN_EXECUTION_PLAN.md`.

### Fase 2: Motor de Narração Local (F5-TTS / Kokoro em `audio_factory`)
- [ ] Criar ponte em `src/stage2_audio/local_voice_engine.py` aproveitando o venv de `D:\IA\audio_factory`.
- [ ] Configurar voz de referência (`minha_voz_referencia.wav` ou `locutor_principal.wav`) e síntese com cadência pausada (~125-135 wpm).
- [ ] **Gating Test 2:** Sintetizar áudio de teste de 30s e validar tom humano, ausência de aceleração e clareza acústica.
- [ ] **Atualizar Guardião:** Registrar métricas e status no `GUARDIAN_EXECUTION_PLAN.md`.

### Fase 3: Legendas com Agrupamento Sintático
- [ ] Refatorar `src/stage3_captions/ass_generator.py` para agrupar por cláusulas e pontuação (`.`, `,`, `?`, `!`), abolindo o bloco fixo de 4 palavras.
- [ ] Validar sincronização com `Faster-Whisper` guiado pelo roteiro original.
- [ ] **Gating Test 3:** Verificar arquivo `.ass` e garantir que nenhuma frase termine cortada no meio de um bloco na tela.
- [ ] **Atualizar Guardião:** Registrar métricas e status no `GUARDIAN_EXECUTION_PLAN.md`.

### Fase 4: Diretor Visual Híbrido e Templates Remotion
- [ ] Conectar os templates `DocumentaryParallax.tsx`, `NewspaperHighlight.tsx` e `DataChartCard.tsx` no fluxo do orquestrador `main.py`.
- [ ] Curadoria de obras históricas no `wikimedia_fetcher.py` + fallback de imagem conceitual local via ComfyUI.
- [ ] **Gating Test 4:** Renderizar 1 cena de cada tipo e verificar fluidez e ausência de jitter.
- [ ] **Atualizar Guardião:** Registrar métricas e status no `GUARDIAN_EXECUTION_PLAN.md`.

### Fase 5: Controle de Duração e Interface Web
- [ ] Implementar seletor de duração (`30s` / `60s`) no CLI (`--duration`) e na UI (`src/ui/static/index.html`).
- [ ] Sincronizar o cálculo de frames e cortes no `main.py`.
- [ ] **Gating Test 5:** Gerar projeto de 30s e comprovar duração exata via ffprobe.
- [ ] **Atualizar Guardião:** Registrar métricas e status no `GUARDIAN_EXECUTION_PLAN.md`.

### Fase 6: Teste de Bancada Completo (Vídeo Master 30s) e Auditoria
- [ ] Produção ponta a ponta do documentário de 30s sobre *"O Vesúvio de Pompeia"*.
- [ ] Validação de áudio, vídeo, legendas, dosagem gráfica e sincronia.
- [ ] Atualização final do `GUARDIAN_EXECUTION_PLAN.md`, commit no git e submissão à revisão.
