# Пайплайн обработки мониторингов

## Описание

Проект представляет собой автоматизированную систему обработки файлов мониторингов цен на продовольственные товары. Построен на базе **Apache Airflow 3.2.0** с использованием **CeleryExecutor** для распределённого выполнения задач.

Поддерживаемые типы мониторингов:
- **meat** — мясные продукции (meatinfo.ru)
- **fishes** — рыбные продукции (fishretail.ru)
- **milk** — молочные продукции (milknet.biz)
- **egg** — мониторинг яиц (meatinfo.ru)
- **fruit** — плодоовощные продукции (fruitinfo.biz)

## Архитектура

Система состоит из двух основных компонентов:

### Apache Airflow
Оркестратор пайплайнов, разворачиваемый через Docker Compose:
- **airflow-apiserver** — API сервер (порт 8080)
- **airflow-scheduler** — планировщик задач
- **airflow-dag-processor** — обработчик DAG'ов
- **airflow-worker** — Celery worker для выполнения задач
- **airflow-triggerer** — обработчик триггеров
- **flower** — мониторинг Celery (порт 5555)
- **postgres** — мета-база данных Airflow
- **redis** — брокер сообщений для Celery

### App Worker
Docker-контейнер с приложением для обработки файлов. Выполняет команды, запускаемые из Airflow DAG'ов через `CustomDockerOperator`.

## Пайплайн обработки

### Excel/CSV пайплайн (на примере meat)

```
wait_file_appear → collect_files → extract_excel/csv → classify → outliers → save_db
```

| Шаг | Описание |
|-----|----------|
| `wait_file_appear` | Sensor, ожидает появления файлов с нужным расширением |
| `collect_files` | Собирает список файлов для обработки |
| `extract_excel/csv` | Извлекает и нормализует данные из файла |
| `classify` | Предсказывает `product_type` с помощью ML-модели (только meat) |
| `outliers` | Детекция выбросов цен с использованием исторических данных (только meat) |
| `save_db` | Загрузка результатов в MySQL |

### Поддерживаемые форматы
- **Excel**: `.xlsx`, `.xls`
- **CSV**: `.csv`

## Структура проекта

```
├── app/                          # Основное приложение
│   ├── common/                   # Общие модули
│   │   ├── extractor.py          # Извлечение даты и округа из имени файла
│   │   ├── processor.py          # Обработка цен
│   │   └── models/               # Общие модели (outliers detection)
│   ├── docker_commands/          # CLI команды для Docker-контейнеров
│   │   ├── make_process_file.py  # Обработка файла мониторинга
│   │   ├── make_classification.py# Классификация product_type
│   │   ├── make_outliers_detection.py # Детекция выбросов
│   │   └── make_save_results.py  # Сохранение результатов в БД
│   ├── meat/                     # Обработка мясных мониторингов
│   │   ├── predictor/            # ML модель для предсказания product_type
│   │   ├── processor/            # Процессоры Excel/CSV
│   │   └── utils/                # Утилиты и данные
│   ├── fishes/                   # Обработка рыбных мониторингов
│   │   ├── caviar/               # Икра
│   │   ├── fish/                 # Рыба
│   │   ├── seafood/              # Морепродукты
│   │   ├── semiprocessed/        # Полуфабрикаты
│   │   └── shrimp/               # Креветки
│   ├── milk/                     # Обработка молочных мониторингов
│   ├── egg/                      # Обработка мониторингов яиц
│   ├── fruit/                    # Обработка плодоовощных мониторингов
│   └── utils/                    # Общие утилиты (БД, логирование, настройки)
├── dags/                         # Airflow DAG'и
│   ├── meat_pipline.py           # Пайплайн для мяса (Excel + CSV)
│   ├── fish_pipline.py           # Пайплайн для рыбы
│   ├── milk_pipline.py           # Пайплайн для молока
│   ├── egg_pipline.py            # Пайплайн для яиц
│   ├── fruit_pipline.py          # Пайплайн для фруктов
│   ├── constants.py              # Константы (пути, таймауты, расширения)
│   └── utils.py                  # Утилиты для DAG'ов
├── plugins/                      # Airflow плагины
│   ├── custom_docker_operator.py # Плагин CustomDockerOperator
│   └── operators/
│       └── docker_opearator.py   # Кастомный DockerOperator с XCom поддержкой
├── config/                       # Конфигурация Airflow
│   └── airflow.cfg
├── data/                         # Временные данные
├── logs/                         # Логи Airflow
├── .env                          # Переменные окружения (не в репозитории)
├── .env.local                    # Локальные переменные окружения
├── docker-compose.yaml           # Оркестрация сервисов
├── Dockerfile                    # Образ app-worker
├── Makefile                      # Команды для управления Docker
├── requirements-app-worker.txt   # Зависимости приложения
└── requirements-dev.txt          # Зависимости для разработки
```

## Быстрый старт

### 1. Подготовка окружения

Создайте файл `.env` на основе `.env.local` с необходимыми переменными окружения:

```bash
# Обязательные переменные
POSTGRES_PASSWORD=...
AIRFLOW__CORE__FERNET_KEY=...
AIRFLOW__API_AUTH__JWT_SECRET=...
AIRFLOW__API_AUTH__JWT_ISSUER=...
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=admin
REDIS_PASSWORD=...
FLOWER_USER=admin
FLOWER_PASSWORD=...

# Папки мониторингов (пути на хост-машине)
MONITORING_NEW_FOLDER=/path/to/monitoring/new
MONITORING_PROCESSED_FOLDER=/path/to/monitoring/processed
MONITORING_ERRORS_FOLDER=/path/to/monitoring/errors
TMP_FILES_FOLDER=/path/to/tmp
```

### 2. Инициализация Airflow

```bash
make docker_init
```

### 3. Запуск сервисов

```bash
make docker_up
```

### 4. Остановка сервисов

```bash
make docker_stop
```

### 5. Полная очистка (включая данные)

```bash
make docker_clean_up_all_data
```

## Веб-интерфейсы

| Сервис | URL | Описание |
|--------|-----|----------|
| Airflow | http://localhost:8080 | Веб-интерфейс Airflow |
| Flower | http://localhost:5555 | Мониторинг Celery workers |

## Как это работает

1. Файлы мониторингов помещаются в папку `MONITORING_NEW_FOLDER/{type}/` (например, `meat/`, `milk/`)
2. Airflow DAG обнаруживает новые файлы каждые час (`schedule="0 * * * *"`)
3. Файл проходит через пайплайн: извлечение → классификация → детекция выбросов → сохранение в БД
4. Успешно обработанные файлы перемещаются в `MONITORING_PROCESSED_FOLDER/`
5. Файлы с ошибками перемещаются в `MONITORING_ERRORS_FOLDER/`

## Зависимости

### Приложение (app-worker)
- pandas, openpyxl, xlrd — обработка Excel/CSV
- scikit-learn, onnxruntime, nltk — ML классификация
- scipy, statsmodels, linearmodels — детекция выбросов
- SQLAlchemy, PyMySQL — работа с БД
- click — CLI интерфейс

### Разработка
- apache-airflow==3.2.0
- apache-airflow-providers-docker==4.5.5


