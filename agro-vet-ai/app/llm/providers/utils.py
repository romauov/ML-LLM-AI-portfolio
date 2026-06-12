import re


def clean_model_response(response: str) -> str:
    """
    Очищает ответ модели от служебных тегов и форматирования

    :param response: Исходный ответ модели
    :return: Очищенный ответ
    """
    if not response:
        return response

    # Удаляем тег </end_of_turn>
    cleaned = re.sub(r'</end_of_turn>', '', response, flags=re.IGNORECASE)

    # Удаляем теги <think> для inline моделей
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)

    # Удаляем лишние пробелы и переносы строк
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    cleaned = cleaned.strip()

    return cleaned
