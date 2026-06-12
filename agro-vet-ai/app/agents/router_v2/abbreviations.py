import json
import re
from pathlib import Path


def _load_glossary() -> dict:
    path = Path(__file__).parent / "abbreviations.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


GLOSSARY = _load_glossary()


def lookup(abbr: str) -> dict | None:
    entry = GLOSSARY.get(abbr)
    if entry is None:
        return None
    if isinstance(entry, str) and entry.startswith("__ref__"):
        entry = GLOSSARY.get(entry.removeprefix("__ref__"))
    return entry if isinstance(entry, dict) else None


def find_abbreviations_in_text(text: str) -> dict[str, dict]:
    found = {}
    for key in GLOSSARY:
        if re.search(rf'(?<![А-Яа-яA-Za-z0-9.]){re.escape(key)}(?![А-Яа-яA-Za-z0-9.])', text):
            entry = lookup(key)
            if entry:
                found[entry["ru_abbr"]] = entry
    return found


def build_abbreviation_hint(text: str) -> str:
    found = find_abbreviations_in_text(text)
    if not found:
        return ""

    lines = ["[Расшифровка аббревиатур из запроса:]"]
    for entry in found.values():
        ru = entry["ru_abbr"]
        en = entry.get("en_abbr")
        en_part = f" / {en}" if en and en != ru else ""
        lines.append(f"- {ru}{en_part}: {entry['ru']}")

    return "\n".join(lines)
