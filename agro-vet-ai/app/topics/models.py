"""
Pydantic модели для topics модуля.
Содержит модели данных для различных топиков системы.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel


class DrugSearchCriteria(BaseModel):
    """Критерии поиска лекарственных препаратов"""
    trade_name: List[str] = []
    generic_name: List[str] = []
    drug_class: List[str] = []
    target_animals: List[str] = []
    symptoms_keywords: List[str] = []
    dosage_form: List[str] = []
    route: List[str] = []


class DrugLLMResponse(BaseModel):
    """Ответ LLM для обработки вопросов о лекарственных препаратах"""
    response_type: Literal["keywords", "final_answer"]
    search_criteria: Optional[DrugSearchCriteria] = None
    field_analysis: str = ""
    answer: Optional[str] = None
    confidence_reasoning: str = ""
    confidence_score: float = 0.0
    completeness_score: float = 0.0