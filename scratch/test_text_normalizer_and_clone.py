import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.stage2_audio.text_normalizer import TextNormalizer
from src.stage2_audio.local_voice_engine import LocalVoiceEngine, VoiceBank

raw_text = "Em 24 de agosto de 79 d.C., o céu escureceu sobre Pompeia às 10h30, lançando cinzas a 30 km de altitude no século I."
normalized = TextNormalizer.normalize_for_speech(raw_text)

print("=== TESTE DE NORMALIZAÇÃO FONÉTICA DOCUMENTÁRIO ===")
print("Texto Original:  ", raw_text)
print("Texto Normalizado:", normalized)

assert "depois de Cristo" in normalized, "Erro: d.C. não foi expandido para depois de Cristo!"
assert "10 horas e 30 minutos" in normalized, "Erro: 10h30 não foi expandido!"
assert "quilômetros" in normalized, "Erro: km não foi expandido!"
assert "século primeiro" in normalized, "Erro: século I não foi expandido!"

print("\n>>> NORMALIZAÇÃO VALIDADA COM SUCESSO! <<<")

print("\n=== GERANDO ÁUDIO CLONADO COM TEXTO NORMALIZADO ===")
bank = VoiceBank()
engine = LocalVoiceEngine(bank)
out_audio = Path("workspace/gating_fase2_audio/teste_clonado_normalizado.wav")

engine.generate_speech(
    text=raw_text,
    output_path=out_audio,
    voice_profile_id="nova_ref_7s"
)

dur = engine.get_duration(out_audio)
print(f"Áudio gerado em: {out_audio.resolve()}")
print(f"Duração exata: {dur:.2f}s")
assert out_audio.exists() and dur > 5.0
print("\n>>> SÍNTESE COM PRONÚNCIA CORRIGIDA CONCLUÍDA! <<<")
