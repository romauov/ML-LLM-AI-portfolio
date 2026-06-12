from typing import Dict
from app.topics.questions.base_image_topic import BaseImageTopic
from app.llm.prompts.pcr_interpretation.system import SYSTEM_PROMPT
from app.llm.prompts.pcr_interpretation.extraction import EXTRACTION_PROMPT
from app.utils.logger import get_logger


class PcrTestInterpretation(BaseImageTopic):
    """
    Интерпретатор результатов ПЦР.

    Обработка текстовых запросов по теме, обработка
    анализов отправленных в виде PDF-документа
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "pcr_test_interpretation"
        self.description = "Интерпретация результатов ПЦР"
        self.extraction_prompt = EXTRACTION_PROMPT
        self.analysis_prompt = SYSTEM_PROMPT

    def process(
            self,
            question: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None,
            file_path: str = None
    ) -> Dict[str, str]:
        return self.process_lab_test(
            question=question,
            extraction_prompt=self.extraction_prompt,
            analysis_prompt=self.analysis_prompt,
            context=context,
            dialog_history=dialog_history,
            file_path=file_path
        )
