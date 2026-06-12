from typing import Dict
from app.llm.prompts import get_combined_general_prompts
from app.topics.questions.base import BaseTopic
from app.utils.logger import get_logger


class CombinedGeneral(BaseTopic):
    """
    Объединенный обработчик общих вопросов.

    Этот класс объединяет функциональность трех обработчиков:
    - Capabilities (вопросы о возможностях бота)
    - Chatter (вопросы не по теме)
    - General (общие ветеринарные вопросы)
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "combined_general"
        self.description = "Объединенный обработчик общих вопросов"

    def process(
            self,
            question: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Обработать общий вопрос, используя универсальный подход.
        
        :param question: Вопрос пользователя
        :param context: Дополнительный контекст (опционально)
        :param dialog_history: История диалога пользователя
        :return: Словарь с тэгом и контентом ответа
        """
        try:
            self.logger.info(f"Обрабатываем combined general вопрос: {question[:100]}...")

            # Используем объединенный промпт для всех типов вопросов
            system_prompt, user_prompt = get_combined_general_prompts(question, "")

            # Отправляем запрос к LLM
            messages = self.prompts_to_messages(system_prompt, user_prompt, dialog_history)
            response = self.ask_llm(messages=messages).content

            self.logger.info(f"Получен ответ для combined general вопроса")
            return {"tag": self.topic_name, "content": response}

        except Exception as e:
            self.logger.error(f"Ошибка в CombinedGeneral.process: {e}")
            import traceback
            self.logger.error(f"Полный стек ошибки: {traceback.format_exc()}")
            return {
                "tag": self.topic_name,
                "content": "Извините, произошла ошибка при обработке вашего вопроса."
            }