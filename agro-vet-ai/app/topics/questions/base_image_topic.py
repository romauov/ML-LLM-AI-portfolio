import base64
import io
import traceback
from abc import abstractmethod
from typing import Dict

from pdf2image import convert_from_path

from config.config import Config
from app.topics.questions.base import BaseTopic
from app.llm.providers.vsegpt import VseGPTProvider
from app.utils.settings import secrets as s


class BaseImageTopic(BaseTopic):
    """
    Абстрактный класс обработки вопросов топиков c файлами.
    """

    def __init__(self):
        super().__init__()
        self.vsegpt_provider = VseGPTProvider(
            api_key=s.vsegpt_api_key,
            base_url=s.vsegpt_base_url
        )

    def process_lab_test(
            self,
            question: str,
            extraction_prompt: str,
            analysis_prompt: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None,
            file_path: str = None
    ) -> Dict[str, str]:
        """
        Обработать вопрос о лабораторном тесте.

        :param question: Вопрос пользователя
        :param extraction_prompt: Промт для извлечения данных
        :param analysis_prompt: Промт для анализа данных
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
                f"[{self.topic_name.upper()}_TEST] Получен file_path: {file_path}")
            self.logger.info(
                f"[{self.topic_name.upper()}_TEST] Получен context: {context}")

            # --- Обработка файла или контекста ---
            analysis_data = None

            # Сначала проверяем файл, если он есть
            if file_path and file_path.lower().endswith('.pdf'):
                analysis_data = self.extract_pdf_data(
                    file_path, extraction_prompt)
                if not analysis_data:
                    return {"tag": self.topic_name, "content": "Не удалось извлечь данные из PDF документа."}
            # Затем проверяем контекст
            elif context:
                # Извлекаем лабораторные данные из контекста
                lab_results = context.get("lab_results", "") if isinstance(
                    context, dict) else str(context)
                if lab_results:
                    analysis_data = self.extract_context_data(
                        lab_results, extraction_prompt)

            # --- Анализ извлеченных данных ---
            if analysis_data:
                system_prompt = analysis_prompt
                user_message = f"Данные для анализа:\n{analysis_data}\n\nВопрос пользователя: {question}"

                if dialog_history:
                    user_message += f"\n\nИстория диалога:\n{dialog_history}"

                messages = self.prompts_to_messages(
                    system_prompt, user_message, dialog_history)
                response = self.ask_llm(messages=messages).content
                return {"tag": self.topic_name, "content": response}
            else:
                # Если нет ни PDF данных, ни данных из контекста, возвращаем ошибку
                if file_path:
                    return {
                        "tag": self.topic_name,
                        "content": "Не удалось извлечь данные из PDF документа."
                    }
                else:
                    return {
                        "tag": self.topic_name,
                        "content": "Не обнаружено лабораторных данных для анализа. Пожалуйста, предоставьте текст с лабораторными данными через контекст или PDF файл с результатами."
                    }

        except Exception as e:
            self.logger.error(
                f"[{self.topic_name.upper()}_TEST] Ошибка в {self.__class__.__name__}.process: {e}")
            self.logger.error(
                f"[{self.topic_name.upper()}_TEST] Полный стек ошибки: {traceback.format_exc()}")
            return {
                "tag": self.topic_name,
                "content": (
                    f"Произошла ошибка при обработке {self.topic_name} запроса. "
                    "Рекомендую обратиться к ветеринарному врачу для получения "
                    "профессиональной консультации по результатам анализов."
                )
            }

    @staticmethod
    def prompts_and_image_to_messages(
            system: str,
            user: str = None,
            dialog_history: list[dict] = None,
            base64_image: str = None
    ) -> list[dict]:
        messages = [{"role": "system", "content": system}]
        if dialog_history:
            messages.extend(dialog_history)

        if not base64_image:
            messages.append({"role": "user", "content": user})
        else:
            user_content = []
            if user:
                user_content.append({"type": "text", "text": user})
            user_content.append({"type": "image_url", "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"}})
            messages.append({"role": "user", "content": user_content})

        return messages

    def extract_pdf_data(
            self,
            file_path: str,
            extraction_prompt: str
    ) -> str:
        """
        Универсальный метод извлечения данных из PDF файла с использованием VLM.

        :param file_path: Путь к PDF файлу
        :param extraction_prompt: Промт для извлечения данных
        :return: Извлеченные данные в виде строки
        """
        try:

            ocr_model = Config.from_yaml().llm_models.ocr_model

            # Конвертируем PDF в изображения
            images = convert_from_path(file_path, dpi=300, fmt='jpeg')
            all_extracted_data = []

            # Обрабатываем каждую страницу PDF
            for page_num, image in enumerate(images, 1):
                try:
                    # Сохраняем изображение в буфер памяти
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='JPEG', quality=95)
                    img_buffer.seek(0)
                    base64_image = base64.b64encode(
                        img_buffer.read()).decode("utf-8")

                    self.logger.info(
                        f"[BASE_IMAGE_TOPIC] Отправляем запрос к VLM для страницы {page_num}")

                    # Извлекаем данные страницы с помощью VLM
                    messages = self.prompts_and_image_to_messages(
                        system=extraction_prompt,
                        base64_image=base64_image
                    )
                    extracted_page_data = self.ask_llm(
                        messages=messages, model=ocr_model).content

                    if s.mode == 'dev':
                        self.logger.info(
                            f"[BASE_IMAGE_TOPIC] Результат страницы {page_num}: {str(extracted_page_data)[:100]}...")

                    if extracted_page_data:
                        all_extracted_data.append(
                            f"Страница {page_num}:\n{extracted_page_data}")

                    self.logger.info(
                        f"[BASE_IMAGE_TOPIC] Обработана страница {page_num} из {len(images)}")

                except Exception as page_error:
                    self.logger.error(
                        f"❌ [BASE_IMAGE_TOPIC] Ошибка обработки страницы {page_num}: {page_error}")
                    continue

            if not all_extracted_data:
                return None

            # Комбинируем все извлеченные данные
            combined_data = "\n\n".join(all_extracted_data)
            self.logger.info(
                f"✅ [BASE_IMAGE_TOPIC] Данные извлечены, общий размер: {len(combined_data)} символов")
            return combined_data

        except Exception as e:
            self.logger.error(
                f"[BASE_IMAGE_TOPIC] Ошибка извлечения PDF данных: {e}")
            self.logger.error(
                f"[BASE_IMAGE_TOPIC] Полный стек: {traceback.format_exc()}")
            return None

    def extract_context_data(self, lab_results_text: str, extraction_prompt: str) -> str:
        """
        Извлекает и структурирует данные из текста лабораторных результатов,
        используя указанный EXTRACTION_PROMPT.

        :param lab_results_text: Текст с лабораторными результатами
        :param extraction_prompt: Промт для извлечения данных
        :return: Структурированные данные для дальнейшей передачи в LLM
        """
        try:
            self.logger.info(
                f"[CONTEXT_EXTRACTION] Обработка текстовых данных из контекста")

            # Используем EXTRACTION_PROMPT для обработки текста
            # с аналогичной логикой, как при обработке PDF
            system_prompt = extraction_prompt
            user_message = f"Текст с лабораторными данными:\n\n{lab_results_text}"

            # Формируем сообщения для LLM
            messages = self.prompts_to_messages(
                system_prompt, user_message, [])

            # Вызываем LLM для извлечения и структурирования данных
            extracted_data = self.ask_llm(messages=messages).content

            self.logger.info(
                f"✅ [CONTEXT_EXTRACTION] Данные извлечены, размер: {len(extracted_data)} символов")
            return extracted_data

        except Exception as e:
            self.logger.error(
                f"[CONTEXT_EXTRACTION] Ошибка извлечения данных из контекста: {e}")

            self.logger.error(
                f"[CONTEXT_EXTRACTION] Полный стек: {traceback.format_exc()}")
            return None
