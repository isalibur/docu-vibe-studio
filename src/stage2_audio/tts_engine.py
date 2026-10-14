"""
src/stage2_audio/tts_engine.py - Motor de síntese de voz (TTS) para narração expressiva.
Provedor primário: edge-tts (voz neural broadcast em nuvem, custo zero e zero VRAM).
Configurado com cadência cinematográfica de documentário (+6% rate para engajamento e clareza).
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
import edge_tts
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TTSEngine")


class TTSEngine:
    def __init__(
        self,
        voice: str = "pt-BR-AntonioNeural",
        rate: str = "+6%",
        pitch: str = "+0Hz"
    ):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def generate_speech_async(self, text: str, output_path: Path) -> Path:
        """Gera áudio MP3 de alta qualidade a partir do texto fornecido via Edge-TTS."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Texto para narração não pode ser vazio.")

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )
        await communicate.save(str(output_path))
        logger.info("Áudio sintetizado com sucesso: %s", output_path)
        return output_path

    def generate_speech(self, text: str, output_path: Path) -> Path:
        """Versão síncrona para integração simples em scripts de esteira."""
        return asyncio.run(self.generate_speech_async(text, output_path))

    @staticmethod
    def get_duration(audio_path: Path) -> float:
        """Calcula a duração exata do arquivo de áudio usando ffprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())


if __name__ == "__main__":
    test_out = Path("workspace/test_audio.mp3")
    engine = TTSEngine()
    engine.generate_speech("Em menos de quarenta e oito horas, quarenta bilhões de dólares desapareceram do mapa.", test_out)
    print(f"Teste de áudio gerado com {test_out.stat().st_size} bytes. Duração: {engine.get_duration(test_out):.2f}s")
    if test_out.exists():
        test_out.unlink()
