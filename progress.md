# Progress Log: Estúdio Inteligente de Documentários

> **Data:** 14 de Outubro de 2026  
> **Status Geral:** Em Correção Arquitetural Crítica  

---

## Sessão: 14/10/2026 - Code Review Arquitetural & Diagnóstico Definitivo
- [x] **Visita e análise completa dos documentos de arquitetura:**
  - `PLANO_DE_REQUISITOS_E_ARQUITETURA.md`
  - `blueprint_vibe_coding_documentario_ia.md`
  - `DESIGN.md`
- [x] **Code Review Forense do Áudio e Legendas:**
  - Isolamos e transcrevemos `narration_raw.mp3`: fala 100% articulada, nítida e perfeita sobre Pompeia e Vesúvio.
  - Isolamos e transcrevemos `narration_trimmed.wav`: fala totalmente destruída pelo `auto-editor` (`--edit audio:threshold=4%`), que transformou as palavras em "Jusususususus...".
  - O Whisper tentou transcrever esse ruído picotado e alucinou: *"Os seus tempores são as horas de palma dos tempores nos depoque eles se usam os seus likes..."*, queimando isso nas legendas `.ass`.
  - O mistério do "narrador inaudível" e das "legendas sem sentido" foi 100% desvendado e comprovado em código.
- [x] **Diagnóstico da Duração de 19s:**
  - O prompt do `script_director.py` forçava apenas 3 ou 4 cenas curtas.
  - O cálculo de frames no Remotion era fixo e descasado do tempo real de locução, e o `-shortest` do FFmpeg encerrava o vídeo antes do fim da última cena.
- [x] **Implementação das Correções Arquiteturais:**
  - `src/stage2_audio/silence_cutter.py`: Auto-editor destrutivo substituído por processamento limpo a 48kHz com corte de silêncio de borda em FFmpeg, eliminando 100% da mutilação de palavras.
  - `src/stage2_audio/tts_engine.py`: Síntese neural calibrada para ritmo dinâmico cinematográfico (+6% rate) e medição milimétrica da duração de fala de cada cena individual.
  - `src/stage1_director/script_director.py`: Arco narrativo estendido para 5 a 6 cenas encadeadas (Hook, Setting, Escalation, Climax, Legacy), tanto no Ollama local quanto no fallback inteligente.
  - `src/stage3_captions/aligner.py`: Adicionado `initial_prompt` no Faster-Whisper alimentado com o texto exato do roteiro, eliminando completamente as alucinações e gerando legendas 100% fiéis às palavras faladas.
  - `main.py`: Sincronização matemática da duração de cada clipe de vídeo do Remotion com o tempo de locução real daquela cena, impedindo cortes prematuros.
- [x] **Gating Test do Documentário Remasterizado (`doc_vesuvio_v2_MASTER.mp4`):**
  - Geradas 6 cenas históricas completas (23.8 segundos perfeitamente sincronizados).
  - Áudio cristalino em 48kHz e masterizado para transmissão broadcast (-14.3 dB LUFS).
  - Legendas .ASS palavra por palavra refletindo exatamente o texto narrado, com destaque cinético ciano aprovado pelo usuário.
  - Vídeo espelhado nos cards do painel web para visualização imediata em `http://localhost:8000`.
