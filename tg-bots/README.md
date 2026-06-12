# Телеграм-боты с ассистентами ЦОП
## Описание репозитория
Чат-боты представляют собой ассистентов ЦОП на базе aiogram и Chat GPT.

## Разворачивание проекта
```
git clone {{GITLAB_URL}}/romauov/tg-bots.git
cd tg-bots
scp -i ~/.ssh/id_rsa.pub -P 22005 ~/your/path/.env username@host:~/tg-bots
docker compose up -d
```
## Структура проекта


```
├── clients                             # пакеты с кастомными модулями клиенов
    └── client1
        ├── conversator_client1.py      # кастомный ассистент для генерации ответов
        ├── file_loader.py              # кастомный модуль загрузки промта
        ├── handlers.py                 # обработчик сообщений aiogram
        ├── keyaboards.py               # клавиатуры aiogram
        └── tools.py                    # функции ассистента
    ├── client2
    ├── ...
├── logs                                # папки с логами и другими вспомогательными файлами
    ├── client1 
    ├── client2
    ├── ...
├── utils                               # пакеты с базовыми модулями
    ├── conversator                     # пакет ассистента для генерации ответов 
        ├── chat_history.py             # функции сохранения и загрузки истории чатов
        ├── conversator.py              # модуль ассистента для генерации ответа
        ├── file_loader.py              # загрузка промта
        └── tools.py                    # функции  ассистента
    ├── opeanai_client.py               # пакет клиента Chat GPT
        └── client.py                   # клиент Chat GPT
    ├── summarizer                      # пакет суммаризатора сообщений
        └── summarizer.py               # суммаризатор сообщений
    ├── charge_logging.py               # логирование затрат Chat GPT
    └── settings.py                     # секреты проекта
├── .env                                # файл с переменными окружения (отсутствует в репозитории)
├── bot.py                              # запуск ботов
├── docker-compose.yaml                 
├── Dockerfile
├── README.md
└── requirements.txt
```

