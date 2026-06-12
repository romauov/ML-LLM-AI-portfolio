# vet-rag-system

# AgroBot: Интеллектуальный Telegram-бот для ветеринаров

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![ChatGPT](https://img.shields.io/badge/ChatGPT-1A1A1A?style=for-the-badge&logo=openai&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Colab](https://img.shields.io/badge/Colab-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white)

AgroBot — это умный Telegram-бот, разработанный для ветеринарных клиник и специалистов.
Он помогает быстро находить информацию о лекарственных препаратах, их составе и способе применения в инструкциях к препаратам, а также отвечает на вопросы, используя технологии Llama Index или GPT.

---

## Основные функции:
- **Интеграция с Telegram**: Простая авторизация и удобный интерфейс для пользователей.
- **База знаний**: Хранение и обработка информации о препаратах, вакцинации и других медицинских данных.
- **Искусственный интеллект**: Генерация ответов на основе базы знаний и обработки пользовательских вопросов.
- **Работа с PostgreSQL**: Надёжное хранение и быстрый доступ к данным.
- **Масштабируемая архитектура**: Лёгкость в добавлении новых функций и расширении возможностей.
- **Описание работы бота для тестирования - здесь!** - {{GITLAB_URL}}/agropredict/vet-rag-system/-/issues/32


## Полезные ссылки
[**База знаний (ветеринария и лекарственные препараты)**]({{GITLAB_URL}}/agropredict/vet-rag-system/-/wikis/%D0%91%D0%B0%D0%B7%D0%B0-%D0%B7%D0%BD%D0%B0%D0%BD%D0%B8%D0%B9)
<br><br>
[![Тестирование обработки инструкции gpt-4o-mini](https://img.shields.io/badge/Обработка_инструкции_gpt_4o_mini-Colab-blue?style=for-the-badge&logo=google-colab)](https://colab.research.google.com/drive/1PT97SderDjpTdESBM0mLr25rVR5eSVnD#scrollTo=fzw4OHIgBYTx)

# **GitLab CI/CD**
  - CI/CD-конвейер автоматически запускается только при внесении изменений в ветку `main` в удаленном репозитории.
  - Развертывание происходит в Docker-кластере на сервере Agropredict.
  - Адрес Телеграм-бота при развертывании с помощью GitLab CI/CD: @veterinary_assistant_bot
  - Для редактирования переменных окружения нужно перейти в настройки GitLab CI/CD: `Settings > CI/CD > Variables`
# Запуск проекта

## **Запуск в Docker-окружении**
При развертывании в Docker-окружении база данных будет инициализирована автоматически с помощью дампа, сохраненного в scripts/schema_and_data.dump.

### **1. Запуск в автономном режиме (вне кластера).**
```bash
1. Скачать удаленный репозиторий:
  $ git clone https://<username>:<token>@lab.inline-ltd.ru/agropredict/vet-rag-system.git
  $ cd vet-rag-system

2. Создать файл .env на основе .env_example и указать значения переменных окружения: 
  $ cp .env_example .env

3. Запустить сервисы из Compose-файла:
  $ docker-compose up -d --build postgres_rag app_rag
```

### **2. Запуск в Swarm-режиме (в кластере).**
```bash
1. Скачать удаленный репозиторий:
  $ git clone https://<username>:<token>@lab.inline-ltd.ru/agropredict/vet-rag-system.git
  $ cd vet-rag-system

2. Создать файл .env на основе .env_example и указать значения переменных окружения: 
  $ cp .env_example .env

3. Выполнить сборку Docker-образов:
  $ docker build -f Dockerfile.postgres -t postgres_rag_image .
  $ docker build -f Dockerfile.rag -t app_rag_image .

4. Запустить сервисы в кластере Docker Swarm:
  $ docker stack deploy -c docker-compose.swarm.yaml rag
```

## **Запуск без использования Docker**
### 1. Перейти в виртуальную среду Python

Если виртуальной среды нет, создайте её:
```bash
python3 -m venv venv
```
Теперь активируйте её:

**Linux/MacOS:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate
```

---

## 2. Установить зависимости Python
Убедитесь, что в виртуальной среде установлены все необходимые зависимости:
```bash
pip install -r requirements.txt
```

---

## 3. Запустить PostgreSQL

## 4. Выполнить миграции

```bash
alembic upgrade head
```

---

## 5. Запустить Telegram-бота
Запустите основное приложение:
```bash
python3 main.py
```

## 6. Переменные окружение
* `MODE` — тип окружения приложения:

  * `dev` — режим разработки
      - выводит отладочную информацию с указанием категории вопросов
  * `prod` — режим эксплуатации (без лишней информации)
---


# Проверка работы
- После запуска вы можете проверить работу бота, отправив `/start` в Telegram.
- В случае ошибок убедитесь, что:
  - Контейнер с PostgreSQL работает (`docker ps`).
  - Переменные окружения (`.env`) настроены правильно.


# Создать миграцию

```bash
alembic revision -m "Creat table users"
```

Файл новой миграции будет создан автоматически, перейти внести нужные правки

![image](/uploads/61484c78e3517bcf7525b8ca2d80d8a5/image.png)

Запустить

```bash
alembic upgrade head
```

если  приложение в контейнере

```bash
docker exec -it vet-rag-system_bot_1 alembic upgrade head
```

# Генератор Markdown-файлов для базы данных

Данный модуль предназначен для генерации Markdown-файлов на основе таблицы из базы данных.
Папка модуля: `/rag/markdown_fragments`

## Запуск скрипта

Чтобы запустить скрипт из корневой директории проекта, выполните следующие шаги:

1. Выполните пункты `1-4` из раздела `Запуск проекта локально`.

2. Перейдите в корневую директорию проекта.

3. Отредактируйте файл `/rag/markdown_fragments/main.py`, указав необходимые параметры для вызываемых методов.

5. Запутите модуль в коммандной строке:
   ```bash
   python3 -m rag.markdown_fragments.main
   ```

# Парсер каталога препаратов ВИК

Данный модуль предназначен для наполнения базы данных на основе каталога препаратов ВИК.
<br>
Папка модуля: `/rag/tokenizer`

## Запуск скрипта

Чтобы запустить скрипт из корневой директории проекта, выполните следующие шаги:

1. Выполните пункты `1-4` из раздела `Запуск проекта локально`.

2. Перейдите в корневую директорию проекта.

3. Отредактируйте файл `/rag/tokenizer/main.py`, указав путь к к PDF-файлу с каталогом препаратов и папке для сохранения инструкций относительно корневой папки проекта.

5. Запутите модуль в коммандной строке:
   ```bash
   python3 -m rag.tokenizer.main
   ```

## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin {{GITLAB_URL}}/agropredict/vet-rag-system.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

- [ ] [Set up project integrations]({{GITLAB_URL}}/agropredict/vet-rag-system/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.
- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)
