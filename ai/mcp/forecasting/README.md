## Forecasting MCP server


### Инструменты:
- Поставить задачу на планирование `POST /predict`
- Проверить статус задачи `GET /status/{task_id}`
- Получение  результатов прогноза `GET /result/{task_id}`

### Подключение сервера Docker:
сборка:

```docker build -t mcp/forecasting .```

Claude desktop:

В claude_desktop_config.json надо добавить:
```
{
  "mcpServers": {
    "forecasting": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        '--rm',
        "--mount", f"type=bind,src=/agent_workspace,dst=/agent_workspace",
        "mcp/forecasting",
        "--url", "{forecasting_server_url}",
        "--port", "{forecasting_server_port}",
        "--user", "{user_name}",
        "--password", "{user_password}"
      ]
    }
  }
}
```
При подключении к удаленному серверу прогнозирования используйте `--url http://147.45.104.19 --port 81`

При подключении к серверу прогнозирования на локальной машине `--url http://host.docker.internal --port port`

Для прогнозирования нужен доступ к excel файлу с временным рядом, для этого монтируется часть файловой системы в контейнер, где лежит excel файл


### Примеры:
Пример подключения через python код:
```python
from mcp import StdioServerParameters
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
user = "..."
password = "..."


StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            '--rm',
            "--mount", f"type=bind,src={str(Path(ROOT_DIR, 'agent_workspace').absolute())},dst=/agent_workspace",
            "mcp/forecasting",
            "--url", "http://host.docker.internal",
            "--port", "81",
            "--user", user,
            "--password", password
        ],
    )
```

Пример промпта агенту:

    Сделай прогноз временного ряда по excel файлу /agent_workspace/api_predictions.xlsx, на листе с названием beef. 
    Колонка с датой называется date, а прогнозируемая колонка prod.
    Прогноз сделай на 12 шагов, при этом используй только быстрые модели. Не ограничивай исторические данные.
    
    Прогноз занимает время, делай между проверками статуса задачи паузы в 10 секунд.
    
    Результат прогноза напиши текстом и скажи какая ошибка по метрике была при прогнозе.