# Findings & Decisions: Estúdio Inteligente de Documentários

Este documento registra todas as decisões arquiteturais, descobertas de pesquisa e parâmetros descobertos ao longo do desenvolvimento.

---

## 1. Ferramental & Ambiente
* **Ambiente Python:** Python 3.10.5 no `.venv` local e 3.12 no sistema, com PyTorch 2.6.0+cu124 já disponível.
* **Ambiente Node.js:** v24.19.0 (compatível com Remotion v4+ e WebMCP).
* **FFmpeg:** Versão 8.1.1 full build instalada e validada com suporte a `h264_nvenc` e `hevc_nvenc`.
* **Tokens & Terminal:** Ferramenta **RTK v0.50.0** instalada via `winget` para redução de overhead de tokens nos comandos de terminal.
* **Planning Framework:** Metodologia e skill oficial **`planning-with-files`** instalada na pasta `.agents/skills/planning-with-files/`.

---

## 2. Decisões Arquiteturais Fundamentais
* **Proibição do `zoompan` do FFmpeg:** Confirmado tecnicamente que o `zoompan` opera com arredondamento inteiro de coordenadas, gerando jitter inaceitável. O Remotion utiliza CSS Transforms e WebGL acelerado com floats contínuos e curvas `cubic-bezier`.
* **Eliminação de Geradores de Vídeo IA (Wan2GP / LTX-Video):** Testes e literatura confirmam que vídeos de modelos DiT levam de 2 a 5 minutos por clipe de 4s na RTX 3060 e consomem ~11 GB de VRAM com risco alto de OOM e artefatos de consistência. A substituição por imagens estáticas FLUX GGUF (~6s por imagem) + recorte RMBG + Parallax 2.5D no Remotion atinge estética superior e renderização ~40x mais rápida.
* **WhisperX vs. Faster-Whisper puro:** WhisperX foi eleito porque aplica alinhamento fonético Wav2Vec2, essencial para posicionar o destaque palavra por palavra na legenda e na caneta marca-texto sobre manchetes.
* **Contrato Pydantic v2:** Centralização de todas as propriedades de cena no `project_manifest.json` com campos estritos e validação de tempo, caminhos de áudio e tipo visual.

---

## 3. Diagnóstico e Resolução do Problema da Amostra Repetida (13/10/2026)
* **Causa Raiz 1 (Fallback Estático no Roteirizador):** Quando nenhuma chave de API (`GEMINI_API_KEY`) estava presente no `.env`, `_generate_fallback_template` no `script_director.py` gerava um roteiro fixo sobre o colapso financeiro de 2008, ignorando o tema fornecido. Corrigido com gerador heurístico investigativo que extrai palavras-chave do tema fornecido e constrói dinamicamente Manchetes 3D, Gráficos de Impacto e chamadas históricas para o tema exato (ex: Monte Vesúvio de Pompeia).
* **Causa Raiz 2 (Faster-Whisper Silero VAD no Áudio Tratado):** O parâmetro `vad_filter=True` em áudios já limpos pelo auto-editor descartava a fala gerada pelo TTS, retornando 0 palavras. Desabilitando `vad_filter` e utilizando o modelo `base`, o extrator capturou com perfeição 86 palavras com timestamps fonéticos milimétricos.
* **Causa Raiz 3 (Filtro FFmpeg de Legendas Desconectado):** `ffmpeg_composer.py` preparava a string `vf_str` mas não a injetava no comando. O pipeline foi unificado com `[0:v]subtitles='...'[vout]` e `[2:a]sidechaincompress...[aout]` dentro do mesmo `-filter_complex`, queimando legendas dinâmicas ciano no render NVENC H.264.
* **Causa Raiz 4 (Mídia Híbrida Desconectada em main.py):** O estágio 4 chamava apenas `broll_fetcher` (que gerava tela escura sem chave de API). O pipeline foi integrado de ponta a ponta com `WikimediaFetcher` (100% gratuito e público) + `ParallaxSegmenter` (`rembg`) + Remotion `DocumentaryParallax`, entregando imagens reais históricas com efeito 2.5D.
* **Causa Raiz 5 (Cache do Player no Navegador e Opções de UI):** O player do frontend carregava URLs sem parâmetro de bust de cache (`?t=timestamp`), e o servidor não repassava as opções de voz e pasta local. Adicionado cache-busting, repasse de argumentos e campo para salvar chave do Gemini direto no frontend.
