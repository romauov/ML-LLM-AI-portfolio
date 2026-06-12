"""
VetBot Router Agent using LangChain AgentExecutor.

Агент использует LangChain AgentExecutor с функциями для маршрутизации
ветеринарных запросов (диагностика, препараты, книги, тесты).
Аналогично investigations/web-backend/app/agents/vet_agent.py
"""

import os

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

from typing import AsyncGenerator
import traceback

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.base import BaseAgent
from app.agents.router_v2.models import TopicRouterAgentResponse
from app.agents.router_v2.prompts import ROUTER_AGENT_TOOLS_PROMPT
from app.agents.router_v2.librarian_tools import (
    search_database_by_all_books,
    search_database_by_one_book,
    get_page_content,
    get_list_of_books,
    get_books_content,
)
from app.agents.router_v2.pharmacist_tools import (
    search_by_trade_name,
    search_by_active_substance,
    search_by_conditions,
    get_drug_full_info,
)
from app.agents.router_v2.tools import (
    process_with_avian_disease_diagnosis,
    process_with_swine_disease_diagnosis,
    process_with_pcr_test_interpretation,
    process_with_elisa_test_interpretation,
)
from app.utils.logger import get_logger
from config.config import Config
from app.utils.settings import secrets as s
from app.agents.router_v2.abbreviations import build_abbreviation_hint

cfg = Config.from_yaml()
logger = get_logger(__name__)


