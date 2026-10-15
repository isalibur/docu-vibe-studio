import sys
from pathlib import Path

# Adiciona audio_factory ao path
sys.path.insert(0, r"D:\IA\audio_factory")

from app.services.voice_clone_service import VoiceCloneService

print("=== TESTANDO CLONAGEM LOCAL VIA VOICE CLONE SERVICE ===")
svc = VoiceCloneService()

ref_audio = r"D:\IA\audio_factory\voices\nova_ref_7s.mp3"
ref_text = "O sistema dos chitibucais foi destruído, mas se você acha que os piratas mais perigosos do mundo ficaram desempregados..."
gen_text = "Em vinte e quatro de agosto do ano setenta e nove, o monte Vesúvio despertou, cobrindo Pompeia em cinzas incandescentes."

print(f"Texto a sintetizar: '{gen_text}'")
res = svc.clone_voice(
    ref_audio_path=ref_audio,
    gen_text=gen_text,
    ref_text=ref_text,
    speed=0.92,
    num_steps=32, # 32 passos para teste veloz
    output_filename="teste_gating_fase2_pompeia"
)

print("\nRESULTADO:")
print(res)
if res.get("success"):
    print("\n>>> CLONAGEM LOCAL EXECUTADA COM SUCESSO! <<<")
else:
    print("\nFALHA:", res.get("error"))
