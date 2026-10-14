# 🎨 DESIGN.md: Sistema Visual do Estúdio de Documentários (Vox / Investigativo)
> **Projeto:** `D:\IA\editor_inteligente`  
> **Estilo Visual:** Documentário Investigativo Cinematográfico (*Vox*, *Johnny Harris*, *Fern*, *Magnates*)  
> **Resolução Padrão:** 1920x1080 (Full HD, 30 fps) | Margens Seguras: 80px horizontal / 60px vertical

---

## 1. Princípios Estéticos Fundamentais
1. **Fundo com Textura e Profundidade (Nunca Preto 100% Puro):**
   * O fundo principal é um carvão profundo com textura sutil de papel vegetal escuro ou grid milimetrado técnico quase imperceptível (`#0F1115` ou `#12141A`).
   * Camada global superior com vinheta escura suave e *Film Grain* 35mm a 15-20% de opacidade para unificar todas as mídias.
2. **Contraste Editorial e Cores de Impacto:**
   * Textos e cartões de dados usam alto contraste.
   * Destaques em caneta marca-texto animada e linhas de gráficos usam cores vibrantes e intencionais (amarelo investigativo ou vermelho de crise).
3. **Movimento Baseado em Física (Anti-Jitter):**
   * Movimento de câmera contínuo via sub-pixel em CSS/WebGL (`interpolate` e `spring`).
   * Transições em desaceleração elástica cúbica (*cubic-bezier* `0.16, 1, 0.3, 1`).

---

## 2. Paleta de Cores Oficial

| Token | Hex | Uso / Aplicação |
| :--- | :--- | :--- |
| **`bg-canvas`** | `#0D0F12` | Fundo principal escuro das cenas do Remotion |
| **`bg-paper-dark`** | `#161920` | Superfície de cartões, recortes de jornais escuros e molduras |
| **`bg-paper-aged`** | `#F4EFE6` | Textura de jornal de época / documentos de arquivo |
| **`text-primary`** | `#F8FAFC` | Texto principal, manchetes de alto impacto (Slate 50) |
| **`text-muted`** | `#94A3B8` | Fontes de dados, legendas de rodapé e anos de linha do tempo |
| **`accent-yellow`** | `#FCD34D` / `#F59E0B` | Cor da caneta marca-texto animada e pontos de destaque |
| **`accent-red`** | `#EF4444` | Alertas de crise, quedas acentuadas em gráficos financeiros |
| **`accent-cyan`** | `#00F0FF` | Highlight da palavra ativa nas legendas dinâmicas `.ass` |
| **`accent-grid`** | `rgba(255, 255, 255, 0.04)` | Linhas de grade técnica e guias de gráficos |

---

## 3. Tipografia e Pareamentos de Fontes

| Função | Família de Fontes | Peso | Estilo / Rationale |
| :--- | :--- | :--- | :--- |
| **Manchetes & Títulos de Impacto** | `Playfair Display` ou `Cinzel` | Bold (700) | Traz a autoridade jornalística de um New York Times / Financial Journal. |
| **Dados, Números e Rótulos Técnicos** | `JetBrains Mono` ou `Space Mono` | Medium (500) | Estética investigativa de dados, percentuais e datas financeiras. |
| **Subtítulos & Legendas Dinâmicas** | `Inter` ou `Montserrat` | SemiBold (600) | Altíssima legibilidade em telas móveis e desktop com espaçamento de -0.02em. |

---

## 4. Diretrizes de Componentes do Remotion

### 4.1 `NewspaperHighlight`
* Recorte em leve inclinação isométrica ou perspectiva sutil (`transform: perspective(1000px) rotateX(4deg)`).
* O marca-texto anima cobrindo a frase-chave com `width: interpolate(frame, [start, end], [0, 100])%`.
* Textura de papel com bordas levemente rasgadas ou sombra projetada (`drop-shadow(0 25px 35px rgba(0,0,0,0.8))`).

### 4.2 `DataChartCard`
* O eixo X (tempo) e o eixo Y (valores) aparecem com fade sutil.
* A linha ou as barras se constroem progressivamente acompanhadas por um som de bip digital discreto (`digital_beep.wav`).
* Rótulo de fonte de dados no rodapé sempre em `text-muted` e fonte menor (14-16px) com opacidade 70%.

### 4.3 `DocumentaryParallax` (2.5D Cutout)
* Sujeito recortado em primeiro plano via `rembg` (RMBG-2.0).
* Escala do fundo: de `1.00` para `1.10`.
* Escala do sujeito: de `1.00` para `1.04` com translação vertical suave e sombra profunda para destacar a separação de profundidade.

### 4.4 Legendas Dinâmicas (`captions_ass`)
* Máximo de 3 a 5 palavras por linha na base da tela (margem segura de 120px do rodapé).
* Palavra dita no milissegundo recebe cor `#00F0FF` (Ciano) e leve aumento de escala (110%), voltando ao branco `#FFFFFF` imediatamente após ser falada.
