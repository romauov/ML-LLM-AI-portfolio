# Web API для Vet-RAG-System

## 🔍 API Endpoints

### GET `/api/up`
- **Назначение**: Проверка работоспособности сервера
- **Ответ**: HTTP 200

```bash
curl http://localhost:81/api/up \
  -H "Authorization: Bearer $API_KEY"
```

### POST `/api/submit`
- **Назначение**: Обработка запросов пользователей
- **Параметры**:
  - `message` (string, optional): Текст сообщения
  - `file_contents` (file, optional): Загружаемый файл
  - `dialog_history` (JSON, optional): История диалога в формате JSON
- **Ответ**: Обработанный ответ в текстовом формате

```bash
# Отправка запроса
curl -X POST http://localhost:81/api/submit \
  -F "message=Какие симптомы у классической чумы свиней?" \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $API_KEY"
```

#### Параметр dialog_history

Для передачи истории диалога в параметре `dialog_history` используйте следующий формат JSON:

```json
{
  "dialog": [
    {
      "role": "user",
      "content": "Текст сообщения пользователя"
    },
    {
      "role": "assistant",
      "content": "Текст ответа ассистента"
    }
  ]
}
```

**Структура dialog_history:**
- `dialog` - массив объектов, каждый из которых представляет собой сообщение в диалоге
- Каждое сообщение содержит:
  - `role` - роль отправителя ("user" для пользователя, "assistant" для ассистента)
  - `content` - текст сообщения

**Порядок сообщений:**
- Сообщения должны быть упорядочены в хронологическом порядке (от самых старых к самым новым)
- Первое сообщение в истории - это самое раннее сообщение в диалоге
- Последнее сообщение перед текущим запросом - это последний ответ ассистента перед текущим запросом
- Текущий запрос (message в POST-запросе) будет обрабатываться с учетом всей предоставленной истории

Пример полного запроса с историей диалога:

```bash
curl -X POST http://localhost:81/api/submit \
  -F "message=Какие симптомы у птичьего гриппа?" \
  -F 'dialog_history={"dialog": [{"role": "user", "content": "Привет"}, {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"}]}' \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $API_KEY"
```

## 🧪 Лабораторные тесты API Endpoints

### POST `/api/process_lab_results`
- **Назначение**: Обработка результатов лабораторных исследований
- **Функция**: Автоматическое определение типа теста (ПЦР или ИФА) и направление к соответствующему обработчику
- **Параметры**:
  - `message` (string, optional): Дополнительное сообщение или вопрос пользователя
  - `lab_results` (string, optional): Текстовая версия лабораторных результатов
  - `file_contents` (file, optional): Файл с результатами лабораторных исследований (PDF, изображение и т.д.)
- **Ответ**: Результат обработки лабораторных результатов или сообщение об ошибке

```bash
# Отправка результатов лабораторных исследований в текстовом виде
curl -X POST http://localhost:81/api/process_lab_results \
  -F "lab_results=Результаты ПЦР-тестирования..." \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $API_KEY"
```

```bash
# Отправка файла с результатами лабораторных исследований
curl -X POST http://localhost:81/api/process_lab_results \
  -F "file_contents=@path_to_lab_results_file.pdf" \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $API_KEY"
```

```bash
# Отправка файла с уточняющим запросом пользователя
curl -X POST http://localhost:81/api/process_lab_results \
  -F "message=Проанализируй результаты ПЦР теста" \
  -F "file_contents=@lab_results.pdf" \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $API_KEY"
```

#### Функциональность классификатора лабораторных тестов:
- **Автоматическое определение типа теста**: Система определяет, является ли файл результатом ПЦР-теста или ИФА-теста
- **Выбор соответствующего обработчика**: Направляет результаты к соответствующему обработчику (ПЦР или ИФА)
- **Интерпретация результатов**: Обеспечивает профессиональную интерпретацию лабораторных данных

Пример обработки файла с ПЦР-тестом:
```bash
curl -X POST http://localhost:81/api/process_lab_results \
  -F "file_contents=@PCR_test_results.pdf" \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $API_KEY"
```

Пример обработки файла с ИФА-тестом:
```bash
curl -X POST http://localhost:81/api/process_lab_results \
  -F "file_contents=@ELISA_test_results.pdf" \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $API_KEY"
```