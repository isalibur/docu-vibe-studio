# GUARDIAN_EXECUTION_PLAN.md — Protocolo Guardião de Engenharia e Qualidade
> **Projeto:** Docu-Vibe Studio (`D:\IA\editor_inteligente`)  
> **Versão do Protocolo:** 3.0 (Fábrica de Produção Modular de Alta Fidelidade)  
> **Data de Criação:** 14 de Outubro de 2026  
> **Ambiente de Hardware:** AMD Ryzen 5 5500 (6c/12t) | 24 GB RAM DDR4 | NVIDIA GeForce RTX 3060 (12 GB VRAM)  
> **Regra Mandatória de Operação:** Este documento é o **Guardião do Processo**. Antes de iniciar qualquer fase, o agente deve obrigatoriamente ler este plano; após a execução e teste de bancada de cada fase, deve atualizar seu status, registrar métricas reais e coletar o checklist. Nenhuma fase é pulada. Nenhum atalho é tolerado.

---

## 1. Visão Geral e Princípios Fundamentais

O objetivo deste projeto não é criar um "slideshow automatizado com voz robótica", mas sim uma **esteira de produção cinematográfica automatizada** capaz de gerar documentários investigativos densos, dinâmicos e envolventes (estilo *Vox*, *Johnny Harris*, *Lemmino*, *Magnates*), com elementos visuais dosados, sincronia cirúrgica e áudio profissional.

### Os 5 Pilares de Qualidade Inegociáveis:
1. **Inteligência Contextual Real:** O roteiro e a decupagem de cenas (*Shot List*) são orquestrados por LLM de fronteira via **9router local (`http://localhost:20128/v1`)** utilizando o endpoint OpenAI-compatible e modelos de alta capacidade semântica (`arsenal` / `gpt-oss:120b` / `gemini-3.8-flash`), eliminando alucinações e descasamento entre o que se fala e o que se vê.
2. **Voz Local Profissional e Cadenciada:** Substituição de vozes genéricas de TTS de nuvem aceleradas por **síntese local de alta fidelidade** (`F5-TTS` / `Kokoro` / clonagem da voz de referência já existente em `D:\IA\audio_factory`), com ritmo pausado, dramático e cinematográfico (~2.2 a 2.4 palavras por segundo com respiração).
3. **Legendas com Alinhamento Sintático Natural:** Eliminação do agrupamento cego de "4 palavras por bloco". As legendas são agrupadas estritamente por **cláusulas gramaticais, vírgulas e pontos finais**, garantindo que frases nunca sejam cortadas no meio e que a leitura acompanhe a fala com naturalidade absoluta.
4. **Mídia Híbrida Dosada e Contextual:** Nenhuma cena é genérica. O sistema combina:
   * **Obras de arte e fotos históricas reais** em alta resolução (Wikimedia Commons filtrada).
   * **Imagens contextuais geradas localmente** via ComfyUI (`D:\IA\ComfyUI`).
   * **Animações programáticas Remotion** dosadas (manchetes em perspectiva 3D com marca-texto animado, cards de gráficos e dados, cortes 2.5D com recorte RMBG).
5. **Duração Determinística:** O usuário escolhe o tema e a duração alvo (ex: 30s para validação rápida ou 60s para documentário completo). O diretor calcula exatamente a densidade textual e o número de cenas para preencher o tempo com precisão matemática.

---

## 2. Mapa do Ecossistema Técnico Local

