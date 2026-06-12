# Спецификация MCP инструмента extract_document

## Назначение

Извлечение текста из документов (PDF, DOCX) с лабораторными результатами, договорами и другими файлами через VseGPT API.

## Основной use case

**Сценарий**: Ветеринар получил результаты лабораторных исследований в PDF или DOCX формате и хочет, чтобы AI-ассистент проанализировал их.

**Workflow**:
1. Ветеринар загружает файл с результатами
2. AI-ассистент вызывает `extract_document` с путем к файлу
3. MCP сервер отправляет файл в VseGPT API
4. Возвращается текст в markdown формате
5. AI-ассистент анализирует результаты и обновляет расследование

## MCP Tool Definition

```python
Tool(
    name="extract_document",
    description=(
        "Извлечение текста из документов (PDF, DOCX) с использованием VseGPT API. "
        "Используйте для обработки лабораторных результатов, договоров, отчетов. "
        "PDF документы обрабатываются с OCR, что обеспечивает высокое качество "
        "распознавания таблиц и структурированных данных."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Абсолютный путь к файлу (PDF или DOCX)"
            },
            "model": {
                "type": "string",
                "enum": ["auto", "extract-text", "pdf-ocr"],
                "default": "auto",
                "description": (
                    "Модель для извлечения текста. "
                    "'auto' - автоматический выбор (рекомендуется), "
                    "'extract-text' - базовая модель (PDF, DOCX), "
                    "'pdf-ocr' - OCR модель только для PDF"
                )
            },
            "return_markdown": {
                "type": "boolean",
                "default": True,
                "description": "Возвращать результат в markdown формате (рекомендуется)"
            }
        },
        "required": ["file_path"]
    }
)
```

## Ответ инструмента

### Успешный ответ

```json
{
  "success": true,
  "text": "Извлеченный текст в markdown формате...",
  "metadata": {
    "filename": "IFA.pdf",
    "file_size_bytes": 94029,
    "model_used": "utils/pdf-ocr-1.0",
    "pages_processed": 1,
    "has_images": true,
    "images_count": 1
  }
}
```

### Ответ с ошибкой

```json
{
  "success": false,
  "error": "Формат файла не поддерживается. Поддерживаемые форматы: PDF, DOCX",
  "metadata": {
    "filename": "data.xlsx",
    "error_code": "UNSUPPORTED_FORMAT"
  }
}
```

## Логика автоматического выбора модели

```python
def select_model(file_path: str, user_choice: str) -> str:
    if user_choice != "auto":
        # Пользователь явно указал модель
        return MODEL_MAP[user_choice]

    # Автоматический выбор
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return "utils/pdf-ocr-1.0"  # OCR для лучшего качества таблиц
    elif ext == ".docx":
        return "utils/extract-text-1.0"
    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")
```

## Обработка ошибок

### 1. Rate Limiting (429 или множественные 500)

```python
# Автоматический retry с экспоненциальной задержкой
max_retries = 3
for attempt in range(max_retries):
    try:
        result = call_api()
        break
    except RateLimitError:
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
        else:
            raise
```

### 2. Неподдерживаемый формат

```python
SUPPORTED_FORMATS = {".pdf", ".docx"}

if ext not in SUPPORTED_FORMATS:
    return error_response(
        f"Формат {ext} не поддерживается. "
        f"Поддерживаемые форматы: {', '.join(SUPPORTED_FORMATS)}"
    )
```

### 3. Файл не найден

```python
if not Path(file_path).exists():
    return error_response(f"Файл не найден: {file_path}")
```

### 4. Кириллица в имени файла

```python
from transliterate import translit

def sanitize_filename(filename: str) -> str:
    """Транслитерация кириллицы в латиницу."""
    if any('\u0400' <= c <= '\u04FF' for c in filename):
        # Есть кириллица - транслитерируем
        return translit(filename, 'ru', reversed=True)
    return filename
```

## Форматирование ответа для пользователя

```python
def format_response(api_response: dict, filename: str) -> str:
    """Форматирование ответа для отображения пользователю."""

    output = f"# Извлечен текст из документа: {filename}\n\n"
    output += "## Содержимое документа\n\n"
    output += api_response["text"]
    output += "\n\n---\n\n"

    # Метаданные
    if "usage_info" in api_response:
        info = api_response["usage_info"]
        output += f"**Обработано страниц:** {info.get('pages_processed', 'N/A')}\n"
        output += f"**Размер файла:** {info.get('doc_size_bytes', 0) / 1024:.1f} KB\n"

    return output
```

## Интеграция с agent workflow

В `AGENTS.md` добавить инструкцию:

```markdown
### 5. extract_document - Извлечение текста из документов

**Когда использовать**:
- Ветеринар прислал PDF или DOCX с лабораторными результатами
- Нужно извлечь текст из договора, отчета, инструкции
- Результаты анализов представлены в виде файла

**Пример использования**:
```
extract_document(
    file_path="/path/to/lab_results.pdf"
)
```

**После извлечения**:
1. Сохранить результаты в `05_lab_results.md`
2. Провести поиск в базе знаний по выявленным патогенам
3. Обновить гипотезы
```

## Ограничения

1. **Rate Limit**: 1 запрос в секунду к VseGPT API
   - Решение: автоматические retry с задержками

2. **Размер файла**: Неизвестно точное ограничение
   - Рекомендация: файлы до 10 MB
   - Для больших файлов - возвращать предупреждение

3. **Форматы**: Только PDF и DOCX
   - XLSX не поддерживается
   - Для Excel - рекомендовать сохранить как PDF

4. **Изображения**:
   - По умолчанию не возвращаем base64 изображений (экономим трафик)
   - При необходимости можно добавить параметр `return_images`

## Безопасность

1. **Валидация пути к файлу**:
   ```python
   # Проверка на path traversal
   file_path = Path(file_path).resolve()
   if not file_path.is_relative_to(ALLOWED_DIR):
       raise SecurityError("Доступ запрещен")
   ```

2. **API ключ**:
   - Использовать тот же OPENAI_API_KEY из .env
   - Не передавать ключ в ответе

3. **Логирование**:
   ```python
   logger.info(
       f"Извлечение текста из файла: {filename} "
       f"(размер={file_size}, модель={model})"
   )
   ```

## Тестирование

### Unit тесты

```python
async def test_extract_pdf_auto():
    result = await extract_document("test_documents/IFA.pdf")
    assert result["success"] is True
    assert "IBD" in result["text"]
    assert result["metadata"]["model_used"] == "utils/pdf-ocr-1.0"

async def test_extract_docx():
    result = await extract_document("test_documents/test_document.docx")
    assert result["success"] is True
    assert "Договор" in result["text"]

async def test_unsupported_format():
    result = await extract_document("test.xlsx")
    assert result["success"] is False
    assert "не поддерживается" in result["error"]
```

### Integration тесты

```python
async def test_mcp_extract_document():
    # Вызов через MCP
    response = await mcp_client.call_tool(
        "extract_document",
        {"file_path": "/path/to/test.pdf"}
    )
    assert response is not None
```

## Метрики

Логировать для мониторинга:
- Количество запросов
- Используемые модели
- Размеры файлов
- Время обработки
- Ошибки (rate limit, unsupported format, etc.)
