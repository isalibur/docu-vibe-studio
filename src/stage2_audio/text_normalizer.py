"""
src/stage2_audio/text_normalizer.py - Normalizador Fonético e Semântico para Roteiros de Documentário.
Converte abreviações históricas, datas, medidas e algarismos romanos para texto falado natural em Português Brasileiro (PT-BR).
Exemplos:
- "d.C." / "D.C." -> "depois de Cristo"
- "a.C." / "A.C." -> "antes de Cristo"
- "século I" / "século XIX" -> "século primeiro" / "século dezenove"
- "km" -> "quilômetros" | "km/h" -> "quilômetros por hora"
- "10h30" -> "dez horas e trinta minutos"
"""

import re
from typing import Dict

ROMAN_ORDINALS = {
    "i": "primeiro",
    "ii": "segundo",
    "iii": "terceiro",
    "iv": "quarto",
    "v": "quinto",
    "vi": "sexto",
    "vii": "sétimo",
    "viii": "oitavo",
    "ix": "nono",
    "x": "décimo",
    "xi": "onze",
    "xii": "doze",
    "xiii": "treze",
    "xiv": "quatorze",
    "xv": "quinze",
    "xvi": "dezesseis",
    "xvii": "dezessete",
    "xviii": "dezoito",
    "xix": "dezenove",
    "xx": "vinte",
    "xxi": "vinte e um"
}

NUMBERS_PT = {
    0: "zero", 1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco",
    6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
    11: "onze", 12: "doze", 13: "treze", 14: "quatorze", 15: "quinze",
    16: "dezesseis", 17: "dezessete", 18: "dezoito", 19: "dezenove", 20: "vinte",
    24: "vinte e quatro", 30: "trinta", 40: "quarenta", 50: "cinquenta",
    70: "setenta", 79: "setenta e nove", 80: "oitenta", 90: "noventa", 100: "cem"
}


class TextNormalizer:
    @classmethod
    def normalize_for_speech(cls, text: str) -> str:
        """Aplica a cadeia completa de normalização fonética e expansão semântica."""
        if not text:
            return ""

        t = text

        # 1. Normalização de datas e eras históricas (d.C. e a.C.)
        t = re.sub(r"\b[dD]\.[cC]\.?", "depois de Cristo", t)
        t = re.sub(r"\b[dD][cC]\b", "depois de Cristo", t)
        t = re.sub(r"\b[aA]\.[cC]\.?", "antes de Cristo", t)
        t = re.sub(r"\b[aA][cC]\b", "antes de Cristo", t)

        # 2. Séculos com numerais romanos (século I -> século primeiro, século XIX -> século dezenove)
        def replace_century(m):
            prefix = m.group(1)
            roman = m.group(2).lower()
            spoken = ROMAN_ORDINALS.get(roman, roman)
            return f"{prefix} {spoken}"

        t = re.sub(r"\b(s[eé]culo)\s+([IVXLCDMivxlcdm]+)\b", replace_century, t, flags=re.IGNORECASE)

        # 3. Horários (ex: 10h30 -> 10 horas e 30 minutos, 10h -> 10 horas)
        def replace_time(m):
            h = m.group(1)
            mins = m.group(2)
            if mins:
                return f"{h} horas e {mins} minutos"
            return f"{h} horas"

        t = re.sub(r"\b(\d{1,2})h(\d{2})?\b", replace_time, t)

        # 4. Unidades de medida científicas e geográficas
        t = re.sub(r"\b(\d+)\s*km/h\b", r"\1 quilômetros por hora", t)
        t = re.sub(r"\b(\d+)\s*km\b", r"\1 quilômetros", t)
        t = re.sub(r"\b(\d+)\s*m²\b", r"\1 metros quadrados", t)
        t = re.sub(r"\b(\d+)\s*m³\b", r"\1 metros cúbicos", t)
        t = re.sub(r"\b(\d+)\s*m\b", r"\1 metros", t)
        t = re.sub(r"\b(\d+)\s*º[cC]\b", r"\1 graus Celsius", t)
        t = re.sub(r"\b(\d+)\s*graus\b", r"\1 graus", t)

        # 5. Remove resquícios de markdown como ** ou *
        t = re.sub(r"\*+", "", t)

        # 6. Limpeza de múltiplos espaços
        t = re.sub(r"\s+", " ", t).strip()

        return t
