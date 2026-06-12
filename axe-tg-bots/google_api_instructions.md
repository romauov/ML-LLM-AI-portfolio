### Инструкция по настройке Google Sheets API и созданию сервисного аккаунта

#### Шаг 1: Создание проекта в Google Cloud Console
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Если у вас нет проекта:
   - Нажмите на выпадающий список проектов в верхней панели
   - Выберите "Новый проект"
   - Введите название проекта (например, "My Sheets API Project")
   - Нажмите "Создать"

#### Шаг 2: Включение Google Sheets API
1. В панели навигации слева выберите "API и сервисы" > "Библиотека"
2. В поиске введите "Google Sheets API"
3. Выберите "Google Sheets API" из результатов
4. Нажмите "Включить"

#### Шаг 3: Создание сервисного аккаунта
1. В панели навигации слева выберите "API и сервисы" > "Учетные данные"
2. Нажмите "Создать учетные данные" в верхней части страницы
3. Выберите "Сервисный аккаунт"
4. Заполните форму:
   - Имя сервисного аккаунта (например, "sheets-api-access")
   - ID сервисного аккаунта (оставьте по умолчанию)
   - Описание (необязательно, например, "Для доступа к Google Sheets")
5. Нажмите "Создать и продолжить"

#### Шаг 4: Настройка прав доступа
1. В разделе "Предоставить этому сервисному аккаунту доступ к проекту":
   - Выберите роль "Редактор" (или более узкую, если нужно)
   - Можно выбрать "Basic" > "Editor" или "Project" > "Editor"
2. Нажмите "Продолжить"
3. В следующем окне можно добавить пользователей, которые будут управлять аккаунтом (пока можно пропустить)
4. Нажмите "Готово"

#### Шаг 5: Создание ключа доступа
1. В списке сервисных аккаунтов найдите только что созданный
2. Нажмите на email сервисного аккаунта (вида `sheets-api-access@your-project-id.iam.gserviceaccount.com`)
3. Перейдите на вкладку "Ключи"
4. Нажмите "Добавить ключ" > "Создать новый ключ"
5. Выберите тип ключа "JSON"
6. Нажмите "Создать"
7. Автоматически скачается JSON-файл с ключами - сохраните его в безопасное место!

#### Шаг 6: Предоставление доступа к таблице
1. Откройте нужную Google Таблицу в браузере
2. Нажмите "Настройки доступа" (кнопка "Поделиться" в правом верхнем углу)
3. В поле "Добавьте пользователей или группы" введите email вашего сервисного аккаунта (тот, что был в скачанном JSON-файле, поле "client_email")
4. Выберите уровень доступа (как минимум "Редактор" или "Просмотр", в зависимости от ваших нужд)
5. Нажмите "Отправить"

#### Содержимое JSON-файла
Скачанный файл будет содержать примерно следующее:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "123...abc",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "sheets-api-access@your-project-id.iam.gserviceaccount.com",
  "client_id": "123...456",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

#### Проверка работы
Вы можете проверить работу API с помощью этого кода:
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

SERVICE_ACCOUNT_FILE = 'google_credentials.json'  # Ваш ключ
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)

# Загрузка по имени листа (вместо sheet_id)
sheet_name = 'Sheet1'  # Укажите название листа
result = service.spreadsheets().values().get(
    spreadsheetId=table_id,
    range=f"'{sheet_name}'!A:Z"  # Диапазон
).execute()

values = result.get('values', [])
if not values:
    print('Данные не найдены')
else:
    prompt_table = pd.DataFrame(values[1:], columns=values[0])
```
