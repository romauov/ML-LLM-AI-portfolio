# Словарь сокращений
import re

ABBREVIATIONS = {
    "ГП": "Грипп птиц",
    "НБ": "Ньюкаслская болезнь",
    "ИБК": "Инфекционный бронхит кур",
    "ИББ": "Инфекционная бурсальная болезнь",
    "ИЛТ": "Инфекционный ларинготрахеит",
    "РЕО": "Реовирусная инфекция птиц",
}


def expand_abbreviations(text: str | None) -> str:
    """Заменяет сокращения на полные названия."""
    if not text:
        return ""

    pattern = r'\b(' + '|'.join(re.escape(abbr) for abbr in ABBREVIATIONS.keys()) + r')\b'
    return re.sub(pattern, lambda match: ABBREVIATIONS[match.group(0)], text)