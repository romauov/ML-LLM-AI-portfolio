"""
Методы генерации текста для рассылок (OpenAI only)

@author Dmitry Abramov
@author Koltashev Yaroslav
"""
import json
import random
from gpt.client import client
from api.schemas import GptTemplaterRequest, GptTemplaterResponse
from gpt.templates import response_examples, templates


def create_prompt_content(json_data):
    """
    Создание содержимого промта для генерации коммерческого предложения

    Args:
        json_data (dict): Данные для генерации предложения

    Returns:
        str: Сформированный промт для LLM
    """

    # Случайные варианты шаблонов для увеличения разнообразия


# Случайный выбор шаблона
    template = random.choice(templates)

    # Случайные примеры формата ответа для разнообразия

    # Случайный выбор примера формата
    response_example = random.choice(response_examples)

    # Extract data with fallback values for all fields
    deal_type = json_data.get('deal_type', 'предложение')
    title = json_data.get('title', 'Коммерческое предложение')
    descr = json_data.get('descr', '')
    category_id = json_data.get('category_id', '')
    type1 = json_data.get('type1', 'продукт')
    type2 = json_data.get('type2', '')
    state = json_data.get('state', '')
    certification = json_data.get('certification', '')
    price = json_data.get('price', 'по запросу') if json_data.get(
        'price') is not None else 'по запросу'
    delivery_info = json_data.get('delivery_info', 'по запросу')
    unitCount = json_data.get('unitCount', '0')
    unit = json_data.get('unit', 'кг')
    user_company_id = json_data.get('user_company_id', 0)
    user_company_name = json_data.get('user_company_name', 'компания')
    author_firstname = json_data.get('author_firstname', 'менеджер')
    author_lastname = json_data.get('author_lastname', '')
    author_position = json_data.get('author_position', '')
    addresses = json_data.get('addresses', 'по запросу')
    email = json_data.get('email', 'по запросу')
    phones = json_data.get('phones', 'по запросу')
    company_descr = json_data.get('company_descr', '')

    # Добавляем случайный фактор в промт для генерации уникальных результатов
    random_factor = random.randint(1, 1000)

    # Create content with template and example
    content = f"""Используй шаблон и пример формата ответа для написания текста и
    заголовка к тексту маркетингового предложения, выдели в заголовке название предлагаемой продукции и релевантность для пользователя,
    например Баранина 12 частей или Мясо говядины.
    Текст для маркетингового предложения: по {deal_type} {type1} {type2} {price} рублей,
    от компании {user_company_name}.
    Адрес склада: {addresses}.
    Доставка от {unitCount} {unit}.
    Контакты:
    Номер телефона: {phones},
    Адрес электронной почты: {email}
    Менеджер: {author_firstname} {author_lastname}.

    ВАЖНО: Верни результат ТОЛЬКО в формате JSON с двумя полями:
    {{"title": "Заголовок коммерческого предложения", "text": "Текст коммерческого предложения"}}

    Пример формата ответа:
    {response_example}

    Шаблон:
    {template}

    Случайный фактор для уникальности: {random_factor}
    """

    return content


async def generate_openai_response(request: GptTemplaterRequest) -> GptTemplaterResponse:
    """
    Генерация текста с помощью OpenAI API

    Args:
        request (GptTemplaterRequest): Объект запроса содержащий данные для генерации

    Returns:
        GptTemplaterResponse: Сгенерированное коммерческое предложение с заголовком и текстом
    """
    try:
        # Convert Pydantic model to dict for easier access
        json_data = request.model_dump()

        # Create prompt content using template approach
        content = create_prompt_content(json_data)

        # Generate response using OpenAI-compatible API (async)
        response = await client.chat.completions.create(
            model=request.model or "google/gemini-2.5-flash-pre-05-20",
            messages=[
                {"role": "system",
                    "content": "Вы помощник по созданию коммерческих предложений. Создавайте профессиональные маркетинговые предложения на основе предоставленных данных."},
                {"role": "user", "content": content}
            ],
            temperature=request.temperature,
            extra_headers={"X-title": "axe-templater"},
            # max_tokens=1000
        )

        # Extract the response text
        response_text = response.choices[0].message.content

        # Try to clean the response text first (remove markdown formatting)
        cleaned_response = response_text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # Remove '```json'
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # Remove '```'
        cleaned_response = cleaned_response.strip()

        # Try to parse as JSON, fallback to plain text if parsing fails
        try:
            result = json.loads(cleaned_response)
            if isinstance(result, dict) and 'title' in result and 'text' in result:
                return GptTemplaterResponse(title=result['title'], text=result['text'])
            else:
                # If JSON doesn't have the expected structure, use the whole response as text
                return GptTemplaterResponse(title="Сгенерированное предложение", text=response_text)
        except json.JSONDecodeError:
            # If response is not valid JSON, try to extract title and text from the response
            # Look for title in the first line
            lines = response_text.strip().split('\n')
            if lines:
                title = lines[0].strip()
                text = '\n'.join(lines[1:]).strip()
                if text:
                    return GptTemplaterResponse(title=title, text=text)
                else:
                    return GptTemplaterResponse(title="Сгенерированное предложение", text=response_text)
            else:
                return GptTemplaterResponse(title="Сгенерированное предложение", text=response_text)

    except Exception as e:
        # In case of error, return a default response with error information
        error_text = f"Ошибка при генерации текста: {str(e)}"
        return GptTemplaterResponse(title="Ошибка", text=error_text)
