import logging
from typing import Union
from enum import Enum

import requests
from requests.auth import HTTPBasicAuth
from pydantic import BaseModel
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, CallToolResult


class ForecastingTools(str, Enum):
    CREATE = 'create_task'
    GET_STATUS = 'get_task_status'
    GET_RESULT = 'get_task_result'


class CreateTask(BaseModel):
    file: str
    sheet_name: str
    date_name: str
    series_name: str
    forecasting_steps: int
    use_only_light_models: bool = True
    year_limit: Union[int, None] = None
    train_n_epochs: Union[int, None] = None


class GetTaskStatus(BaseModel):
    task_id: str


class GetTaskResult(BaseModel):
    task_id: str


def make_request(method, url, data=None, files=None, auth=None):
    try:
        if files:
            files = {'file': open(files, 'rb')}

        response = requests.request(
            method,
            url,
            auth=auth,
            headers={'accept': 'application/json'},
            data=data,
            files=files,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        )


def create_task(
        url, auth,
        file: str, sheet_name: str, date_name: str, series_name: str, forecasting_steps: int,
        use_only_light_models: bool = True, year_limit: Union[int, None] = None, train_n_epochs: Union[int, None] = None
) -> str:
    """постановки задачи прогнозирования временного ряда на основе загруженного файла Excel.

    Args:
        file: Путь до загружаемого Excel файла.
        sheet_name: Имя листа в Excel, содержащего данные.
        date_name: Название столбца с датами.
        series_name: Название столбца с временными рядами.
        forecasting_steps: Количество шагов для предсказания.
        use_only_light_models: Флаг использования только легких моделей для увеличения скорости предсказания. Исключается NeuralProphet.
        year_limit: Ограничение по годам для анализа данных (необязательный параметр).
        train_n_epochs: Количество эпох обучения neuralprophet, если не указан, то количество эпох будет зависеть от размера временного ряда, чем больше эпох, тем дольше обучение (необязательный параметр).
    return: ID Уникальный идентификатор задачи
    """

    data = {
        'sheet_name': sheet_name,
        'date_name': date_name,
        'series_name': series_name,
        'forecasting_steps': forecasting_steps,
        'use_only_light_models': use_only_light_models,
        'year_limit': year_limit,
        'train_n_epochs': train_n_epochs,
    }
    response = make_request('POST', f'{url}/predict', files=file, data=data, auth=auth)
    return str(response['task_id'])


def get_task_status(task_id: str, url: str, auth: HTTPBasicAuth) -> str:
    """Получение статуса задачи предсказания.

    Args:
        task_id:  ID задачи, статус которой нужно получить.
    return: Статус задачи (PENDING, SUCCESS, FAILURE)
    """

    response = make_request('GET', url=f'{url}/status/{task_id}', auth=auth)
    return str(response['status'])


def get_task_result(task_id: str, url: str, auth: HTTPBasicAuth) -> str:
    """Получение результата задачи предсказания.

    Args:
        task_id: ID задачи, результат которой нужно получить.

    return: Результат задачи, если она завершена, или статус "PENDING".
    """

    response = make_request('GET', url=f'{url}/result/{task_id}', auth=auth)
    return str(response['result'])


async def serve(url, user, password) -> None:
    logger = logging.getLogger(__name__)
    auth = HTTPBasicAuth(user, password)

    server = Server("mcp-forecasting")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=ForecastingTools.CREATE,
                description=create_task.__doc__,
                inputSchema=CreateTask.schema()
            ),
            Tool(
                name=ForecastingTools.GET_STATUS,
                description=get_task_status.__doc__,
                inputSchema=GetTaskStatus.schema()
            ),
            Tool(
                name=ForecastingTools.GET_RESULT,
                description=get_task_result.__doc__,
                inputSchema=GetTaskResult.schema()
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == ForecastingTools.CREATE.value:
            result = create_task(
                file=arguments.get('file'),
                sheet_name=arguments.get('sheet_name'),
                date_name=arguments.get('date_name'),
                series_name=arguments.get('series_name'),
                forecasting_steps=arguments.get('forecasting_steps'),
                use_only_light_models=arguments.get('use_only_light_models'),
                year_limit=arguments.get('year_limit'),
                train_n_epochs=arguments.get('train_n_epochs'),
                url=url,
                auth=auth
            )
            logger.error(result)
            return [TextContent(
                type='text',
                text=result
            )]

        elif name == ForecastingTools.GET_STATUS.value:
            result = get_task_status(
                task_id=arguments['task_id'],
                url=url,
                auth=auth,
            )
            logger.error(result)
            return [TextContent(
                type='text',
                text=result
            )]
        elif name == ForecastingTools.GET_RESULT.value:
            return [TextContent(
                type='text',
                text=get_task_result(
                    task_id=arguments['task_id'],
                    url=url,
                    auth=auth,
                )
            )]
        else:
            raise ValueError(f"Unknown tool: {name}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
