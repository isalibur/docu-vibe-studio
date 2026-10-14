# Task Plan: Documentário Cinematográfico Real (60s+, Imagens Icônicas e Voz Expressiva)

> **Status:** Em Execução  
> **Workspace:** `D:\IA\editor_inteligente`  
> **Hardware:** AMD Ryzen 5 5500 | 24 GB RAM | NVIDIA RTX 3060 (12 GB VRAM)  
> **Metodologia:** Planning with Files (`task_plan.md`, `findings.md`, `progress.md`)

---

## 🎯 Meta Geral
Transformar o resultado de um "teaser curto de 23s com voz robótica e imagens aleatórias" em um **documentário cinematográfico de verdade**:
1. **Duração & Profundidade (50-65s):** 6 cenas ricas com fatos históricos reais (ano 79 d.C., Plínio, coluna de 30km, fluxos piroclásticos, 20 mil habitantes, escavações). Cada cena com 25 a 40 palavras.
2. **Voz Não-Genérica:** Substituir o genérico Antonio por vozes de documentário autênticas (`pt-BR-ThalitaMultilingualNeural` e `pt-PT-DuarteNeural` com modulação de pitch e cadência cinematográfica).
3. **Imagens Reais e Icônicas:** Filtrar 100% de livros escaneados, arquivos DJVU, placas inadequadas e mapas de satélite modernos. Usar exclusivamente obras de arte históricas (Karl Briullov, Pierre-Jacques Volaire), ruínas icônicas do Fórum Romano e afrescos em 1080p landscape, sem repetição de imagens entre cenas.
4. **UI Amigável:** Permitir seleção de duração (30s, 60s, 90s) e seleção clara das novas vozes narrativas.

---

## 📋 Fases de Execução

### Fase 1: Diagnóstico dos 3 Problemas Apontados (Concluída)
- [x] Imagens erradas: O fetcher baixou a capa de um livro escaneado de 1834 duas vezes, o relevo do Lupanar e um mapa de satélite de 1944 devido à falta de filtros de mídia em `wikimedia_fetcher.py`.
- [x] Voz genérica: O padrão estava fixado em `pt-BR-AntonioNeural` (voz padrão do Edge/Windows sem modulação).
- [x] Duração curta (23s): O prompt gerava apenas 1 frase de 8 a 10 palavras por cena (~50 palavras no total).

### Fase 2: Filtro de Imagens Históricas & Curadoria Visual (Em Progresso)
- [ ] Atualizar `src/stage4_broll/wikimedia_fetcher.py`:
  - Bloquear palavras-chave de lixo de arquivo (`djvu`, `book`, `page`, `scan`, `cover`, `sign`, `lupanar`, `map`, `diagram`, `satellite`, `weather`).
  - Exigir orientação horizontal / landscape (`width > height` e `width >= 1000`).
  - Implementar de-duplicação estrita: rastrear URLs já utilizadas para nunca repetir a mesma imagem em cenas diferentes.
- [ ] Atualizar `script_director.py` para gerar termos de busca visual hiper-específicos e icônicos para cada cena (ex: pinturas a óleo clássicas, ruínas do Fórum, afrescos).
- [ ] **Gating Test:** Testar busca das 6 cenas e verificar que cada imagem baixada é uma obra histórica autêntica em landscape HD.

### Fase 3: Roteirizador de Alta Retenção (50 a 65 segundos)
- [ ] Calibrar `DIRECTOR_SYSTEM_PROMPT` para exigir 25 a 40 palavras por cena, detalhando datas, personagens históricos, medidas geológicas e impacto humano.
- [ ] Atualizar `_generate_fallback_template` com roteiro investigativo completo de 6 cenas (170+ palavras).
- [ ] **Gating Test:** Síntese de áudio atingindo entre 50 e 65 segundos de locução rica.

### Fase 4: Voz Cinematográfica e Expressiva
- [ ] Adicionar `pt-BR-ThalitaMultilingualNeural` (narradora cinematográfica brasileira) e `pt-PT-DuarteNeural` (narrador histórico clássico) como opções de primeira classe.
- [ ] Aplicar modulação de pitch (`pitch="-3Hz"` / `"-5Hz"`) para conferir gravidade e autoridade de documentário.
- [ ] **Gating Test:** Áudio gerado com tom imersivo, zero robótica e zero gagueira.

### Fase 5: Renderização Master & Validação
- [ ] Executar pipeline completo para *"O vesúvio de pompeia"*.
- [ ] Verificar vídeo final: duração entre 50s e 65s, áudio broadcast, legendas sincronizadas palavra por palavra, 6 imagens distintas e cinematográficas animadas em 2.5D.
- [ ] Espelhar resultado no servidor Web e verificar reprodução.
- [ ] Commitar e sincronizar com o GitHub.
