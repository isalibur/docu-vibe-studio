# Task Plan: Reestruturação Arquitetural e Correção Crítica do Pipeline (Docu-Vibe Studio)

> **Status do Projeto:** Em Correção Arquitetural Profunda  
> **Workspace:** `D:\IA\editor_inteligente`  
> **Hardware Alvo:** AMD Ryzen 5 5500 | 24 GB RAM | NVIDIA RTX 3060 (12 GB VRAM)  
> **Metodologia:** Planning with Files (`task_plan.md`, `findings.md`, `progress.md`)

---

## 🎯 Meta Geral
Resolver integralmente o feedback crítico do usuário:
1. Eliminar a corrupção de voz que gerava áudio inaudível e transcrições alucinadas ("Os seus tempores são as horas de palma...").
2. Reestruturar a sincronização entre áudio e vídeo por cena para evitar cortes prematuros de 19s e descasamento de ritmo.
3. Permitir roteiros substanciais e completos (com arco narrativo de documentário estilo Vox/Johnny Harris/Lemmino de 45s a 90s, configurável).
4. Corrigir o alinhamento de legendas para refletir com 100% de precisão as palavras reais do roteiro.
5. Garantir que a montagem mestre no FFmpeg mantenha áudio cristalino, BGM ducking perfeito e sincronia quadro a quadro.

---

## 📋 Fases de Desenvolvimento

### Fase 1: Diagnóstico e Code Review Arquitetural (Concluída)
- [x] Leitura completa de `PLANO_DE_REQUISITOS_E_ARQUITETURA.md` e `blueprint_vibe_coding_documentario_ia.md`.
- [x] Isolamento da causa raiz do áudio inaudível: o `auto-editor` com threshold agressivo cortava formantes/consoantes e gerava gagueira repetitiva ininteligível.
- [x] Isolamento da causa raiz das legendas sem sentido: o Whisper recebia o áudio mutilado pelo `auto-editor` e alucinava fonemas inexistentes.
- [x] Isolamento da causa raiz da duração reduzida (19s): o prompt do `script_director.py` limitava rigidamente a "3 ou 4 cenas de 4 a 8s", e o FFmpeg `-shortest` decepava a última cena.
- [x] **Gating Test:** Diagnóstico confirmado experimentalmente via transcrição comparativa de `narration_raw.mp3` vs `narration_trimmed.wav`.

### Fase 2: Correção do Motor de Áudio e Síntese por Cena (Concluída)
- [x] Eliminar o corte destrutivo do `auto-editor` em favor de síntese neural natural com ritmo acelerado nativo (`rate="+6%"`) e `silenceremove` conservador via FFmpeg.
- [x] Implementar geração de áudio por cena em `tts_engine.py`, calculando a duração real exata de cada cena.
- [x] Garantir taxa de amostragem padronizada em 48kHz broadcast (16-bit PCM WAV).
- [x] **Gating Test:** Áudio gerado em português perfeitamente audível, inteligível e transcrevendo 100% fiel ao texto do roteiro.

### Fase 3: Roteirizador com Arco Narrativo Completo e Duração Flexível (Concluída)
- [x] Atualizar `script_director.py` para permitir durações completas (5 a 6 cenas encadeadas: Gancho, Contexto, Tensão, Clímax e Legado).
- [x] Sincronizar o schema das cenas para que `duration_sec` de cada clipe de vídeo seja derivado diretamente do tempo de fala medido no áudio daquela cena (+ margem de respiração de 0.3s).
- [x] **Gating Test:** Geração de roteiro estruturado com 6 cenas coesas sobre o tema fornecido via Ollama local.

### Fase 4: Sincronia Fonética Precisa e Legendas .ASS (Concluída)
- [x] Atualizar `aligner.py` para receber o texto de referência do roteiro (`initial_prompt`), garantindo que o Whisper não alucine palavras.
- [x] Validar que o arquivo `.ass` gerado contenha exatamente as palavras do roteiro com os milissegundos corretos.
- [x] **Gating Test:** Validação de que 100% das palavras do `.ass` correspondem ao texto narrado (zero alucinações).

### Fase 5: Montador FFmpeg e Renderização Master (Concluída)
- [x] Atualizar `main.py` para calcular frames de cada clipe Remotion com base na duração real do áudio daquela cena.
- [x] Garantir que a concatenação de vídeo e áudio termine perfeitamente alinhada, sem corte brusco da última cena.
- [x] Testar renderização ponta a ponta do tema *"O vesúvio de pompeia"*.
- [x] **Gating Test:** Vídeo final `doc_vesuvio_v2_MASTER.mp4` gerado com áudio cristalino (-14.3 dB LUFS broadcast), legendas perfeitamente sincronizadas palavra por palavra, imagens históricas em movimento suave e duração proporcional ao tema.

### Fase 6: Atualização da UI e Validação com o Usuário (Em Progresso)
- [x] Atualizar backend/manifestos para servir o vídeo remasterizado nos cards de projeto da Web UI.
- [ ] Commitar e sincronizar todas as correções no GitHub.
- [ ] Notificar o usuário para inspeção e teste.

---

## 🛑 Guardrails & Regras de Ouro
1. **Zero Zoompan do FFmpeg:** Movimentos de imagem apenas no Remotion com interpolação contínua.
2. **Inteligibilidade Vocal Absoluta:** O áudio nunca pode ser mutilado ou acelerado por cortes artificiais de silêncio que danifiquem fonemas.
3. **Fidelidade Total das Legendas:** As legendas devem refletir o texto exato do roteiro.
4. **Respeito ao Hardware:** Máximo de 8 threads no Ryzen 5 5500 e limites seguros na RTX 3060.
