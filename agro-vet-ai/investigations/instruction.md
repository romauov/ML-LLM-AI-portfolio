# Инструкция по интеграции проекта VetRetro в другое приложение

## 1. Извлечение компонентов проекта

### Основные компоненты для интеграции:
1. **MCP сервер** (отдельный сервис)
2. **Инструменты расследования** (файловые операции)
3. **Ветеринарный агент** (с промптами)
4. **Управление расследованиями** (файловая структура)

## 2. Интеграция MCP сервера

MCP сервер должен запускаться отдельно от основного приложения:
- Запускается на фиксированном порту (например, 8765)
- Обеспечивает доступ к базе знаний через инструменты:
  - `vet_search` - семантический поиск
  - `vet_sources` - список источников
  - `source_info` - информация об источнике
  - `get_pages` - извлечение страниц
  - `extract_document` - извлечение документов

## 3. Извлечение и интеграция веб-бэкенда

### Вариант A: Интеграция как библиотека

Создайте в вашем проекте модуль `vetretro`:

#### 1. Извлеките основные классы:

**Службы:**
```python
# vetretro/services.py
from app.services.investigation_manager import InvestigationManager
from app.services.mcp_client import VetRetroMCPClient
```

**Инструменты:**
```python
# vetretro/tools.py
from app.tools.mcp_tools import create_mcp_tools
from app.tools.investigation_tools import create_investigation_tools
from app.tools.todo_tool import TodoWriteTool
```

**Агент:**
```python
# vetretro/agent.py
from app.agents.vet_agent import get_vet_agent_executor, create_investigation_agent
from app.agents.prompts import get_vet_agent_prompt
```

#### 2. Создайте сервис расследования:

```python
# vetretro/investigation_service.py
from app.services.investigation_manager import InvestigationManager
from app.services.mcp_client import VetRetroMCPClient
from app.agents.vet_agent import create_investigation_agent
import asyncio

class VetInvestigationService:
    def __init__(self, mcp_url: str, workspace_path: str):
        self.mcp_client = VetRetroMCPClient(url=mcp_url)
        self.investigation_manager = InvestigationManager(workspace_path=workspace_path)

    async def create_investigation(
        self, 
        farm_name: str, 
        animal_type: str, 
        problem_type: str, 
        description: str,
        llm_config: dict
    ):
        # Создать расследование
        investigation = self.investigation_manager.create_investigation(
            farm_name=farm_name,
            animal_type=animal_type,
            problem_type=problem_type,
            description=description
        )
        
        # Создать агента для расследования
        agent_executor = create_investigation_agent(
            investigation_id=investigation.id,
            mcp_client=self.mcp_client,
            investigation_manager=self.investigation_manager,
            animal_type=animal_type
        )
        
        return investigation.id, agent_executor

    async def process_query(self, investigation_id: str, query: str):
        # Загрузить существующий агент
        agent_executor = create_investigation_agent(
            investigation_id=investigation_id,
            mcp_client=self.mcp_client,
            investigation_manager=self.investigation_manager
        )
        
        # Обработать запрос
        result = await agent_executor.ainvoke({"input": query})
        return result
```

### Вариант B: Интеграция как API-сервис

#### 1. Подключите маршруты к вашему основному приложению:

```python
# vetretro/api.py
from fastapi import APIRouter, Depends
from app.api.investigations import investigations_router
from app.api.chat import chat_router

vetretro_router = APIRouter(prefix="/vetretro")

# Подключите оригинальные маршруты
vetretro_router.include_router(investigations_router)
vetretro_router.include_router(chat_router)
```

#### 2. Инициализируйте сервисы в вашем основном приложении:

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from vetretro.api import vetretro_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация VetRetro сервисов
    # (как показано в предыдущей инструкции)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(vetretro_router, prefix="/api")
```

## 4. Настройка конфигурации

#### 1. Добавьте настройки VetRetro:

```python
# config.py
from pydantic_settings import BaseSettings

class VetRetroSettings(BaseSettings):
    mcp_url: str = "http://localhost:8765"
    investigations_dir: str = "./agent-workspace/investigations"
    agent_workspace_dir: str = "./agent-workspace"
    
    # Настройки LLM
    llm_api_base: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "qwen/qwen3-next-80b-a3b-instruct"

vetretro_settings = VetRetroSettings()
```

#### 2. Инициализируйте глобальные сервисы:

```python
# services.py
from app.services.mcp_client import VetRetroMCPClient
from app.services.investigation_manager import InvestigationManager
from config import vetretro_settings

def init_vetretro_services():
    mcp_client = VetRetroMCPClient(url=vetretro_settings.mcp_url)
    investigation_manager = InvestigationManager(
        workspace_path=vetretro_settings.investigations_dir
    )
    return mcp_client, investigation_manager
```

## 5. Использование в вашем приложении

### Вариант использования в контроллере:

```python
# controllers/veterinary_controller.py
from fastapi import APIRouter, HTTPException
from typing import Optional
from vetretro.investigation_service import VetInvestigationService
from config import vetretro_settings

router = APIRouter()
vet_service: Optional[VetInvestigationService] = None

@router.on_event("startup")
async def startup_event():
    global vet_service
    vet_service = VetInvestigationService(
        mcp_url=vetretro_settings.mcp_url,
        workspace_path=vetretro_settings.investigations_dir
    )

@router.post("/investigations")
async def create_investigation(
    farm_name: str,
    animal_type: str,
    problem_type: str,
    description: str
):
    if not vet_service:
        raise HTTPException(status_code=500, detail="Vet service not initialized")
    
    investigation_id, _ = await vet_service.create_investigation(
        farm_name=farm_name,
        animal_type=animal_type,
        problem_type=problem_type,
        description=description,
        llm_config={}
    )
    
    return {"investigation_id": investigation_id}

@router.post("/investigations/{investigation_id}/query")
async def query_investigation(investigation_id: str, query: str):
    if not vet_service:
        raise HTTPException(status_code=500, detail="Vet service not initialized")
    
    result = await vet_service.process_query(investigation_id, query)
    return result
```

## 6. Зависимости

#### 1. Добавьте в requirements вашего проекта:

```txt
# Из mcp-server
mcp>=0.9.0
asyncpg>=0.29.0
pgvector>=0.2.0
openai>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Из web-backend
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
langchain>=0.1.0
langchain-openai>=0.0.5
langserve>=0.0.30
langchain-classic  # Важно!
```

#### 2. Установите langchain-classic

```bash
pip install langchain-classic
```

## 7. Файловая структура

#### 1. Создайте структуру workspace:

```
your_project/
├── agent-workspace/
│   ├── investigations/     # Файлы расследований
│   ├── templates/          # Шаблоны
│   ├── instructions/       # Инструкции по типам проблем
│   └── examples/           # Примеры расследований
```

#### 2. Или настройте на другую директорию:

```python
# В настройках
investigations_dir = "/path/to/vet/investigations"
```

## 8. Запуск и интеграция

1. **Запустите MCP сервер** отдельно:
   ```bash
   cd mcp-server && python run_http.py
   ```

2. **Добавьте компоненты VetRetro** в ваше основное приложение

3. **Используйте API** или **интегрируйте напрямую** через сервисы

4. **Обеспечьте доступ** к ветеринарной базе данных (PostgreSQL+pgvector)

Таким образом, VetRetro становится частью вашего основного приложения, предоставляет API для ветеринарных расследований и использует внешний MCP сервер для доступа к знаниям.