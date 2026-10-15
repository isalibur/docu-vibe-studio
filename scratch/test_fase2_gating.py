import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.stage2_audio.local_voice_engine import LocalVoiceEngine, VoiceBank

print("=== INICIANDO GATING TEST DA FASE 2: MOTOR DE VOZ & BANCO MULTI-PERFIL ===")
start = time.time()

bank = VoiceBank()
profiles = bank.list_profiles()

print(f"\n[1] Total de perfis descobertos no Voice Bank: {len(profiles)}")
for p in profiles:
    print(f"  * ID: '{p.id}' | Nome: '{p.name}' | Tipo: {p.voice_type}")

assert len(profiles) >= 3, "Erro: Banco de vozes deve ter pelo menos 3 perfis disponíveis."

engine = LocalVoiceEngine(bank)
out_dir = Path("workspace/gating_fase2_audio")
out_dir.mkdir(parents=True, exist_ok=True)

# Teste 1: Síntese com Voz Clonada Local (GPU)
print("\n[2] Testando Síntese com Perfil de Voz Clonada Local ('nova_ref_7s')...")
text_cloned = "Em vinte e quatro de agosto de setenta e nove d.C., o céu escureceu sobre Pompeia enquanto o Vesúvio despertava."
cloned_wav = out_dir / "teste_cloned.wav"

t_start = time.time()
engine.generate_speech(text_cloned, cloned_wav, voice_profile_id="nova_ref_7s")
dur_cloned = engine.get_duration(cloned_wav)
gen_time_cloned = time.time() - t_start

print(f"  -> Áudio gerado: {cloned_wav.name} | Duração: {dur_cloned:.2f}s | Tempo de síntese: {gen_time_cloned:.2f}s")
assert cloned_wav.exists() and cloned_wav.stat().st_size > 10000, "Erro: arquivo de áudio clonado inválido."
assert dur_cloned >= 5.0, "Erro: áudio gerado muito curto."

# Teste 2: Síntese com Narrador Histórico Solene (Duarte)
print("\n[3] Testando Síntese com Narrador Histórico Solene ('pt-PT-DuarteNeural')...")
text_duarte = "Pompeia virou museu a céu aberto, ensinando ao mundo a fragilidade humana e a força implacável da natureza."
duarte_wav = out_dir / "teste_duarte.wav"

t_start = time.time()
engine.generate_speech(text_duarte, duarte_wav, voice_profile_id="pt-PT-DuarteNeural")
dur_duarte = engine.get_duration(duarte_wav)
gen_time_duarte = time.time() - t_start

print(f"  -> Áudio gerado: {duarte_wav.name} | Duração: {dur_duarte:.2f}s | Tempo de síntese: {gen_time_duarte:.2f}s")
assert duarte_wav.exists() and duarte_wav.stat().st_size > 10000, "Erro: arquivo de áudio histórico inválido."

elapsed = time.time() - start
print(f"\n[4] Tempo total do Gating Test: {elapsed:.2f}s")
print("\n" + "="*60)
print(">>> GATING TEST FASE 2 APROVADO COM LOUVOR! <<<")
print("="*60)
