"""
Утилиты для модуля topics.
Содержит общие функции для лемматизации и работы с текстом.
"""
import re
import json
from pydantic import ValidationError
import pymorphy3
from typing import List

from app.utils.logger import get_logger


class TextUtils:
    """Утилиты для работы с текстом и лемматизации."""

    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()
        self.logger = get_logger(__name__)
    
    def lemmatize_keywords(self, keywords: List[str]) -> List[str]:
        """
        Лемматизировать список ключевых слов.
        
        :param keywords: Список ключевых слов
        :return: Список лемматизированных ключевых слов
        """
        lemmatized = []
        for keyword in keywords:
            try:
                # Разбиваем ключевое слово на отдельные слова
                words = keyword.split()
                lemmatized_words = []
                
                for word in words:
                    # Очищаем от пунктуации
                    clean_word = word.strip('?!.,')
                    if clean_word:
                        # Получаем лемму через pymorphy3
                        parsed = self.morph.parse(clean_word)
                        if parsed:
                            normal_form = parsed[0].normal_form
                            lemmatized_words.append(normal_form)
                        else:
                            lemmatized_words.append(clean_word)
                
                # Объединяем лемматизированные слова
                if lemmatized_words:
                    clean_lemma = ' '.join(lemmatized_words)
                    lemmatized.append(clean_lemma.lower())
            except Exception as e:
                self.logger.warning(f"Ошибка лемматизации ключевого слова '{keyword}': {e}")
                lemmatized.append(keyword.lower())  # fallback к оригинальному слову
        
        return lemmatized
    
    def lemmatize_query(self, query: str) -> str:
        """
        Лемматизировать запрос пользователя.
        
        :param query: Исходный запрос пользователя
        :return: Лемматизированный запрос
        """
        try:
            # Разбиваем запрос на слова
            words = query.split()
            lemmatized_words = []
            
            for word in words:
                # Очищаем от пунктуации
                clean_word = word.strip('?!.,()[]{}":;')
                if clean_word:
                    # Получаем лемму через pymorphy3
                    parsed = self.morph.parse(clean_word)
                    if parsed:
                        normal_form = parsed[0].normal_form
                        lemmatized_words.append(normal_form)
                    else:
                        lemmatized_words.append(clean_word)
            
            return ' '.join(lemmatized_words).lower()
        except Exception as e:
            self.logger.warning(f"Ошибка лемматизации запроса: {e}")
            return query.lower()  # fallback к оригинальному запросу


    def parse_llm_json_response(self, response: str, model_class, response_type: str = None):
        """
        Универсальный парсер JSON ответов от LLM с улучшенными паттернами.

        :param response: Ответ LLM в текстовом формате
        :param model_class: Pydantic модель для валидации
        :param response_type: Тип ответа для установки в parsed_data (опционально)
        :return: Экземпляр model_class или None при ошибке
        """

        json_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{[^}]*"search_criteria"[^}]*\{.*?\}[^}]*\}',
            r'\{.*?\}'
        ]

        for pattern in json_patterns:
            try:
                json_match = re.search(pattern, response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1) if pattern.startswith('```') else json_match.group(0)
                    json_str = re.sub(r'```.*?```|```json|```', '', json_str).strip()
                    parsed_data = json.loads(json_str)

                    # Устанавливаем response_type если передан
                    if response_type and isinstance(parsed_data, dict):
                        parsed_data["response_type"] = response_type

                    return model_class(**parsed_data)
            except (json.JSONDecodeError, ValidationError):
                continue
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка при парсинге JSON: {e}")
                continue

        self.logger.warning(f"Не удалось распарсить JSON ответ от LLM")
        self.logger.debug(f"Проблемный ответ LLM: {response[:500]}...")
        return None


# Глобальный экземпляр для переиспользования
text_utils = TextUtils() 