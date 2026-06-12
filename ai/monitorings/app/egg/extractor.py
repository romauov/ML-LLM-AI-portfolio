import re
from typing import Optional

spell_mapping = {
    'C0': 'С0',
    'C1': 'С1',
    'C2': 'С2',
    'C3': 'С3',
    'CB': 'СВ',
    'CО': 'С0',
    'CO': 'С0',
    'СО': 'С0',
    'СO': 'С0',
    'ПЕРЕПЕЛ': 'Перепелиное',
    'ПЕРЕПЕЛИНОЕ': 'Перепелиное'
}


def extract_egg_category(text: str) -> Optional[str]:
    if not isinstance(text, str):
        return None

    match = re.search(r'(\b[CС][0-3ВBOО]|перепелиное|перепел)\b', text, flags=re.IGNORECASE)
    if match:
        category = match.group().upper()
        return spell_mapping.get(category, category)

    return None
