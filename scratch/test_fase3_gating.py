import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.stage3_captions.aligner import AudioAligner, WordTimestamp
from src.stage3_captions.ass_generator import ASSGenerator

print("=== INICIANDO GATING TEST DA FASE 3: LEGENDAS CINEMATOGRÁFICAS & LEITURA NATURAL ===")
start = time.time()

# 1. Simula palavras alinhadas com pontuação real de documentário
mock_words = [
    WordTimestamp("Em", 0.0, 0.25, 0.98),
    WordTimestamp("24", 0.25, 0.60, 0.99),
    WordTimestamp("de", 0.60, 0.75, 0.99),
    WordTimestamp("agosto", 0.75, 1.20, 0.98),
    WordTimestamp("de", 1.20, 1.35, 0.99),
    WordTimestamp("79", 1.35, 1.70, 0.97),
    WordTimestamp("d.C.,", 1.70, 2.10, 0.95), # Vírgula / divisão de oração
    WordTimestamp("o", 2.30, 2.45, 0.99),
    WordTimestamp("céu", 2.45, 2.80, 0.98),
    WordTimestamp("escureceu", 2.80, 3.40, 0.96),
    WordTimestamp("sobre", 3.40, 3.70, 0.99),
    WordTimestamp("Pompeia,", 3.70, 4.30, 0.97), # Vírgula
    WordTimestamp("enquanto", 4.50, 4.90, 0.98),
    WordTimestamp("o", 4.90, 5.05, 0.99),
    WordTimestamp("Vesúvio", 5.05, 5.55, 0.99),
    WordTimestamp("despertava.", 5.55, 6.30, 0.98), # Ponto final forte
    WordTimestamp("Uma", 6.80, 7.00, 0.99),
    WordTimestamp("coluna", 7.00, 7.45, 0.98),
    WordTimestamp("colossal", 7.45, 8.10, 0.97),
    WordTimestamp("atingiu", 8.10, 8.60, 0.96),
    WordTimestamp("a", 8.60, 8.70, 0.99),
    WordTimestamp("estratosfera.", 8.70, 9.50, 0.98) # Ponto final forte
]

out_ass = Path("workspace/gating_fase3_captions/documentary_subtitles.ass")
generator = ASSGenerator(font_name="Segoe UI", font_size=42)
generator.generate_ass(mock_words, out_ass)

assert out_ass.exists(), "Erro: Arquivo .ass não foi criado."
lines = out_ass.read_text(encoding="utf-8").splitlines()

dialogue_lines = [l for l in lines if l.startswith("Dialogue:")]
print(f"\n[1] Total de eventos de legenda gerados: {len(dialogue_lines)}")

# Validações estritas de qualidade cinematográfica
for idx, dl in enumerate(dialogue_lines, 1):
    print(f"  Evento {idx}: {dl}")
    assert r"{\c" not in dl, f"Erro: Efeito karaokê de cor detectado no evento {idx}!"
    assert r"\fscx" not in dl, f"Erro: Efeito de escala/pop detectado no evento {idx}!"

# Verifica que o número de eventos é pequeno (frases completas, não palavras soltas)
assert len(dialogue_lines) <= 5, f"Erro: Muitas quebras excessivas ({len(dialogue_lines)} eventos para 22 palavras)."

# Teste com áudio real gerado na Fase 2
real_audio = Path("workspace/gating_fase2_audio/teste_duarte.wav")
if real_audio.exists():
    print("\n[2] Alinhando com áudio real e gerando legendas com Faster-Whisper...")
    aligner = AudioAligner(model_size="base", device="cpu", compute_type="int8")
    ref_script = "Pompeia virou museu a céu aberto, ensinando ao mundo a fragilidade humana e a força implacável da natureza."
    real_words = aligner.align_audio(real_audio, language="pt", reference_text=ref_script)
    real_out = Path("workspace/gating_fase3_captions/real_duarte_subtitles.ass")
    generator.generate_ass(real_words, real_out)
    real_lines = [l for l in real_out.read_text(encoding="utf-8").splitlines() if l.startswith("Dialogue:")]
    print(f"  -> Legendas geradas do áudio real ({len(real_lines)} orações sintáticas):")
    for rl in real_lines:
        print(f"     {rl}")

elapsed = time.time() - start
print(f"\n[3] Tempo do Gating Test: {elapsed:.2f}s")
print("\n" + "="*60)
print(">>> GATING TEST FASE 3 APROVADO COM LOUVOR! <<<")
print("="*60)
