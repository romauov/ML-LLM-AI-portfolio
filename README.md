# Sergei Romanov — Team Lead ML Engineer

**INLINE LLC** · 2 years 7 months

---

## About Me

<table>
<tr>
<td width="50%">

ML-инженер с фокусом на LLM, мультиагентные системы и прогнозирование временных рядов. Руковожу разработкой AI-продуктов для различных индустрий, включая агропром, retail и B2B-продажи. Проектирую архитектуру, управляю командой, выстраиваю CI/CD и контуры тестирования.

</td>
<td width="50%">

ML Engineer focused on LLMs, multi-agent systems, and time series forecasting. Lead AI product development across multiple industries, including agriculture, retail, and B2B sales. Design architecture, manage teams, establish CI/CD pipelines and testing frameworks.

</td>
</tr>
</table>

---

## Tech Stack

**Core:** Python, FastAPI, LangGraph, LangChain, SQLAlchemy, Pydantic

**ML & AI:** Qwen, DeepSeek, Minimax, OpenAI-compatible API, CatBoost, Torch, scikit-learn, ONNX, DVC, MLflow

**Forecasting:** NeuralProphet, TimesFM, SARIMAX, Prophet, ThetaModel, Exponential Smoothing

**Infrastructure:** Docker, PostgreSQL + pgvector, Airflow, Redis, MySQL, ClickHouse, Grafana

**Bot Development:** aiogram 3.x, Telegram Bot API, Google Sheets API

**Other:** Pandas, Polars, MCP (Model Context Protocol)

---

# Projects

---

## 1. AgroPredict — Multi-Agent AI Veterinarian

<table>
<tr>
<td width="50%">

**Роль:** Team Lead ML-инженер  
**Период:** Ноябрь 2024 — настоящее время  
**Заказчик:** ТД ВИК + Сколково  
**Статус:** Представлен на Agravia 2026

Мультиагентный LLM-модуль для промышленного птицеводства и свиноводства. Обеспечивает AI-консультации, интерпретацию лабораторных данных, поиск по ветеринарной базе знаний и расследование инцидентов.

**Архитектура:**
- Роутер запросов → классификация темы (птицеводство/свиноводство/лаборатория/фармацевтика)
- Агент-библиотекарь — RAG-поиск по 200+ источникам
- Агент-фармацевт — справочник 200+ препаратов
- Диагностический контур — 11 болезней птиц + 11 болезней свиней
- Telegram-интерфейс (aiogram) + FastAPI + Web-интеграция

**Ключевые результаты:**
- Руководство командой из 3 разработчиков
- Архитектура мультиагентной системы на LangGraph
- Интеграция с Qwen, DeepSeek, Minimax
- База знаний с pgvector (векторный поиск)
- Eval-контур: deepeval + promptfoo

**[→ agro-vet-ai/](./agro-vet-ai/)**

</td>
<td width="50%">

**Role:** Team Lead ML Engineer  
**Period:** November 2024 — present  
**Client:** TD VIK + Skolkovo  
**Status:** Presented at Agravia 2026 expo

Multi-agent LLM module for poultry and swine farming industries. Provides AI consultations, lab data interpretation, veterinary knowledge base search, and incident investigation.

**Architecture:**
- Query router → topic classification (poultry/swine/lab/pharma)
- Librarian agent — RAG search across 200+ sources
- Pharmacist agent — directory of 200+ drugs
- Diagnostic pipeline — 11 avian + 11 swine diseases
- Telegram interface (aiogram) + FastAPI + Web integration

**Key achievements:**
- Led team of 3 engineers
- Multi-agent architecture with LangGraph
- Integration with Qwen, DeepSeek, Minimax
- pgvector knowledge base with semantic search
- Eval framework: deepeval + promptfoo

**[→ agro-vet-ai/](./agro-vet-ai/)**

</td>
</tr>
</table>

---

## 2. ETL & Price Forecasting

