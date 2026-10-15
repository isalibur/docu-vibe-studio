import json
import subprocess
import sys
from pathlib import Path

AUDIO_FACTORY_PYTHON = "D:/IA/audio_factory/.venv/Scripts/python.exe"

script = """import sys
import json
from pathlib import Path

sys.path.insert(0, "D:/IA/audio_factory")
from app.services.voice_clone_service import VoiceCloneService

svc = VoiceCloneService()
res = svc.clone_voice(
    ref_audio_path=sys.argv[1],
    gen_text=sys.argv[2],
    ref_text=sys.argv[3],
    speed=float(sys.argv[4]),
    output_filename=sys.argv[5],
    num_steps=32
)
print("---CLONE_RESULT_JSON---")
print(json.dumps(res))
"""

runner_file = Path("scratch/temp_runner.py")
runner_file.write_text(script, encoding="utf-8")

cmd = [
    AUDIO_FACTORY_PYTHON,
    str(runner_file.resolve()),
    "D:/IA/editor_inteligente/assets/voices/nova_ref_7s.mp3",
    "Em menos de vinte e quatro horas, a historia de Pompeia foi reescrita para sempre.",
    "O sistema dos chitibucais foi destruido, mas se voce acha que os piratas mais perigosos do mundo ficaram desempregados...",
    "0.92",
    "teste_subproc_clone"
]

print("Executando subprocesso de clonagem...")
res = subprocess.run(cmd, cwd="D:/IA/audio_factory", capture_output=True, text=True, encoding="utf-8")
print("STDOUT:", res.stdout[-400:])
if res.returncode != 0:
    print("STDERR:", res.stderr)
