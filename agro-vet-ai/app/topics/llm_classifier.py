"""
LLM-классификатор топиков.
"""
import json
import time
from typing import Any, Dict, Optional
from app.llm.prompts import CLASSIFICATION_SYSTEM_PROMPT
from app.llm.providers.llm_provider import LLMProvider
from app.utils.logger import get_logger


def format_dialog_history(dialog_history: list[dict[str, str]]) -> str:
    if not dialog_history:
        return ""
    formatted_history = []
    for msg in dialog_history:
        role = msg["role"]
        content = msg["content"]
        formatted_history.append(f"{role}: {content}")
    return "\n".join(formatted_history)


class LLMTopicClassifier:
    """
    Классификатор на базе LLM. Использует короткие промпты по темам и способен
    возвращать топики, прошедшие порог уверенности.
    """

    def __init__(self):
        self.log = get_logger(__name__)
        self.llm_provider = LLMProvider()
        self.log.info("Инициализация LLM TopicClassifier...")

        self.performance_stats = {
            "total_classifications": 0,
            "llm_classifications": 0,
            "total_time": 0.0,
            "average_time": 0.0,
        }

        # Порог уверенности для фильтрации топиков
        self.confidence_threshold = 0.8

        self.topic_priority = [
            "elisa_test_interpretation",
            "pcr_test_interpretation",
            "avian_disease_diagnosis",
            "swine_disease_diagnosis",
            "librarian_agent",
            "drug_instruction",
            "capabilities",
            "chatter",
            "general",
            "antimicrobial_therapy_handbook",
        ]

        self._precompiled_system_prompt: Optional[str] = None
        self._initialize_topics_and_models()

    def _initialize_topics_and_models(self):
        librarian_books = (
            "Доступ к различным книгам: Antimicrobial Therapy in Veterinary Medicine, 5th Edition; "
            "Practical guide to broiler health management; "
            "Examination of the pharmacokinetic/pharmacodynamic relationships of orally administered antimicrobials "
            "and their correlation with the therapy of various bacterial and mycoplasmal infections in pigs; "
            "Пейсак З. - Болезни свиней"
        )
        self.available_topics = {
            "librarian_agent": librarian_books,
            "elisa_test_interpretation": "Интерпретация результатов ИФА (ELISA)",
            "pcr_test_interpretation": "Интерпретация результатов ПЦР",
            "avian_disease_diagnosis": "Диагностика заболеваний птиц",
            "swine_disease_diagnosis": "Диагностика заболеваний свиней",
            "drug_instruction": "Инструкции по лекарственным препаратам",
            "capabilities": "Вопросы о возможностях бота",
            "chatter": "Приветствия, прощания, благодарности, вопросы о боте, не связанные с ветеринарией",
            "general": "Общие ветеринарные темы"
        }

        self._precompile_prompts()
        self.log.info("LLM TopicClassifier инициализирован.")

    def _precompile_prompts(self):
        try:
            self._precompiled_system_prompt = CLASSIFICATION_SYSTEM_PROMPT
        except Exception as e:
            self.log.error(f"Ошибка предкомпиляции промпта: {e}")
            self._precompiled_system_prompt = "Вы — ИИ-классификатор для ветеринарных вопросов."

    def classify(self, question: str, dialog_history: list[dict[str, str]]) -> Dict[str, Any]:
        start_time = time.time()
        self.performance_stats["total_classifications"] += 1

        # LLM классификация с коротким промптом (топики по порогу)
        self.performance_stats["llm_classifications"] += 1
        try:
            self.log.info(
                f"🧠 [LLMTopicClassifier] Начинаем классификацию вопроса: {question[:50]}...")

            system_prompt = self._get_system_prompt()
            user_prompt = self._build_llm_user_prompt(question, dialog_history)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = self.llm_provider.ask(messages=messages).content

            cleaned = response.strip()
            if "```json" in cleaned:
                s_idx = cleaned.find("```json") + 7
                e_idx = cleaned.find("```", s_idx)
                if e_idx != -1:
                    cleaned = cleaned[s_idx:e_idx].strip()
            elif cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned.strip("`").strip()

            data = json.loads(cleaned)

            # Новый формат: {"topic_name": {"confidence": 0.9, "reasoning": "..."}}
            topics_with_confidence = []
            for topic_name, topic_data in data.items():
                if isinstance(topic_data, dict) and "confidence" in topic_data:
                    confidence_val = float(topic_data.get("confidence", 0.0))
                    reasoning_val = topic_data.get("reasoning", "LLM-классификация")
                    if confidence_val >= self.confidence_threshold:
                        topics_with_confidence.append({
                            "topic": topic_name,
                            "confidence": confidence_val,
                            "reasoning": reasoning_val
                        })

            # Сортируем по уверенности (убывание)
            topics_with_confidence.sort(key=lambda x: x["confidence"], reverse=True)

            if topics_with_confidence:
                # Берем топики выше порога
                if len(topics_with_confidence) == 1:
                    topic_value = topics_with_confidence[0]["topic"]
                    confidence = topics_with_confidence[0]["confidence"]
                    reasoning = topics_with_confidence[0]["reasoning"]
                    is_multiple = False
                else:
                    topic_value = [t["topic"] for t in topics_with_confidence]
                    confidence = topics_with_confidence[0]["confidence"]  # Берем максимальную
                    reasoning = f"Множественная классификация: {len(topics_with_confidence)} топиков"
                    is_multiple = True
            else:
                # Нет топиков выше порога
                topic_value = "chatter"
                confidence = 0.1
                reasoning = "Нет подходящих топиков выше порога уверенности"
                is_multiple = False

            self.log.info(
                f"Классификация завершена. Топик(и): {topic_value}, Уверенность: {confidence}")

            result: Dict[str, Any] = {
                "topic": topic_value,
                "confidence": confidence,
                "reasoning": reasoning,
                "is_multiple": is_multiple,
                "method": "llm_classification",
            }

            self._update_performance_stats(start_time)
            self.log.info(f"✅ Классификация завершена: {result}")
            return result
        except Exception as e:
            self.log.error(f"❌ Ошибка LLM классификации: {e}")
            self.log.error(f"Тип ошибки: {type(e).__name__}")
            import traceback
            self.log.error(f"Трассировка ошибки: {traceback.format_exc()}")
            self._update_performance_stats(start_time)
            return self._build_result("chatter", 0.1, "fallback")

    def get_performance_stats(self) -> Dict[str, Any]:
        stats = self.performance_stats.copy()
        total = stats["total_classifications"]
        if total > 0:
            stats["average_time"] = stats["total_time"] / total
            stats["llm_classification_rate"] = stats["llm_classifications"] / total * 100
        return stats

    def get_available_topics(self) -> Dict[str, Dict[str, Any]]:
        return self.available_topics.copy()

    # ---- Внутренние утилиты
    def _update_performance_stats(self, start_time: float):
        elapsed = time.time() - start_time
        self.performance_stats["total_time"] += elapsed

    def _get_system_prompt(self) -> str:
        return self._precompiled_system_prompt

    def _build_llm_user_prompt(self,
                               question: str,
                               dialog_history: list[dict[str, str]]
                               ) -> str:
        # Короткие описания на тему для быстрого выбора LLM
        topic_hints = {
            "elisa_test_interpretation": "ИФА, ELISA, антитела, титры",
            "pcr_test_interpretation": "ПЦР, PCR, Ct, амплификация",
            "avian_disease_diagnosis": "болезни домашней птицы, симптомы у кур/индюков/уток",
            "swine_disease_diagnosis": "болезни свиней, симптомы у поросят/свиноматок",
            "librarian_agent": "антибиотики, антимикробная терапия, выбор препарата, бройлеры, курицы, птицы, свиньи",
            "drug_instruction": "лекарства, дозировки, инструкции по применению",
            "capabilities": "вопросы о возможностях бота",
            "chatter": "ветеринарные темы, которые не относятся к другим категориям",
            "other": "не ветеринарные темы",
        }

        categories_lines = [f"- {k}: {v}" for k, v in topic_hints.items()]
        categories_text = "\n".join(categories_lines)

        return (
            f"""
            Классифицируй вопрос по темам (верни все подходящие темы с уверенностью).
            Вопрос: "{question}"
            {format_dialog_history(dialog_history)}
            КАТЕГОРИИ:\n{categories_text}
            ТРЕБОВАНИЯ К ОТВЕТУ:
            - Верни строго JSON без пояснений.
            - Для каждого топика укажи уверенность (0-1).
            - Верни в формате: {{"topic": "название_топика", "confidence": 0.0-1.0, "reasoning": "краткое обоснование"}}
            - Включай только топики с уверенностью выше {self.confidence_threshold}
            """
        )

    def _quick_classify(self, question: str) -> str:
        q = question.lower().strip()

        # фразы
        for phrase, topics in self.keyword_phrase_map.items():
            if phrase in q:
                for priority_topic in self.topic_priority:
                    if priority_topic in topics:
                        return priority_topic
                return topics[0]

        # одиночные слова
        for topic in self.topic_priority:
            if topic in self.keyword_word_patterns:
                for _, pattern in self.keyword_word_patterns[topic]:
                    if pattern.search(q):
                        return topic

        return ""

    def _build_result(self, topic: str, confidence: float, method: str) -> Dict[str, Any]:
        method_descriptions = {
            "llm_classification": "LLM-классификация",
            "fallback": "Результат по умолчанию",
        }
        return {
            "topic": topic,
            "confidence": confidence,
            "reasoning": method_descriptions.get(method, method),
            "is_multiple": isinstance(topic, list),
            "method": method,
        }
