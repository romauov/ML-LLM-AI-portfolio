"""
Модуль промптов для LLM системы.

Этот модуль содержит разделенные промпты:
- system: системные промпты и общие инструкции
- specialized: специализированные промпты для конкретных задач
- test: промпты для тестирования
"""

from app.llm.prompts.system import (
    COMMON_INSTRUCTIONS,
    SYSTEM_PROMPT_BASE,
    CLASSIFICATION_SYSTEM_PROMPT,
    get_classification_user_prompt,
)

from app.llm.prompts.specialized import (
    # Промпты для диагностики заболеваний птиц
    # AVIAN_DISEASE_FUNCTION_CALLING_INSTRUCTIONS,

    # Промпты для интерпретации тестов
    ELISA_TEST_SYSTEM_PROMPT,
    ELISA_TEST_USER_PROMPT,
    get_elisa_test_prompts,

    # Промпты для общих вопросов
    GENERAL_QUESTION_SYSTEM_PROMPT,
    GENERAL_QUESTION_USER_PROMPT,
    get_general_question_prompts,

    # Промпты для возможностей и разговоров не по теме
    CAPABILITIES_SYSTEM_PROMPT,
    CHATTER_SYSTEM_PROMPT,
    get_capabilities_prompts,
    get_chatter_prompts,

    # Промпты для объединенного обработчика общих вопросов
    get_combined_general_prompts,
)

from .test import (
    TEST_ANSWER_PROMPT,
    TEST_EVALUATION_CRITERIA,
)

__all__ = [
    # Системные промпты
    'COMMON_INSTRUCTIONS',
    'SYSTEM_PROMPT_BASE',
    'CLASSIFICATION_SYSTEM_PROMPT',
    'get_classification_user_prompt',

    # Специализированные промпты
    # 'AVIAN_DISEASE_FUNCTION_CALLING_INSTRUCTIONS',
    # 'SWINE_DISEASE_FUNCTION_CALLING_INSTRUCTIONS',
    'ELISA_TEST_SYSTEM_PROMPT',
    'ELISA_TEST_USER_PROMPT',
    'get_elisa_test_prompts',
    'GENERAL_QUESTION_SYSTEM_PROMPT',
    'GENERAL_QUESTION_USER_PROMPT',
    'get_general_question_prompts',
    'CAPABILITIES_SYSTEM_PROMPT',
    'CHATTER_SYSTEM_PROMPT',
    'get_capabilities_prompts',
    'get_chatter_prompts',
    'get_combined_general_prompts',

    # Тестовые промпты
    'TEST_ANSWER_PROMPT',
    'TEST_EVALUATION_CRITERIA',
]