| Componente | Localização / Porta | Especificação | Status Inicial |
| :--- | :--- | :--- | :--- |
| **LLM Router (9router)** | `http://localhost:20128/v1` | Auth: Bearer `sk-4c637809...` \| Modelo: `arsenal` | ✅ Verificado e respondendo |
| **Voz Local / Clonagem** | `D:\IA\audio_factory` | Venv com `f5-tts 1.1.22`, `kokoro 0.9.4`, PyTorch CUDA 12.4 | ✅ Modelos e pesos baixados |
| **Áudios de Referência** | `D:\IA\audio_factory\voices` | `minha_voz_referencia.wav` (24s) e `locutor_principal.wav` | ✅ Disponíveis |
| **Geração de Imagens** | `D:\IA\ComfyUI` | Instalação local com modelos SD/FLUX para cenas conceituais | ✅ Presente no disco |
| **Motion Engine** | `D:\IA\editor_inteligente\remotion_graphics` | React + Remotion CLI (Anti-Jitter sub-pixel interpolation) | ✅ Instalado |
| **Assembler Final** | FFmpeg NVENC RTX 3060 | Masterização 1080p30, Sidechain ducking e burn-in .ASS | ✅ Calibrado |

---

## 3. Matriz de Fases de Execução e Quality Gates

```
[Fase 1: Diretor 9router] ➔ [Fase 2: Motor de Voz Local] ➔ [Fase 3: Legendas Sintáticas]
                                                                    │
[Fase 6: Master & Gating 30s]  [Fase 5: Controle Duração]  [Fase 4: Visual Híbrido Dosado]
```

---

### FASE 1: Conexão e Decupagem Contextual via 9router
* **Objetivo:** Conectar o `ScriptDirector` ao 9router (`http://localhost:20128/v1`), passando prompt cinematográfico rigoroso que decomponha o tema em roteiro investigativo e *Shot List* visual hiper-específica.
* **Tarefas de Engenharia:**
  1. Configurar cliente OpenAI em `src/stage1_director/script_director.py` apontando para `http://localhost:20128/v1` com a chave do 9router.
  2. Implementar schema JSON estrito de cena que obrigue o modelo a definir:
     * `narration_text`: Texto rico e detalhado em português com cadência cinematográfica.
     * `visual_category`: `historic_art` | `local_generated` | `motion_graphic` | `document_headline`.
     * `visual_prompt_or_query`: Termo de busca em inglês altamente específico para obras reais ou prompt para geração de imagem.
     * `motion_type`: `parallax_push`, `drift_left`, `headline_reveal`, `chart_flow`.
  3. Suportar escolha de duração (ex: 30s = 3 cenas de 20-25 palavras; 60s = 6 cenas de 25-35 palavras).
* **Quality Gate (Critério de Aceite):**
  - Execução de script de teste gerando JSON completo sem erros 401/503.
  - As queries de busca devem citar nomes de pinturas, fóruns romanos, autores ou eventos históricos concretos, com zero termos genéricos como "ancient rome".

---

### FASE 2: Motor de Narração Local de Alta Fidelidade (F5-TTS / Kokoro & Banco Multi-Vozes)
* **Objetivo:** Eliminar a voz genérica acelerada e implementar síntese local humanizada, com suporte a **múltiplos perfis de voz clonada** e presets temáticos, com pausas respiratórias e ritmo autêntico de documentário.
* **Tarefas de Engenharia:**
  1. Criar `src/stage2_audio/local_voice_engine.py` integrando com o ambiente `D:\IA\audio_factory\.venv`.
  2. Implementar **Banco Dinâmico de Perfis de Voz (Voice Bank)**:
     * O sistema deve escanear pastas de vozes (`assets/voices/` e `D:\IA\audio_factory\voices/`).
     * Suporte para adicionar novas referências de áudio (`.wav`) pelo usuário a qualquer momento para combinar com diferentes temas (ex: narrador épico, investigativo, reflexivo, histórico).
     * Descoberta automática de perfis com fallback inteligente para presets de alta qualidade.
  3. Suportar os modos locais de alta fidelidade:
     * **Modo A (Clonagem Zero-Shot F5-TTS):** Utiliza os checkpoints de `D:\IA\audio_factory\models\voice_clone\models--SWivid--F5-TTS` e a referência selecionada do perfil.
     * **Modo B (Kokoro TTS Local):** Síntese ultra-rápida e expressiva de alta fidelidade rodando em PyTorch local.
     * **Fallback Seguro (Edge-TTS Humanizado):** Taxa negativa (`rate="-2%"` ou `"-4%"` com pitch profundo) caso a GPU esteja reservada para geração de imagem.
  4. Garantir inserção de silêncios naturais de respiração (0.4s a 0.6s) entre frases e pontos finais.
