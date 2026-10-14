"""
src/stage2_audio/tts_engine.py - Motor de síntese de voz (TTS) para narração expressiva.
Provedor primário: edge-tts (voz neural broadcast em nuvem, custo zero e zero VRAM).
"""

import asyncio
from pathlib import Path
from typing import Optional
import edge_tts
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TTSEngine")


class TTSEngine:
    def __init__(self, voice: str = "pt-BR-AntonioNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def generate_speech_async(self, text: str, output_path: Path) -> Path:
        """Gera áudio MP3 de alta qualidade a partir do texto fornecido via Edge-TTS."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Limpa possíveis tags ou espaços extras
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


if __name__ == "__main__":
    test_out = Path("workspace/test_audio.mp3")
    engine = TTSEngine()
    engine.generate_speech("Em menos de quarenta e oito horas, quarenta bilhões de dólares desapareceram do mapa.", test_out)
    print(f"Teste de áudio gerado com {test_out.stat().st_size} bytes.")
    if test_out.exists():
        test_out.unlink()