<table>
<tr>
<td width="50%">

**Продукты:** agro.foodbi.ru, foodbi.ru, comida.ai  
**Клиенты:** X5 Group, Вкусно — и точка, Черкизово, Мираторг

ETL- и ML-контур для обработки и прогнозирования цен на мясную и рыбную продукцию. Исторические данные за 20 лет, ~10 ГБ Excel-файлов → 9 млн записей в БД.

**Компоненты:**
- **Forecasting API** ([ai/forecasting/](./ai/forecasting/)) — FastAPI-сервис с ансамблем моделей и RQ-воркерами
- **Monitoring DAGs** ([ai/monitorings/](./ai/monitorings/)) — Airflow-пайплайны классификации и детекции выбросов

**Модели:** Exponential Smoothing, NeuralProphet, ThetaModel, TimesFM (Google), SARIMAX

**Результаты:**
- Точность повышена с 92% до 96% за 6 месяцев
- Количество моделей с точностью < 90% сокращено с 4-5 до 1
- 28 постоянных прогнозов в production

**[→ ai/forecasting/](./ai/forecasting/)** • **[→ ai/monitorings/](./ai/monitorings/)**

</td>
<td width="50%">

**Products:** agro.foodbi.ru, foodbi.ru, comida.ai  
**Clients:** X5 Group, Vkusno — i Tochka, Cherkizovo, Miratorg

ETL and ML pipeline for meat and seafood price forecasting. 20 years of historical data, ~10 GB Excel files → 9M database records.

**Components:**
- **Forecasting API** ([ai/forecasting/](./ai/forecasting/)) — FastAPI service with model ensemble + RQ workers
- **Monitoring DAGs** ([ai/monitorings/](./ai/monitorings/)) — Airflow pipelines for classification and outlier detection

**Models:** Exponential Smoothing, NeuralProphet, ThetaModel, TimesFM (Google), SARIMAX

**Results:**
- Accuracy improved from 92% to 96% over 6 months
- Models below 90% accuracy reduced from 4-5 to 1
- 28 production forecasts running continuously

**[→ ai/forecasting/](./ai/forecasting/)** • **[→ ai/monitorings/](./ai/monitorings/)**

</td>
</tr>
</table>

---

## 3. Sales Accelerator PRO — AI Consultants in Telegram

<table>
<tr>
<td width="50%">

**Платформа:** Meatinfo.ru, Fishretail.ru  
**Тариф:** "Профи"  
**Масштаб:** 50+ ботов

Платформа динамических Telegram-ботов для B2B-продаж. Каждый бот — AI-консультант, отвечающий на коммерческие запросы (ассортимент, цены, доставка, контакты).

**Ключевые особенности:**
- Динамическая генерация роутеров и промптов из Google Sheets
- Мгновенный запуск ботов (< 2 сек)
- LLM с function calling для доступа к прайс-листам
- Веб-интерфейс управления клиентами

**Проекты:**
- [axe-tg-bots/](./axe-tg-bots/) — текущая платформа (FastAPI + aiogram 3.x)
- [tg-bots/](./tg-bots/) — предыдущая версия с жёстко заданными ботами

**[→ axe-tg-bots/](./axe-tg-bots/)** • **[→ tg-bots/](./tg-bots/)**

</td>
<td width="50%">

**Platform:** Meatinfo.ru, Fishretail.ru  
**Tier:** "Pro"  
**Scale:** 50+ bots

Dynamic Telegram bot platform for B2B sales. Each bot is an AI consultant handling commercial inquiries (assortment, pricing, delivery, contacts).

**Key features:**
- Dynamic router and prompt generation from Google Sheets
- Instant bot launch (< 2 seconds)
- LLM with function calling for price list access
- Web management interface for clients

**Projects:**
- [axe-tg-bots/](./axe-tg-bots/) — current platform (FastAPI + aiogram 3.x)
- [tg-bots/](./tg-bots/) — earlier version with hardcoded client bots

