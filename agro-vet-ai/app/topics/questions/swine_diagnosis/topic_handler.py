from typing import Dict
import yaml
import glob
from app.topics.questions.base import BaseTopic
from app.topics.questions.swine_diagnosis.system_prompt import SWINE_DISEASE_SYSTEM_PROMPT
from app.utils.search_engine.engine import create_search_engine
from app.utils.logger import get_logger


class SwineDiseasesDiagnosis(BaseTopic):
    """
    Обработчик вопросов о диагностике заболеваний свиней.

    Этот класс обрабатывает вопросы, связанные с диагностикой заболеваний
    свиней, включая симптомы, клинические признаки и методы диагностики.
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "swine_disease_diagnosis"
        self.description = "Диагностика заболеваний свиней"
        self.path = "knowledge/diagnostics/swine_diseases/list"
        self.search_engine = create_search_engine(self.path)
        self.diseases_data = self._load_diseases_data()

    def _load_diseases_data(self):
        """Загрузить данные о заболеваниях из YAML файлов."""
        diseases = {}

        for file_path in glob.glob(f"{self.path}/*.yml"):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    # Получаем имя заболевания из ключа первого уровня
                    disease_key = list(data.keys())[0]
                    disease_name = data[disease_key].get('disease_name', '').strip()
                    if disease_name:
                        # Используем disease_name как ключ для поиска
                        diseases[disease_name] = data[disease_key]
            except Exception as e:
                self.logger.error(f"Ошибка при загрузке файла {file_path}: {e}")
                
        return diseases

    def _get_disease_info(self, disease_name: str) -> str:
        """
        Получить информацию о заболевании из загруженных данных.
        
        :param disease_name: Название заболевания
        :return: Строка с информацией о заболевании
        """
        # Ищем заболевание по частичному совпадению имени
        for loaded_name, disease_data in self.diseases_data.items():
            if disease_name.lower() in loaded_name.lower() or loaded_name.lower() in disease_name.lower():
                # Собираем нужные разделы
                sections = []
                
                if 'clinical_findings' in disease_data:
                    sections.append(f"Клинические признаки:\n{disease_data['clinical_findings']}")
                    
                if 'postmortem_findings' in disease_data:
                    sections.append(f"Патологоанатомические изменения:\n{disease_data['postmortem_findings']}")
                    
                if 'differential_diagnosis' in disease_data:
                    sections.append(f"Дифференциальная диагностика:\n{disease_data['differential_diagnosis']}")
                
                return "\n\n".join(sections)
                
        return ""

    def process(
            self,
            question: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None
    ) -> Dict[str, str | None]:
        """
        Обработать вопрос о диагностике заболеваний свиней.

        :param question: Вопрос пользователя
        :param context: Дополнительный контекст (опционально)
        :param dialog_history: История диалога пользователя
        :return: Словарь с тэгом и контентом ответа
        """
        try:
            self.logger.info(f"Обрабатываем вопрос о заболеваниях свиней: {question[:100]}...")

            relevant_content = self.relevant_content(question)
            context_text = "\n\n".join(relevant_content) if relevant_content else ""

            system_prompt = SWINE_DISEASE_SYSTEM_PROMPT
            user_prompt = (
                f"<additional_information>\n{context_text}\n</additional_information>\n\n"
                f"<user_question>\n{question}\n</user_question>"
            )

            messages = self.prompts_to_messages(system_prompt, user_prompt, dialog_history)
            response = self.ask_llm(messages=messages).content

            self.logger.info(f"Получен ответ о заболеваниях свиней")
            return {"tag": self.topic_name, "content": response, "context": context_text}

        except Exception as e:
            self.logger.error(f"Ошибка в SwineDiseasesDiagnosis.process: {e}")
            import traceback
            self.logger.error(f"Полный стек ошибки: {traceback.format_exc()}")
            return {
                "tag": self.topic_name,
                "content": (
                    "Произошла ошибка при обработке вопроса о заболеваниях свиней. "
                    "Рекомендую срочно обратиться к ветеринарному врачу для осмотра животного "
                    "и постановки точного диагноза. При подозрении на АЧС немедленно уведомите "
                    "ветеринарные службы! Изолируйте больных животных от остального поголовья "
                    "и примите карантинные меры."
                )
            }

    def relevant_content(self, query: str) -> list:
        """
        Получить релевантный контент из базы знаний.

        :param query: Запрос для поиска
        :return: Список найденного контента
        """
        # Проверяем, что search_engine доступен
        if not self.search_engine:
            return []
            
        # Используем search_engine для поиска наиболее релевантных заболеваний
        search_results = self.search_engine.search(query, top_n=3)
        
        content_list = []
        for disease_name, score in search_results:
            # Получаем информацию о заболевании из YAML файлов
            disease_info = self._get_disease_info(disease_name)
            if disease_info:
                content_list.append(f"Заболевание: {disease_name}\n{disease_info}")
                
        return content_list
