# ai.m16.tech

AI-модели и демонстрационная площадка для них

## Оглавление 

[Развёртывание проекта](#развёртывание-проекта)

[Запуск сервисов](#запуск-сервисов)

[Запуск pylint](#запуск-pylint)

[Хранение моделей и датасетов в dvc](#хранение-моделей-и-датасетов-в-dvc)
* [Сохранение файлов](#сохранение-файлов)
* [Обновление файлов](#обновление-файлов)
* [Получение файлов](#получение-файлов)
* [Переключение между версиями](#переключение-между-версиями)

[Добавление сервисов flask](#добавление-сервисов-flask)

[Добавление пакетов python](#добавление-пакетов-python)

[Команды](#команды)

[Подключение к продакшн базе axe и clickhouse](#подключение-к-продакшн-базе-axe-и-clickhouse)

[Airflow](#airflow)
* [Общие сведения](#общие-сведения)
* [Добавление пакетов](#добавление-пакетов)
* [Авторизация в Airflow](#авторизация-в-airflow)
* [Airflow на локалке](#airflow-на-локалке)
* [Краткая инструкция по добавлению нового Pipeline](#краткая-инструкция-по-добавлению-нового-pipeline)
* [Добавление Pipeline](#добавление-pipeline)

[Label Studio](#работа-с-label-studio)
* [Настройка проектов](#настройка-проектов)
* [Общие сведения о Label studio](#использование-label-studio)
* [Детекция изображений](#детекция-изображений)

## Развёртывание проекта
```sh
$ git clone {{GIT_REPO_URL}}
$ cd ai.m16.tech
$ ./bin/init
```

## Запуск сервисов

```sh
docker-compose up -d
```
Адрес: http://localhost:5000/

## Запуск pylint
```sh
./bin/pylint
```

## Хранение моделей и датасетов в dvc
Большие файлы и бинарные не храним в git, т.к. он предназначен для версионирования исходных кодов
либо для небольших бинарных файлов.

Если файлы больше 5Мб, то следует хранить их с использованием DVC (хранилище, которое размещено в облачном s3 сервисе)

Мы используем s3-хранилище от компании Timeweb.

Подробная информация по dvc (https://dvc.org/doc)
### Сохранение файлов

```sh
# Добавить файл или директорию в dvc
./bin/dvc add apps/demo/data

# Сохранить информацию о добавленном файле в git
git add apps/demo/data.dvc apps/demo/data/.gitignore
git commit -m "Add raw demo/data"

# Отправка файлов dvc на сервер
./bin/dvc push
```

### Обновление файлов
```sh
# Добавить измененные файлы
./bin/dvc add apps/demo/data

# Сохранить информацию о измененном файле в git
git commit apps/demo/data.dvc -m "Dataset updates"

# Отправка файлов dvc на сервер
./bin/dvc push
```

### Получение файлов
```sh
./bin/dvc pull
```

### Переключение между версиями
```sh
git checkout <...>
./bin/dvc checkout
```

## Добавление сервисов flask

1. Создать директорию apps/new_service
2. В директории создать файлы `__init__.py` и routes.py. Пример файлов в apps/demo
    ```python
    # __init__.py
    import os
    import sys
    from flask import Blueprint
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    blueprint = Blueprint('new_service', __name__)
    # pylint: disable=cyclic-import
    # pylint: disable=wrong-import-position
    from . import routes
    
    # routes.py
    from . import blueprint
    @blueprint.route('/new_service', methods=['GET'])
    def demo():
        return "new_service"
    ```
3. В файле apps/server/server.py добавить регистрацию сервиса
    ```python
    from new_service import blueprint as new_service_blueprint
    app.register_blueprint(new_service_blueprint)
    ```
4. Модели и датасеты хранить в директории apps/new_service/data.

## Добавление пакетов python

1. Вписываем библиотеки в requirements.txt, придерживаемся текущего оформления
2. Проверка пакетов до релиза
   ```sh
   # Консоль контейнера python с установкой пакетов
   ./bin/app-req
   # Запуск сервисов с установкой пакетов
   ./bin/run-req
   ```
3. Обновить версию образа в файле .env
   ```
   ML_SERVICES_PYTHON_IMAGE_TAG=1
   ```
   
## Команды

| команда        | описание                                       |
|----------------|------------------------------------------------|
| ./bin/app-gpu  | консоль контейнера python с поддержкой gpu     |
| ./bin/app-req  | консоль контейнера python с установкой пакетов |
| ./bin/dvc      | контроль версий для моделей и датасетов        |
| ./bin/init     | инициализация проекта                          |
| ./bin/pylint   | линтер python файлов                           |
| ./bin/run-prod | запуск сервисов на проде                       |
| ./bin/run-req  | запуск сервисов с установкой пакетов           |
| ./bin/ui-lint  | линтер js файлов                               |
| ./bin/db-prod  | подключение к базе                             |


## Подключение к продакшн базе axe и clickhouse
 
```sh
# скопировать конфиг
cp config/.env-default config/.env

# Добавить имя пользователя и пароль для ssh акса
vi config/.env

# выполнить команду после запуска контейнера
./bin/db-prod
```
## Airflow
### Общие сведения
Airflow используется для построения Pipeline на основе DAG (Directed acyclic graph), который включает в себя изолированные друг от друга операторы/задачи, которые будут выполняться последовательно/параллельно. DAG выполняется через определенные промежутки времени. С помощью airflow можно автоматизировать загрузку и подготовку данных, автоматизировать обучение модели.

Документация: https://airflow.apache.org/docs/apache-airflow/stable/

Airflow развернут в специальном контейнере - ./airflow_docker


### Добавление пакетов
Для добавления пакетов в контейнер airflow необходимо обновить файл ./airflow_docker/requirements.txt

Пример: 

```
# knn_recommendations
pyspark==3.5.0
```

### Авторизация в Airflow
Airflow доступен по ссылке: {{AIRFLOW_URL}}

Логин: {{AIRFLOW_USER}}

Пароль: {{AIRFLOW_PASSWORD}}

Для авторизации в airflow:

Логин: airflow

Пароль: airflow

### Airflow на локалке

После запуска контейнеров на локалке Airflow доступен по url: http://localhost:8080/


### Краткая инструкция по добавлению нового Pipeline
1. Поместить DAG в ./airflow/dags
2. Добавить SQL скрипты в /apps/lib
3. Добавить пакеты в ./airflow_docker/requierements.txt
4. Создать директорию для обмена файлами ./apps/file_hosting/<project_name>
5. Запустить DAG в графическом интерфейсе

### Добавление Pipeline

Cкрипты для выгрызок из баз данных размещать в ./apps/lib

DAG'и размещаются в ./apps/airflow/dags, в эту директорию нельзя помещать дополнительные скрипты для DAGов

В качестве хост папки использовать ./apps/file_hosting/<project_name>. Через эту папку производится обмен данными между контейнерами app и airflow.

Пример сохранения данных:

```python
from lib.user_stat_db import user_stat

df = pd.DataFrame(user_stat(), columns=COLUMN_NAMES)
df.to_csv('/app/apps/file_hosting/<project_name>/<file_name>.csv')
```

Файлы доступны в ai.m16.tech по следующему пути

```python
import pandas as pd

df = pd.read_csv('/apps/file_hosting/<project_name>/<file_name>.csv')
```

Информация по работе с DAG:
1. DAG состоит из операторов/задач, которые изолированы
2. Между операторами/задачами для передачи параметров, небольших данных можно использовать XCom, для передачи больших датасетов - сохранять данные в одной задаче и загружать в другую
3. Инициализировать дату выполнения - предыдущим днём. Если веб сервису необходимы данные из директории - запустить выполнение DAG вручную из интерфейса
4. В базовом случае правило для активации - успешное выполнение предыдущих задач
5. Задачи необходимо связывать оператором >>
6. Для задач с Python скриптами лучше использовать @task декоратор
7. Интервалы между автоматическим запуском можно задать с помощью предустановок airflow/выражения cron. Предпочтительно использовать cron
    * Редактор выражений cron: https://crontab.guru/
    * Предустановки airflow: https://airflow.apache.org/docs/apache-airflow/1.10.1/scheduler.html#dag-runs

Примеры DAG можно найти в apps/airflow/dags/tsop_pipeline.py

Примеры связывания задач:
```
Последовательное выполнение задач:
path >> data_checker_task >> user_ratios_task >> emails_task

Параллельное выполнение задач emails_task, maillisted_users_task, tsop_spamers_task, после чего задачи выполняются последовательно
path >> user_ratios_task >> [emails_task, maillisted_users_task, tsop_spamers_task] >> data_checker_task >> model_fit_task
```

Пример выполнения одной задачи:
```python
from datetime import datetime

from airflow.decorators import dag, task

from lib.user_stat_db import email_db, user_stat

@dag(schedule="0 0 * * *", start_date=datetime(2023, 11, 1))
def tsop_data_preparer():
    @task
    def data_loader():
        data = user_stat()
        df = pd.DataFrame(data)
        path = '/app/apps/file_hosting/<project_name>/userStat.csv'
        df.to_csv(path)

    path = data_loader()

    path
tsop_data_preparer()
```

## Работа с Label Studio 

Разметка изображений доступна по ссылке: ({{LABEL_STUDIO_URL}})

### Настройка проектов 

1. На главной странице указать имя и описание проекта, выбрать распределение задач

2. Выбрать шаблон разметки, удалить существующие классы, добавить свои 

3. Импортировать изображения в проект

### Использование Label Studio

1. Открыть проект 

2. Выбрать изображение для разметки 

3. Под изображением пронумерованы классы, для их выбора нужно нажать на клавиатуре цифру класса/нажать на него курсором

4. На панели разметки доступны горячие клавиши: 

| хоткей         | действие                                       |
|----------------|------------------------------------------------|
| v              | выделить метки                                 |
| h              | движение по изображению с помощью мыши         |
| b              | режим разметки                                 |
| e              | удалить часть аннотации  - стерка              |
| ctrl + enter   | сохранить изменения                            |

### Детекция изображений

1. Открыть проект Detection 

2. Выбрать изображение 

3. Нажать 1 для разметки камней

4. При неправильной разметке нажать на рамку, в появившемся меню нажать на корзину   

![Снимок экрана от 2023-03-24 17-26-46.png](./Снимок экрана от 2023-03-24 17-26-46.png)

5. Для корректирования размеров рамки: 
    - Нажать на рамку
    - Изменить размеры
    - При выделении следующего камня, будет автоматический выход из режима редактирования 

6. ctrl + enter - сохранить изменения

7. Для экспорта изображений перейти на страницу проекта, Export -> YOLO

