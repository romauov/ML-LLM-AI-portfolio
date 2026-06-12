import json
from typing import Annotated, Sequence
from langchain_core.messages import ToolMessage, ToolCall, AIMessage, BaseMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from typing import TypedDict
from app.agents.base import BaseAgent
from app.agents.pharmacist.prompts import SYSTEM_PROMPT, SYSTEM_FINAL_ANSWER_PROMPT
from app.agents.pharmacist.tools import (
    search_by_trade_name,
    search_by_active_substance,
    search_by_conditions,
    get_drug_full_info,
)
from app.agents.pharmacist.searching_engine import DrugSearchEngine
from app.agents.pharmacist.utils import format_drug_chunks, fix_broken_tool_call
from app.utils.logger import get_logger
from config.config import Config
from app.utils.langchain_message_converters import to_openai_format

_search_engine = DrugSearchEngine()

cfg = Config.from_yaml()


class AgentState(TypedDict):
    """State for PharmacistAgent LangGraph workflow."""
    messages: Annotated[Sequence[BaseMessage], add_messages]


class PharmacistAgent(BaseAgent):
    def __init__(
        self,
        context: dict = None,
        dialog_history: list[dict[str, str]] = None
    ):
        super().__init__(context, dialog_history)
        self.logger = get_logger(__name__)
        self.llm_hyperparameters = cfg.pharmacist.main_agent.llm_hyperparameters.dict()

        self.tools = [
            search_by_trade_name,
            search_by_active_substance,
            search_by_conditions,
            get_drug_full_info,
        ]
        self.tools_open_ai = [
            {"type": "function", "function": convert_to_openai_function(t)}
            for t in self.tools
        ]
        self.tools_by_name = {tool_.name: tool_ for tool_ in self.tools}

        self.context_documents = []
        if context and isinstance(context, dict):
            self.context_documents = context.get('documents', [])
        
        self.file_requests = []
        self._attempts = 0

        # Компактный каталог — только малые справочные поля
        db_metadata = _search_engine.get_unique_metadata_values()
        catalog_parts = []
        field_labels = {
            'drug_class': 'Классы препаратов',
            'target_animals': 'Целевые животные',
            'route': 'Пути введения',
            'dosage_form': 'Формы выпуска',
        }
        for field, label in field_labels.items():
            values = db_metadata.get(field, [])
            if values:
                catalog_parts.append(f"{label}: {', '.join(values)}")
        self._catalog_text = "Каталог базы данных препаратов:\n" + "\n".join(catalog_parts)

    def tools_call_node(self, state: AgentState) -> dict[str, list[ToolMessage]]:
        """
        Выполнение инструментов вызванных LLM.
        """
        self.logger.info('[tools_call_node] Выполнение инструментов')
        outputs = []

        for tool_call in state["messages"][-1].tool_calls:
            self.logger.info(f'  Вызов инструмента: {tool_call["name"]}')

            result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])

            text = result.get('text', '')
            context_documents = result.get('documents', [])
            file_request = result.get('file_request')

            if context_documents:
                self.context_documents.extend(context_documents)

            if file_request:
                self.file_requests.append(file_request)

            outputs.append(
                ToolMessage(
                    content=text,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

        return {"messages": outputs}

    def llm_call_node(self, state: AgentState) -> dict[str, AIMessage]:
        """
        Генерация ответа агента.
        """
        self.logger.info('[llm_call_node] Генерация ответа агента')

        # Подставляем каталог в системный промпт
        catalog_text = getattr(self, '_catalog_text', '')
        system_prompt = SYSTEM_PROMPT.format(catalog=catalog_text)

        messages = [
            {"role": "system", "content": system_prompt},
            *[to_openai_format(msg) for msg in state['messages']]
        ]

        response = self.ask_llm(
            messages=messages,
            params=self.llm_hyperparameters,
            tools=self.tools_open_ai,
        )

        if not response.tool_calls:
            context = format_drug_chunks(self.context_documents) if self.context_documents else ''

            return {"messages": AIMessage(
                content=response.content,
                context=context,
            )}

        response = fix_broken_tool_call(response)
        tool_calls = [
            ToolCall(
                name=t.function.name,
                args=json.loads(t.function.arguments) if t.function.arguments else {},
                id=t.id
            )
            for t in response.tool_calls
        ]
        return {"messages": AIMessage(content='', tool_calls=tool_calls)}

    def final_answer_node(self, state: AgentState) -> dict[str, AIMessage]:
        """
        Генерация финального ответа агента при достижении лимита попыток.
        """
        self.logger.info('[final_answer_node] Генерация финального ответа')

        messages = [
            {"role": "system", "content": SYSTEM_FINAL_ANSWER_PROMPT},
            *[to_openai_format(msg) for msg in state['messages']]
        ]

        response = self.ask_llm(
            messages=messages,
            params=self.llm_hyperparameters,
        )

        context = format_drug_chunks(self.context_documents) if self.context_documents else ''

        return {"messages": AIMessage(
            content=response.content,
            context=context,
        )}

    def llm_call_condition(self, state: AgentState) -> str:
        """
        Проверка последнего сообщения и выбор следующей ноды.
        """
        self.logger.info('[llm_call_condition] Проверка условия')

        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, 'tool_calls', None)
        self._attempts += 1

        if tool_calls:
            if self._attempts <= cfg.pharmacist.main_agent.max_attempts:
                return "continue"
            else:
                state["messages"] = state["messages"][:-1]
                return "end_by_limit"

        return "end"

    def tools_call_condition(self, state: AgentState) -> str:
        """
        Проверка результатов выполнения инструмента.
        """
        self.logger.info('[tools_call_condition] Проверка результатов инструмента')
        return 'continue'

    def build(self) -> CompiledStateGraph:
        """
        Создание графа действий агента.
        """
        self.logger.info('Создание графа действий агента Pharmacist')

        workflow = StateGraph(AgentState)

        workflow.add_node('llm_call', self.llm_call_node)
        workflow.add_node('tools_call', self.tools_call_node)
        workflow.add_node('final_answer', self.final_answer_node)

        workflow.set_entry_point('llm_call')

        workflow.add_conditional_edges(
            'llm_call',
            self.llm_call_condition,
            {
                'continue': 'tools_call',
                'end_by_limit': 'final_answer',
                'end': END,
            }
        )

        workflow.add_conditional_edges(
            'tools_call',
            self.tools_call_condition,
            {
                'continue': 'llm_call',
            }
        )

        workflow.add_edge('final_answer', END)

        graph = workflow.compile()
        return graph
