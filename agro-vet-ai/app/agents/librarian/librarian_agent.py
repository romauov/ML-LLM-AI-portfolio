import json
from typing import Annotated, Sequence, TypedDict, Optional

from langchain_core.messages import BaseMessage, ToolMessage, ToolCall, AIMessage
from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from app.agents.base import BaseAgent
from app.agents.librarian.prompts import SYSTEM_PROMPT, SYSTEM_FINAL_ANSWER_PROMPT
from app.agents.librarian.tools import search_database_by_one_book, get_page_content, get_list_of_books, \
    get_books_content, search_database_by_all_books
from app.agents.librarian.utils import format_context, fix_broken_tool_call
from config.config import Config
from app.utils.langchain_message_converters import to_openai_format
from app.utils.logger import get_logger

cfg = Config.from_yaml()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


class LibrarianAgent(BaseAgent):
    def __init__(
            self,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None
    ):
        super().__init__(context, dialog_history)
        self.logger = get_logger(__name__)
        self.llm_hyperparameters = cfg.librarian.main_agent.llm_hyperparameters.dict()

        self.tools = [
            search_database_by_all_books,
            search_database_by_one_book,
            get_page_content,
            get_list_of_books,
            get_books_content,
        ]
        self.tools_open_ai = [
            {"type": "function", "function": convert_to_openai_function(t)} for t in self.tools]
        self.tools_by_name = {tool_.name: tool_ for tool_ in self.tools}

        self.context_documents = []
        self.context_images = []
        self._attempts = 0

    def _init_message(self, state: AgentState) -> dict[str, list[Optional[AIMessage | ToolMessage]]]:

        f_name = 'get_list_of_books'
        f_args = {}
        f_dummy_id = 'call_123456'

        tool_calls = [ToolCall(name=f_name, args=f_args, id=f_dummy_id)]
        assistance_tool_call_message = AIMessage(
            content='', tool_calls=tool_calls)

        tool_response = self.tools_by_name[f_name].invoke(f_args)
        tool_response_message = ToolMessage(
            content=tool_response, name=f_name, tool_call_id=f_dummy_id)

        return {"messages": [assistance_tool_call_message, tool_response_message]}

    def tools_call_node(self, state: AgentState) -> dict[str, list[ToolMessage]]:
        """
        Выполнение инструментов вызванных LLM.

        :param state: Состояние агента.
        """
        self.logger.info(
            '[tools_call_node] Выполнение инструментов вызванных LLM')
        outputs = []
        for tool_call in state["messages"][-1].tool_calls:
            result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"])

            text = result.get('text')
            context_documents = result.get('documents')
            context_images = result.get('images')

            if context_documents:
                self.context_documents.append(
                    format_context(context_documents))
            if context_images:
                self.context_images.extend(context_images)

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

        :param state: Состояние агента.
        """
        self.logger.info('[llm_call_node] Генерация ответа агента')

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[json.loads(json.dumps(to_openai_format(msg))) for msg in state['messages']]
        ]

        response = self.ask_llm(
            messages=messages,
            params=self.llm_hyperparameters,
            tools=self.tools_open_ai,
        )

        if not response.tool_calls:
            return {"messages": AIMessage(
                content=response.content,
                context='\n\n'.join(self.context_documents),
                context_images=list(set(self.context_images)),
            )}

        response = fix_broken_tool_call(response)
        tool_calls = [
            ToolCall(
                name=t.function.name,
                args=eval(t.function.arguments) if t.function.arguments else {},
                id=t.id
            )
            for t in response.tool_calls
        ]
        return {"messages": AIMessage(content='', tool_calls=tool_calls)}

    def final_answer_node(self, state: AgentState) -> dict[str, AIMessage]:
        """
        Генерация финального ответа агента.

        :param state: Состояние агента.
        """
        self.logger.info(
            '[final_answer_node] Генерация финального ответа агента')

        messages = [
            {"role": "system", "content": SYSTEM_FINAL_ANSWER_PROMPT},
            *[json.loads(json.dumps(to_openai_format(msg))) for msg in state['messages']]
        ]

        response = self.ask_llm(
            messages=messages,
            params=self.llm_hyperparameters,
        )

        return {"messages": AIMessage(
            content=response.content,
            context='\n\n'.join(self.context_documents),
            context_images=list(set(self.context_images)),
        )}

    def llm_call_condition(self, state: AgentState) -> str:
        """
        Проверка последнего сообщения в состоянии агента и последующий выбор ноды к которой надо перейти.

        :param state: Состояние агента.
        """
        self.logger.info(
            '[llm_call_condition] Проверка последнего сообщения в состоянии агента')

        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, 'tool_calls', None)
        self._attempts += 1
        if tool_calls:
            if self._attempts <= cfg.librarian.main_agent.max_attempts:
                return "continue"
            else:
                state["messages"] = state["messages"][:-1]
                return "end_by_limit"

        return "end"

    def tools_call_condition(self, state: AgentState) -> str:
        """
        Проверка результатов выполнения последней функции и последующий выбор ноды к которой надо перейти.

        :param state: Состояние агента.
        """
        self.logger.info(
            '[tools_call_condition] Проверка результатов выполнения последней функции')

        return 'continue'

    def build(self) -> CompiledStateGraph:
        """Создание графа действия агента.

        Ноды:
            llm_call - нода вызова llm.
            tools_call - нода выполнения функций, если модель вернула tool_call (function calling).
            final_answer - нода финального ответа llm, если получены все ответы от экспертов или
            достигнут лимит попыток.
        """
        self.logger.info('Создание графа действий агента')

        workflow = StateGraph(AgentState)

        workflow.add_node('init', self._init_message)
        workflow.add_node('llm_call', self.llm_call_node)
        workflow.add_node('tools_call', self.tools_call_node)
        workflow.add_node('final_answer', self.final_answer_node)

        workflow.set_entry_point('init')
        workflow.add_edge('init', 'llm_call')

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
