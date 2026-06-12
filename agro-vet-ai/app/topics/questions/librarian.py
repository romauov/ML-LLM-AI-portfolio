import traceback
from typing import Dict

from app.agents.librarian.librarian_agent import LibrarianAgent
from app.topics.questions.base import BaseTopic
from app.utils.logger import get_logger


class Librarian(BaseTopic):

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "librarian_agent"
        self.description = "Библиотекарь с доступами к разным книгам"
        self.agent_config = {"recursion_limit": 100}

    def process(
            self,
            question: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None,
            file_path=None
    ) -> Dict[str, str]:
        try:
            self.logger.info(f"Бибилиотекарь обрабатывает вопрос пользователя: {question[:100]}...")

            graph = LibrarianAgent(context=context, dialog_history=dialog_history).build()
            user_message = {"messages": [("user", question)]}
            message = graph.invoke(user_message, config=self.agent_config)['messages'][-1]

            self.logger.info(f"Получен ответ от библиотекаря")
            return {
                "tag": self.topic_name,
                "content": message.content,
                "context": message.context,
                "context_images": message.context_images,
            }

        except Exception as e:
            self.logger.error(f"Ошибка в Librarian.process: {e}")
            self.logger.error(f"Полный стек ошибки: {traceback.format_exc()}")
            return {
                "tag": self.topic_name,
                "content": "Извините, произошла ошибка при обработке вопроса"
            }