* **Quality Gate (Critério de Aceite):**
  - O sistema descobre dinamicamente os perfis de voz disponíveis na pasta.
  - O áudio gerado deve soar humano, com cadência pausada (nunca acelerada) e zero artefatos de corte de consoantes.
  - Medição de taxa de fala entre 120 e 140 palavras por minuto.

---

### FASE 3: Reformulação das Legendas (Tipografia Cinematográfica & Tempo de Leitura Natural)
* **Objetivo:** Eliminar o efeito karaokê/TikTok e implementar legendas elegantes de documentário (estilo BBC/Netflix), com tipografia limpa, quebras sintáticas perfeitas e tempo de leitura natural.
* **Tarefas de Engenharia:**
  1. Refatorar completamente `src/stage3_captions/ass_generator.py`.
  2. Eliminar 100% dos efeitos de destaque palavra por palavra (karaokê pop) e tags `\fscx` / `\c` pulando na tela.
  3. Implementar **Agrupador Sintático e Tempo de Leitura Natural**:
     * Quebra de linhas estritamente por orações gramaticais e pontuação (`.`, `,`, `?`, `!`, `:`, `;`).
     * Exibição estática, limpa e legível de frases completas (1 a 2 linhas com no máximo 35 a 42 caracteres por linha).
     * Duração de tela calculada a partir do timestamp fonético inicial da primeira palavra até o término da última palavra da oração, garantindo tempo de permanência mínimo confortável para leitura humana.
  4. Selecionar e configurar a **Melhor Tipografia Cinematográfica de Documentário**:
     * Fonte sans-serif limpa e sofisticada (Montserrat / Inter / Trebuchet / Segoe UI Semibold).
     * Renderização elegante: cor branca pura (`&H00FFFFFF&`), contorno fino suave (`Outline=2`) e sombra difusa profunda para máxima legibilidade sobre qualquer imagem clara ou escura.
  5. Sincronização fonética com `Faster-Whisper` utilizando `initial_prompt` do roteiro original para fidelidade vocabular estrita.
* **Quality Gate (Critério de Aceite):**
  - O arquivo `.ass` gerado não contém tags de efeito karaokê.
  - Frases inteiras aparecem e permanecem na tela enquanto a locução ocorre, trocando suavemente apenas quando a oração termina.
  - Nenhuma legenda corta uma frase ao meio ou mistura o fim de uma oração com o início de outra.

---

### FASE 4: Diretor Visual Híbrido & Dosagem Dinâmica de Elementos
* **Objetivo:** O documentário deve alternar de forma orgânica entre obras históricas, gráficos e animações programáticas, evitando o tédio de um carrossel de fotos estáticas.
* **Tarefas de Engenharia:**
  1. Habilitar os templates Remotion já existentes no pipeline:
     * `DocumentaryParallax.tsx`: Movimento 2.5D com recorte RMBG para retratos e obras de arte.
     * `NewspaperHighlight.tsx`: Manchete de jornal ou documento histórico com marca-texto amarelo fluorescente animado.
     * `DataChartCard.tsx`: Cartão de dados estatísticos/cronológicos quando o roteiro citar números, anos ou comparações.
  2. Conectar o `wikimedia_fetcher.py` curado para mídias históricas reais de domínio público em 1080p horizontal.
  3. Estruturar a ponte com `D:\IA\ComfyUI` para cenas em que o roteiro exigir uma ilustração conceitual não encontrada em arquivos históricos.
* **Quality Gate (Critério de Aceite):**
  - O documentário master deve conter pelo menos 2 tipos visuais diferentes (ex: arte histórica + manchete/gráfico animado), dosados de acordo com o texto da cena.

