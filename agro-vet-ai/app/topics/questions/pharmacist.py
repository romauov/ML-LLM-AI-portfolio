import traceback
from typing import Dict, Any

from app.agents.pharmacist.pharmacist_agent import PharmacistAgent
from app.topics.questions.base import BaseTopic
from app.utils.logger import get_logger
from app.utils.langchain_message_converters import from_openai_format

class Pharmacist(BaseTopic):

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "pharmacist_agent"
        self.description = "Фармацевт с доступом к базе данных препаратов и инструкций по их применению"
        self.agent_config = {"recursion_limit": 100}

    def process(
            self,
            question: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None,
            file_path=None
    ) -> Dict[str, Any]:
        try:
            self.logger.info(f"Фармацевт обрабатывает вопрос пользователя: {question[:100]}...")

            agent = PharmacistAgent(context=context, dialog_history=dialog_history)
            graph = agent.build()

            # Конвертируем dialog_history в LangChain messages
            # Пропускаем служебные сообщения (tool calls, tool results)
            history_messages = []
            if dialog_history:
                for msg in dialog_history:
                    if msg.get("role") in ("tool",) or "tool_calls" in msg:
                        continue
                    if not isinstance(msg.get("content"), str) or not msg["content"]:
                        continue
                    try:
                        history_messages.append(from_openai_format(msg))
                    except Exception as e:
                        self.logger.warning(f"Не удалось конвертировать сообщение из истории: {e}")

            # Добавляем текущий вопрос пользователя
            history_messages.append(("user", question))

            user_message = {"messages": history_messages}
            message = graph.invoke(user_message, config=self.agent_config)['messages'][-1]

            self.logger.info(f"Получен ответ от фармацевта")

            result = {
                "tag": self.topic_name,
                "content": message.content,
                "context": message.context,
            }

            # Добавляем запросы на файлы, если они есть
            if agent.file_requests:
                result["file_requests"] = agent.file_requests
                self.logger.info(f"Запрошены файлы инструкций: {len(agent.file_requests)}")

            return result

        except Exception as e:
            self.logger.error(f"Ошибка в Pharmacist.process: {e}")
            self.logger.error(f"Полный стек ошибки: {traceback.format_exc()}")
            return {
                "tag": self.topic_name,
                "content": "Извините, произошла ошибка при обработке вопроса"
            }