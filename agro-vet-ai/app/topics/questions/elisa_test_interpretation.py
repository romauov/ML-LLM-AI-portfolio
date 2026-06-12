from typing import Dict
from app.topics.questions.base_image_topic import BaseImageTopic
from app.llm.prompts.elisa_interpretation.analysis import ANALYSIS_PROMPT
from app.llm.prompts.elisa_interpretation.extraction import EXTRACTION_PROMPT
from app.utils.logger import get_logger


class ElisaTestInterpretation(BaseImageTopic):
    """
    Интерпретатор результатов ИФА (ELISA).

    Обработка PDF файлов для
    интерпретации результатов анализов BioChek
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.topic_name = "elisa_test_interpretation"
        self.description = "Интерпретация результатов ИФА (ELISA)"
        self.extraction_prompt = EXTRACTION_PROMPT
        self.analysis_prompt = ANALYSIS_PROMPT

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