class TopicRouterAgent(BaseAgent):
    def __init__(self, context=None, dialog_history=None, file_path=None, user_id=None):
        super().__init__(context, dialog_history)
        self.logger = get_logger(__name__)
        self.file_path = file_path
        self.user_id = user_id
        self.llm_hyperparameters = cfg.router_agent.llm_hyperparameters.model_dump()

        self.tools = [
            process_with_avian_disease_diagnosis,
            process_with_swine_disease_diagnosis,
            process_with_pcr_test_interpretation,
            process_with_elisa_test_interpretation,
            search_database_by_all_books,
            search_database_by_one_book,
            get_page_content,
            get_list_of_books,
            get_books_content,
            search_by_trade_name,
            search_by_active_substance,
            search_by_conditions,
            get_drug_full_info,
        ]

        self._agent_executor = None

    def _get_llm(self):
        return ChatOpenAI(
            base_url=s.openrouter_base_url,
            api_key=s.openrouter_api_key,
            model=cfg.llm_models.openrouter.llm,
            temperature=self.llm_hyperparameters.get("temperature", 0.1),
            streaming=True,
            default_headers={"X-title": "agro-vet-ai"},
        )

    def _get_agent_executor(self):
        if self._agent_executor is not None:
            return self._agent_executor

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ROUTER_AGENT_TOOLS_PROMPT),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        llm = self._get_llm()
        agent = create_openai_tools_agent(llm, self.tools, prompt)

        self._agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=10,
            handle_parsing_errors="Извините, произошла ошибка. Попробуйте переформулировать вопрос.",
        )

        return self._agent_executor

    def process(
        self, question: str, file_path: str = None, user_id: str = None
    ) -> TopicRouterAgentResponse:
        try:
            self.logger.info(f"Processing question: {question[:100]}...")

            agent_executor = self._get_agent_executor()

            hint = build_abbreviation_hint(question)
            enriched = f"{hint}\n\n{question}" if hint else question
            agent_input = {"input": enriched}

            if self.user_dialog_history:
                chat_history = []
                for msg in self.user_dialog_history:
                    if msg.get("role") == "user":
                        chat_history.append(
                            HumanMessage(content=msg.get("content", ""))
                        )
                    elif msg.get("role") == "assistant":
                        chat_history.append(AIMessage(content=msg.get("content", "")))
                agent_input["chat_history"] = chat_history

            result = agent_executor.invoke(agent_input)

            response = result.get("output", "")

            self.logger.info("Successfully processed question with router agent")

            return TopicRouterAgentResponse(
                response=response,
                context="",
                context_images=[],
                file_requests=[],
            )

        except Exception as e:
            self.logger.error(f"Error in TopicRouterAgent.process: {e}")
            self.logger.error(f"Full error stack: {traceback.format_exc()}")
            return TopicRouterAgentResponse(
                response="Извините, произошла ошибка при обработке вашего вопроса.",
            )

    def build(self):
        return self._get_agent_executor()

    async def process_stream(
        self, question: str, file_path: str = None, user_id: str = None
    ) -> AsyncGenerator[dict, None]:
        try:
            self.logger.info(f"Starting stream processing: {question[:100]}...")

            agent_executor = self._get_agent_executor()

            hint = build_abbreviation_hint(question)
            enriched = f"{hint}\n\n{question}" if hint else question
            agent_input = {"input": enriched}

            if self.user_dialog_history:
                chat_history = []
                for msg in self.user_dialog_history:
                    if msg.get("role") == "user":
                        chat_history.append(
                            HumanMessage(content=msg.get("content", ""))
                        )
                    elif msg.get("role") == "assistant":
                        chat_history.append(AIMessage(content=msg.get("content", "")))
                agent_input["chat_history"] = chat_history

            config = RunnableConfig(run_name="vet_agent_chat", recursion_limit=100)

            async for event in agent_executor.astream_events(
                agent_input,
                config=config,
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    content = (
                        chunk.content
                        if chunk and hasattr(chunk, "content") and chunk.content
                        else ""
                    )
                    if content:
                        yield {"node": "llm_stream", "data": {"content": content}}

                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    tool_input = event["data"].get("input", {})
                    run_id = event.get("run_id", "unknown")
                    yield {
                        "node": "tool_start",
                        "data": {
                            "tool": tool_name,
                            "input": tool_input,
                            "run_id": run_id,
                        },
                    }

                elif kind == "on_tool_end":
                    tool_name = event["name"]
                    tool_output = event["data"].get("output", "")
                    tool_input = event["data"].get("input", {})
                    output_len = len(str(tool_output))

                    if tool_name == "process_with_avian_disease_diagnosis":
                        summary = f"🐔 **Диагностика птиц** → {output_len} символов"
                    elif tool_name == "process_with_swine_disease_diagnosis":
                        summary = f"🐷 **Диагностика свиней** → {output_len} символов"
                    elif tool_name == "process_with_pcr_test_interpretation":
                        summary = "🧬 **ПЦР тест**"
                    elif tool_name == "process_with_elisa_test_interpretation":
                        summary = "🧪 **ИФА тест**"
                    elif tool_name == "search_database_by_all_books":
                        summary = f"📚 **Поиск по книгам** → {output_len} символов"
                    elif tool_name == "search_database_by_one_book":
                        source = tool_input.get("source_name", "")[:30]
                        summary = f"📖 **Книга: {source}...** → {output_len} символов"
                    elif tool_name == "get_page_content":
                        summary = f"📄 **Страницы книги** → {output_len} символов"
                    elif tool_name == "get_list_of_books":
                        summary = "📋 **Список книг**"
                    elif tool_name == "get_books_content":
                        summary = "📑 **Оглавление книг**"
                    elif tool_name == "search_by_trade_name":
                        summary = f"💊 **Поиск по названию** → {output_len} символов"
                    elif tool_name == "search_by_active_substance":
                        summary = f"🔍 **Поиск по действующему веществу** → {output_len} символов"
                    elif tool_name == "search_by_conditions":
                        summary = f"🏥 **Поиск по заболеванию** → {output_len} символов"
                    elif tool_name == "get_drug_full_info":
                        summary = f"📝 **Инструкция препарата** → {output_len} символов"
                    else:
                        summary = (
                            f"🔧 **Инструмент `{tool_name}`** → {output_len} символов"
                        )

                    yield {
                        "node": "tool_end",
                        "data": {
                            "tool": tool_name,
                            "summary": summary,
                        },
                    }

                elif kind == "on_chain_end" and event.get("name") == "AgentExecutor":
                    output_data = event.get("data", {}).get("output", {})
                    if output_data and isinstance(output_data, dict):
                        final_output = output_data.get("output", "")
                        if final_output:
                            yield {
                                "node": "final_output",
                                "data": {"content": final_output},
                            }

            self.logger.info("Stream processing completed")

        except Exception as e:
            self.logger.error(f"Error in process_stream: {e}")
            yield {"error": str(e)}
