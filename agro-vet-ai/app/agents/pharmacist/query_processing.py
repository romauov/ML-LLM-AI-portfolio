import re
import json
from pathlib import Path


class DiseaseQueryExpander:
    """Расширяет поисковый запрос синонимами болезней из маппинга."""

    def __init__(self):
        mapping_path = Path(__file__).parent.parent.parent.parent / "knowledge/data/drugs/diseases_mapping.json"
        self.disease_map = {}

        if mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Объединяем avian и swine diseases
                for category in data.values():
                    for disease_name, variants in category.items():
                        # Собираем все варианты названия болезни
                        all_forms = set()
                        all_forms.add(disease_name.lower())
                        all_forms.update(v.lower() for v in variants.get('abbreviations', []))
                        all_forms.update(v.lower() for v in variants.get('russian_forms', []))
                        all_forms.update(v.lower() for v in variants.get('latin_names', []))

                        # Каждый вариант -> все варианты
                        for form in all_forms:
                            self.disease_map[form] = all_forms

    def expand_query(self, query: str) -> list[str]:
        """Возвращает список терминов для поиска (оригинал + синонимы)."""
        query_lower = query.lower().strip()
        terms = {query}  # Сохраняем оригинал с регистром

        # Разбиваем на слова, учитывая пунктуацию
        words = re.findall(r'\b\w+\b', query_lower)

        # Проверяем отдельные слова и комбинации
        for i, word in enumerate(words):
            # Одно слово
            if word in self.disease_map:
                terms.update(self.disease_map[word])

            # Биграммы
            if i < len(words) - 1:
                bigram = f"{word} {words[i + 1]}"
                if bigram in self.disease_map:
                    terms.update(self.disease_map[bigram])

        return list(terms)