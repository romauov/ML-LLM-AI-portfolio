import traceback
from typing import Dict
from app.topics.questions.base_image_topic import BaseImageTopic
from app.topics.questions.elisa_test_interpretation import ElisaTestInterpretation
from app.topics.questions.pcr_test_interpretation import PcrTestInterpretation
from app.topics.questions.lab_test_classifier.system_prompt import LAB_TEST_CLASSIFICATION_SYSTEM_PROMPT
from app.utils.parsers.image_converters import PdfConverter
from app.utils.logger import get_logger


class LabTestClassifier(BaseImageTopic):
    """
    Классификатор лабораторных тестов.

    Определяет тип лабораторного теста (ПЦР или ИФА) по содержимому запроса
    и вызывает соответствующий обработчик.
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "lab_test_classifier"
        self.description = "Классификация лабораторных тестов и вызов соответствующего обработчика"
        self.elisa_handler = ElisaTestInterpretation()
        self.pcr_handler = PcrTestInterpretation()

    def process(
            self,
            question: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None,
            file_path: str = None
    ) -> Dict[str, str]:
        """
        Обработать вопрос и определить тип лабораторного теста.

        :param question: Вопрос пользователя
        :param context: Дополнительный контекст
        :param dialog_history: История диалога пользователя
        :param file_path: Путь к файлу
        :return: Словарь с тэгом и контентом ответа
        """
        try:
            question_preview = str(question)[:100] if question else ""
            self.logger.info(
                f"[LAB_TEST_CLASSIFIER] Обрабатываем лабораторный результат: {question_preview}...")
            self.logger.info(
                f"[LAB_TEST_CLASSIFIER] Получен file_path: {file_path}")
            self.logger.info(
                f"[LAB_TEST_CLASSIFIER] Получен context: {context}")

            # Сначала определяем тип теста (ПЦР или ИФА) на основе содержимого
            test_type = self.classify_test_type(question, context, file_path)

            self.logger.info(
                f"[LAB_TEST_CLASSIFIER] Определенный тип теста: {test_type}")

            # Вызываем соответствующий обработчик в зависимости от типа
            if test_type == "ELISA":
                self.logger.info(
                    "[LAB_TEST_CLASSIFIER] Вызов обработчика ELISA")
                return self.elisa_handler.process(
                    question=question,
                    context=context,
                    dialog_history=dialog_history,
                    file_path=file_path
                )
            elif test_type == "PCR":
                self.logger.info("[LAB_TEST_CLASSIFIER] Вызов обработчика ПЦР")
                return self.pcr_handler.process(
                    question=question,
                    context=context,
                    dialog_history=dialog_history,
                    file_path=file_path
                )
            else:
                # Если тип не определен, возвращаем сообщение об ошибке
                return {
                    "tag": self.topic_name,
                    "content": (
                        "Не удалось определить тип лабораторного теста. "
                        "Пожалуйста, уточните, что вы хотите проанализировать: "
                        "результаты ПЦР-теста или ИФА-теста."
                    )
                }

        except Exception as e:
            self.logger.error(
                f"[LAB_TEST_CLASSIFIER] Ошибка в LabTestClassifier.process: {e}")
            self.logger.error(
                f"[LAB_TEST_CLASSIFIER] Полный стек ошибки: {traceback.format_exc()}")
            return {
                "tag": self.topic_name,
                "content": (
                    "Произошла ошибка при классификации лабораторного теста. "
                    "Рекомендую обратиться к ветеринарному врачу для получения "
                    "профессиональной консультации по результатам анализов."
                )
            }

    def classify_test_type(self, question: str, context: dict = None, file_path: str = None) -> str:
        """
        Определить тип лабораторного теста (ПЦР или ИФА) с помощью LLM.

        :param question: Вопрос пользователя
        :param context: Дополнительный контекст
        :param file_path: Путь к файлу
        :return: Тип теста ("PCR", "ELISA" или "UNKNOWN")
        """
        # Подготовить данные для классификации
        content_to_analyze = question or ""

        if context:
            lab_results = context.get("lab_results", "") if isinstance(
                context, dict) else str(context)
            if lab_results:
                content_to_analyze += f"\n\nЛабораторные данные:\n{lab_results}"

        # Если есть файл, извлекаем данные из него для анализа
        if file_path:
            # Сначала пробуем использовать pdfplumber для извлечения текста
            try:
                pdf_converter = PdfConverter(file_path)
                extracted_data = pdf_converter.convert_with_plumber(file_path)
                if extracted_data:
                    content_to_analyze += f"\n\nДанные из файла:\n{extracted_data}"
            except Exception as e:
                self.logger.error(
                    f"[LAB_TEST_CLASSIFIER] Ошибка при извлечении текста из PDF: {e}")
                # В случае ошибки просто сообщаем пользователю, что файл не может быть обработан
                content_to_analyze += f"\n\n[Ошибка при извлечении данных из файла: {str(e)}]"

        try:
            messages = self.prompts_to_messages(
                system=LAB_TEST_CLASSIFICATION_SYSTEM_PROMPT.format(
                    lab_data=content_to_analyze),
                user="",  # используем системный промт, который уже содержит все инструкции
                dialog_history=[]
            )

            response = self.ask_llm(messages=messages).content.strip().upper()

            # Проверяем корректность ответа
            if response in ["PCR", "ELISA"]:
                return response
            else:
                return "UNKNOWN"

        except Exception as e:
            err_msg = f"[LAB_TEST_CLASSIFIER] Ошибка при классификации с помощью LLM: {e}"
            self.logger.error(err_msg)
            # В случае ошибки LLM, делаем попытку на основе keywords
            return err_msg
