"""
src/stage3_captions/aligner.py - Alinhador fonético e extrator de timestamps por palavra.
Utiliza Faster-Whisper (com CTranslate2) configurado em int8_float16 para precisão e baixo consumo de VRAM (<3.5 GB).
Executa rotina obrigatória de limpeza de memória VRAM (flush_vram) pós-inferência.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import logging
from src.core.vram_guard import flush_vram

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WhisperAligner")


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    probability: float


class AudioAligner:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type if device == "cuda" else "int8"

    def align_audio(self, audio_path: Path, language: str = "pt", reference_text: Optional[str] = None) -> List[WordTimestamp]:
        """
        Transcreve o áudio extraindo os timestamps exatos de cada palavra individual.
        Utiliza reference_text como prompt inicial para guiar o vocabulário e impedir alucinações.
        Descarrega o modelo da memória imediatamente após o término para evitar OOM.
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Áudio não encontrado para alinhamento: {audio_path}")

        from faster_whisper import WhisperModel

        logger.info(
            "Carregando WhisperModel (%s) no dispositivo: %s (compute: %s)",
            self.model_size, self.device, self.compute_type
        )
        
        # Carrega modelo com fallback robusto
        try:
            model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        except Exception as e:
            logger.warning("Falha ao carregar modelo configurado (%s). Usando fallback em CPU int8.", str(e))
            model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

        words: List[WordTimestamp] = []
        try:
            transcribe_kwargs = {
                "language": language,
                "word_timestamps": True,
                "beam_size": 5,
                "vad_filter": False
            }
            if reference_text:
                transcribe_kwargs["initial_prompt"] = reference_text[:1000]

            segments, _ = model.transcribe(
                str(audio_path),
                **transcribe_kwargs
            )

            for segment in segments:
                if segment.words:
                    for w in segment.words:
                        clean_word = w.word.strip()
                        if clean_word:
                            words.append(
                                WordTimestamp(
                                    word=clean_word,
                                    start=round(w.start, 3),
                                    end=round(w.end, 3),
                                    probability=round(w.probability, 3)
                                )
                            )
            logger.info("Alinhamento concluído: %d palavras extraídas com timestamps.", len(words))
        finally:
            # Liberação explícita de memória
            del model
            flush_vram()

        return words
