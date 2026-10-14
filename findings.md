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