---

### FASE 5: Controle Determinístico de Duração e Interface Web
* **Objetivo:** Permitir ao usuário definir se deseja um vídeo rápido de 30s (teste) ou 60s (completo), garantindo que o vídeo final termine exatamente na duração estipulada.
* **Tarefas de Engenharia:**
  1. Adicionar seletor de duração na interface web (`src/ui/static/index.html`) e argumento `--duration [30|60]` no `main.py`.
  2. Ajustar a geração do roteiro para calcular:
     * 30 segundos: 3 cenas, ~65 a 75 palavras no total.
     * 60 segundos: 6 cenas, ~135 a 150 palavras no total.
  3. Atualizar o orquestrador `main.py` para sincronizar os quadros do Remotion e a trilha sonora com sidechain ducking no tempo exato.
* **Quality Gate (Critério de Aceite):**
  - Vídeo de 30s deve ter duração medida pelo ffprobe entre 28.0s e 32.0s.
  - Vídeo de 60s deve ter duração medida pelo ffprobe entre 57.0s e 63.0s.

---

### FASE 6: Teste de Bancada Completo (Gating Test de 30s) e Auditoria
* **Objetivo:** Produzir um documentário de teste de 30 segundos para *"O Vesúvio de Pompeia"* cumprindo todos os critérios dos pilares de qualidade.
* **Tarefas de Engenharia:**
  1. Executar a esteira ponta a ponta: 9router -> Voz Local -> Legendas Sintáticas -> Visual Híbrido -> NVENC Master.
  2. Validar áudio, vídeo, legendas e coerência narrativa.
  3. Atualizar este documento com as métricas obtidas e submeter para revisão.

---

## 4. Registro de Execução e Checklist de Fases

| Fase | Descrição | Status | Data Início | Data Conclusão | Evidências / Artefatos |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fase 1** | Integração 9router (`localhost:20128`) | ✅ Concluída | 14/10/2026 20:49 | 14/10/2026 20:53 | Gating Test aprovado: 30s (3 cenas, 65 palavras) e 60s (6 cenas, 154 palavras). Conexão `arsenal` operacional. |
| **Fase 2** | Motor de Voz Local / F5-TTS / Kokoro & Voice Bank | ✅ Concluída | 14/10/2026 20:56 | 14/10/2026 21:02 | Gating Test aprovado: 8 perfis no Voice Bank. Clonagem GPU (6.82s) e narrador solene (6.41s) gerados a 48kHz. |
| **Fase 3** | Legendas Cinematográficas & Leitura Natural | ✅ Concluída | 14/10/2026 21:06 | 14/10/2026 21:08 | Gating Test aprovado: zero tags karaokê, agrupamento sintático por pontuação (. ,), Segoe UI e leitura natural. |
| **Fase 4** | Visual Híbrido e Templates Remotion | ⏳ Pendente | — | — | — |
| **Fase 5** | Duração Parametrizada (30s / 60s) | ⏳ Pendente | — | — | — |
| **Fase 6** | Teste de Bancada 30s & Auditoria | ⏳ Pendente | — | — | — |

---

## 5. Critérios de Avaliação para a IA de Revisão Externa

A IA de revisão externa pode verificar os seguintes pontos objetivos no código e no resultado final:
1. `src/stage1_director/script_director.py` chama `http://localhost:20128/v1/chat/completions` com autenticação válida e recebe modelo `arsenal`.
2. `src/stage2_audio/` contém motor de voz local funcional que gera áudio com cadência humana calibrada.
3. `src/stage3_captions/ass_generator.py` não contém divisão aritmética cega `words_per_block = 4`, e sim agrupamento por pontuação gramatical.
4. `src/stage6_assembler/ffmpeg_composer.py` realiza mixagem com sidechain ducking e normalização -14 LUFS.
5. O vídeo final possui coerência semântica estrita entre o tema, o roteiro e os elementos gráficos renderizados.