**[→ axe-tg-bots/](./axe-tg-bots/)** • **[→ tg-bots/](./tg-bots/)**

</td>
</tr>
</table>

---

## 4. ML Microservice Platform

<table>
<tr>
<td width="50%">

Центральная ML-платформа, содержащая 32 микросервиса с AI-моделями. Единый Flask-gateway с балансировкой через nginx.

Из 32 сервисов мной созданы с нуля: **user_card** (цифровые портреты пользователей), **cluster_recmndr** (кластеризация), **msg_classifier** (классификация сообщений), **chat_helper** (чат-помощник LLM). Остальные ~28 сервисов — поддержка и доработка унаследованного кода.

**Ключевые сервисы:**
- **Рекомендательные системы (BERT, KNN, `PyTorch`, кластеризация)** ⬅️ cluster_recmndr — [`cluster_rec.py`](ai.m16.tech/apps/cluster_recmndr/cluster_rec.py)
- **Классификация сообщений и лидов** ⬅️ msg_classifier
- Генерация коммерческих предложений (text templater) — унаследован
- **Цифровые портреты пользователей** ⬅️ user_card
- **Чат-помощник с LLM** ⬅️ chat_helper
- Трекинг и валидация ответов — унаследован

**Инфраструктура:**
- Docker Compose, GitLab CI, Ansible
- DVC для моделей и датасетов
- Apache Airflow для ETL-пайплайнов
- MLflow для экспериментов

**[→ ai.m16.tech/](./ai.m16.tech/)**

</td>
<td width="50%">

Central ML platform with 32 microservices hosting AI models. Unified Flask gateway with nginx load balancing.

Of the 32 services, I built from scratch: **user_card** (digital user profiles), **cluster_recmndr** (clustering), **msg_classifier** (message classification), **chat_helper** (LLM chatbot). The remaining ~28 services — maintenance and improvement of legacy code.

**Key services:**
- **Recommendation engines (BERT, KNN, `PyTorch`, clustering)** ⬅️ cluster_recmndr — [`cluster_rec.py`](ai.m16.tech/apps/cluster_recmndr/cluster_rec.py)
- **Message and lead classification** ⬅️ msg_classifier
- Commercial proposal generation (text templater) — legacy
- **Digital user profiles** ⬅️ user_card
- **LLM-powered chat assistant** ⬅️ chat_helper
- Response tracking and validation — legacy

**Infrastructure:**
- Docker Compose, GitLab CI, Ansible
- DVC for models and datasets
- Apache Airflow for ETL pipelines
- MLflow for experiment tracking

**[→ ai.m16.tech/](./ai.m16.tech/)**

</td>
</tr>
</table>

---

## 5. Additional Projects

<table>
<tr>
<td width="50%">

**E-mail Bot** ([e-mail-bot/](./e-mail-bot/))
FastAPI-сервис для генерации быстрых ответов на email-рассылки и коммерческих предложений. Интегрирован с платформой Meatinfo для автоматизации обработки входящих запросов.

</td>
<td width="50%">

**Email Bot** ([e-mail-bot/](./e-mail-bot/))
FastAPI service for generating quick email replies to marketing campaigns and commercial proposals. Integrated with Meatinfo platform for automated inquiry handling.

</td>
</tr>
</table>

## 6. Yandex ML Contests

Участие в трёх контестах от Яндекс: AI-агенты (LangGraph), машинный перевод (Gemma-4, NLLB), ML Challenge (головоломки, NVS, LLM inference).

**[→ projects/yandex/](./projects/yandex/)** — отдельный репозиторий: [github.com/romauov/yandex-contests](https://github.com/romauov/yandex-contests)

---

*Portfolio repository: [github.com/romauov/ML-LLM-AI-portfolio](https://github.com/romauov/ML-LLM-AI-portfolio)*
