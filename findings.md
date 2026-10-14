# Findings & Decisions: Estúdio Inteligente de Documentários

Este documento registra todas as decisões arquiteturais, descobertas de pesquisa e parâmetros descobertos ao longo do desenvolvimento.

---

## 1. Ferramental & Ambiente
* **Ambiente Python:** Python 3.10.5 no `.venv` local e 3.12 no sistema, com PyTorch 2.6.0+cu124 já disponível.
* **Ambiente Node.js:** v24.19.0 (compatível com Remotion v4+ e WebMCP).
* **FFmpeg:** Versão 8.1.1 full build instalada e validada com suporte a `h264_nvenc` e `hevc_nvenc`.
* **Hardware:** AMD Ryzen 5 5500 (6 núcleos / 12 threads), 24 GB RAM, NVIDIA GeForce RTX 3060 (12 GB VRAM).
* **LLM Local:** Ollama v0.40.3 com `qwen2.5:3b` operando 100% offload na GPU (37/37 camadas na VRAM, consumo <2 GB).

---

## 2. Descobertas Críticas do Code Review (14/10/2026)

### Descoberta 1: Por que a voz ficou inaudível e as legendas alucinadas?
* **Causa Raiz Identificada:** No estágio 2, o áudio sintetizado pelo `edge-tts` (`narration_raw.mp3`) era absolutamente perfeito, nítido e em português correto. Porém, em seguida o script chamava:
  ```bash
  auto-editor narration_raw.mp3 --edit audio:threshold=4% --margin 0.28sec -o narration_trimmed.wav
  ```
* O `auto-editor` com threshold fixo de volume em 4% interpretou consoantes suaves, transições de sílabas e fonemas sibilantes/fricativos como "silêncio", decepando partes de cada palavra e costurando os pedaços restantes.
* **Resultado:** O áudio virou um murmúrio truncado e repetitivo ("Jususususus...").
* Quando o Faster-Whisper tentou transcrever esse áudio picotado, gerou alucinações absurdas:
  *"Os seus tempores são as horas de palma dos tempores, nos depoque eles se usam os seus likes..."*
* Essas alucinações foram salvas no `.ass` e queimadas no vídeo.
* **Solução Arquitetural:** 
  1. Abandonar o corte destrutivo de silêncios do `auto-editor` para vozes neurais TTS (que já possuem ritmo natural e fluído).
  2. Para documentários dinâmicos, utilizar aceleração nativa de prosódia do TTS (`rate="+8%"` ou `rate="+10%"`) no `edge-tts` e, se necessário, filtro conservador de silêncio longo do FFmpeg (`silenceremove`).
  3. Alinhar a transcrição do Whisper usando o texto original do roteiro como guia (`initial_prompt`), impedindo qualquer alucinação.

### Descoberta 2: Por que o vídeo durou apenas 19 segundos?
* **Causa Raiz Identificada:** 
  1. O prompt do `script_director.py` continha a instrução explícita: *"com 3 ou 4 cenas dinâmicas (4 a 8 segundos cada)"*.
  2. As 4 frases geradas duraram 19.03 segundos no áudio sintetizado.
  3. No FFmpeg, a flag `-shortest` encerrou o vídeo assim que o áudio de 19.03s terminou, cortando o final da cena 4.
* **Solução Arquitetural:**
  1. Permitir durações configuráveis (ex: 5 a 8 cenas para um documentário padrão de 45 a 90 segundos com arco narrativo completo: Gancho, Contextualização, Aprofundamento, Clímax e Reflexão Final).
  2. Sincronizar o vídeo com o áudio: calcular o número exato de frames de cada cena a partir da duração real da narração daquela cena específica (+ margem de respiração), garantindo que o vídeo e a fala terminem no mesmo frame exato.

### Descoberta 3: Por que o Parallax e o Visual funcionaram bem?
* O componente `DocumentaryParallax.tsx` com CSS transforms (`transform: scale(...) translateX(...)`) e interpolação de sub-pixel em 60/30fps garantiu fluidez cinematográfica sem nenhum jitter.
* As mídias históricas do Wikimedia Commons foram carregadas em alta resolução (1080p).
* O visual agradou ao usuário; o problema residia exclusivamente no tripé Áudio / Legenda / Duração.
