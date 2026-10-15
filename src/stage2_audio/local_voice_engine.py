"""
src/stage2_audio/local_voice_engine.py - Motor de Síntese e Clonagem de Voz Local com Banco Multi-Vozes.
Suporta:
1. Clonagem de Voz Local Zero-Shot (OmniVoice / F5-TTS) via audio_factory na GPU RTX 3060.
2. Banco Dinâmico de Perfis de Voz (Voice Bank): escaneia assets/voices/ e D:/IA/audio_factory/voices/
   permitindo ao usuário adicionar novos áudios .wav para qualquer tom/assunto a qualquer momento.
3. Presets Neurais Humanizados (cadência de documentário pausada com rate negativo e pitch calibrado).
4. Normalização padrão broadcast em WAV 48kHz PCM 16-bit mono.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import edge_tts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LocalVoiceEngine")

AUDIO_FACTORY_PYTHON = "D:/IA/audio_factory/.venv/Scripts/python.exe"
AUDIO_FACTORY_DIR = "D:/IA/audio_factory"


@dataclass
class VoiceProfile:
    id: str
    name: str
    voice_type: str  # "cloned" ou "neural_preset"
    audio_path: Optional[str] = None
    ref_text: Optional[str] = None
    description: str = ""


from src.stage2_audio.text_normalizer import TextNormalizer

class VoiceBank:
    """Gerencia e descobre dinamicamente todos os perfis de voz disponíveis."""

    def __init__(self, project_voices_dir: Path = Path("assets/voices")):
        self.project_voices_dir = project_voices_dir
        self.project_voices_dir.mkdir(parents=True, exist_ok=True)
        self.audio_factory_voices_dir = Path("D:/IA/audio_factory/voices")

    def list_profiles(self) -> List[VoiceProfile]:
        profiles: Dict[str, VoiceProfile] = {}

        # 1. Presets Neurais Brasileiros de Primeira Classe (Documentário / História em PT-BR)
        presets = [
            VoiceProfile(
                id="pt-BR-ThalitaMultilingualNeural",
                name="Thalita (Narradora Brasileira / Documentário Cinematográfico)",
                voice_type="neural_preset",
                description="Voz feminina brasileira profunda, cinematográfica e de excelente articulação."
            ),
            VoiceProfile(
                id="pt-BR-FranciscaNeural",
                name="Francisca (Jornalística Brasileira / Investigativa)",
                voice_type="neural_preset",
                description="Voz formal, firme e investigativa em português brasileiro."
            )
        ]
        for p in presets:
            profiles[p.id] = p

        # 2. Escaneia pastas de vozes clonadas (assets/voices e audio_factory/voices)
        scan_dirs = [self.project_voices_dir]
        if self.audio_factory_voices_dir.exists():
            scan_dirs.append(self.audio_factory_voices_dir)

        for sdir in scan_dirs:
            for audio_file in sdir.glob("*.*"):
                if audio_file.suffix.lower() not in [".wav", ".mp3", ".ogg"]:
                    continue

                stem_id = audio_file.stem
                if stem_id in profiles:
                    continue

                # Tenta carregar metadata JSON correspondente
                meta_file = audio_file.with_suffix(".json")
                name = stem_id.replace("_", " ").title()
                desc = "Perfil de voz clonada local"
                ref_text = ""

                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            name = data.get("name", name)
                            desc = data.get("description", desc)
                            ref_text = data.get("ref_text", "")
                    except Exception:
                        pass

                profiles[stem_id] = VoiceProfile(
                    id=stem_id,
                    name=f"{name} (Voz Clonada Local)",
                    voice_type="cloned",
                    audio_path=str(audio_file.resolve()).replace("\\", "/"),
                    ref_text=ref_text,
                    description=desc
                )

        return list(profiles.values())

    def get_profile(self, profile_id: str) -> Optional[VoiceProfile]:
        for p in self.list_profiles():
            if p.id.lower() == profile_id.lower() or p.name.lower() == profile_id.lower():
                return p
        return None


class LocalVoiceEngine:
    """Motor unificado de síntese de voz (Clonagem Local + Presets de Documentário)."""

    def __init__(self, voice_bank: Optional[VoiceBank] = None):
        self.bank = voice_bank or VoiceBank()

    def generate_speech(
        self,
        text: str,
        output_path: Path,
        voice_profile_id: Optional[str] = None,
        speed: float = 0.92
    ) -> Path:
        """
        Gera narração humanizada com cadência cinematográfica.
        Se o perfil for 'cloned', executa na GPU via OmniVoice isolado.
        Se for preset neural, executa Edge-TTS calibrado com rate negativo e pitch solene.
        Converte o áudio final para WAV 48kHz mono sem perdas.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        clean_text = TextNormalizer.normalize_for_speech(text.strip())
        if not clean_text:
            raise ValueError("Texto para narração não pode ser vazio.")
        logger.info("Texto normalizado para fala: '%s'", clean_text)

        # Identifica perfil solicitado ou usa padrão
        profile = None
        if voice_profile_id:
            profile = self.bank.get_profile(voice_profile_id)

        # Se não encontrou ou não especificou, tenta achar um perfil clonado ou usa Duarte/Thalita
        if not profile:
            profiles = self.bank.list_profiles()
            # Prioriza voz clonada se existir
            cloned = [p for p in profiles if p.voice_type == "cloned" and "nova_ref" in p.id]
            profile = cloned[0] if cloned else self.bank.get_profile("pt-BR-ThalitaMultilingualNeural")

        logger.info("Sintetizando fala com perfil: '%s' (Tipo: %s)", profile.name, profile.voice_type)

        temp_raw = output_path.with_name(f"temp_raw_{output_path.stem}.wav")

        if profile.voice_type == "cloned" and profile.audio_path:
            self._generate_cloned_speech(
                text=clean_text,
                profile=profile,
                output_wav=temp_raw,
                speed=speed
            )
        else:
            self._generate_neural_speech(
                text=clean_text,
                voice_name=profile.id,
                output_wav=temp_raw
            )

        # Converte para broadcast standard 48kHz mono PCM 16-bit
        cmd_convert = [
            "ffmpeg", "-y",
            "-i", str(temp_raw.resolve()),
            "-ar", "48000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            str(output_path.resolve())
        ]
        subprocess.run(cmd_convert, capture_output=True, check=True)

        if temp_raw.exists():
            temp_raw.unlink()

        dur = self.get_duration(output_path)
        logger.info("Áudio final masterizado gerado: %s (%.2f segundos)", output_path.name, dur)
        return output_path

    def _generate_cloned_speech(
        self,
        text: str,
        profile: VoiceProfile,
        output_wav: Path,
        speed: float
    ):
        """Executa a clonagem de voz via runner isolado no ambiente audio_factory."""
        ref_text = profile.ref_text or "Texto de referência padrão para clonagem de áudio."
        runner_code = """import sys
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
        runner_file = Path("scratch/cloner_worker.py")
        runner_file.parent.mkdir(parents=True, exist_ok=True)
        runner_file.write_text(runner_code, encoding="utf-8")

        temp_name = f"clone_temp_{output_wav.stem}"
        cmd = [
            AUDIO_FACTORY_PYTHON,
            str(runner_file.resolve()),
            str(profile.audio_path),
            text,
            ref_text,
            str(speed),
            temp_name
        ]

        logger.info("Disparando síntese de clonagem no worker GPU...")
        proc = subprocess.run(
            cmd,
            cwd=AUDIO_FACTORY_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if proc.returncode != 0:
            logger.error("Erro no worker de clonagem: %s", proc.stderr)
            raise RuntimeError(f"Falha na clonagem de voz: {proc.stderr}")

        # Localiza o arquivo gerado na pasta de saída da audio_factory
        factory_out = Path("D:/IA/audio_factory/output") / f"{temp_name}.wav"
        if not factory_out.exists():
            raise FileNotFoundError(f"Arquivo gerado não encontrado em {factory_out}")

        shutil.copyfile(factory_out, output_wav)
        if factory_out.exists():
            factory_out.unlink()

    def _generate_neural_speech(
        self,
        text: str,
        voice_name: str,
        output_wav: Path
    ):
        """Síntese via Edge-TTS com calibração de cadência de documentário (-3% rate, -3Hz pitch)."""
        temp_mp3 = output_wav.with_suffix(".mp3")
        
        async def _run_edge():
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_name,
                rate="-3%",
                pitch="-3Hz"
            )
            await communicate.save(str(temp_mp3))

        asyncio.run(_run_edge())

        cmd = ["ffmpeg", "-y", "-i", str(temp_mp3), str(output_wav)]
        subprocess.run(cmd, capture_output=True, check=True)

        if temp_mp3.exists():
            temp_mp3.unlink()

    @staticmethod
    def get_duration(audio_path: Path) -> float:
        """Calcula a duração exata do áudio usando ffprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
