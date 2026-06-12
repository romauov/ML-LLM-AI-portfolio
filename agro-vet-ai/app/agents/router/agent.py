import traceback

from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from app.agents.base import BaseAgent
from app.agents.pharmacist.utils import extract_substances_and_build_footnote
from app.agents.router.models import TopicRouterAgentResponse
from app.agents.router.state import AgentState
from app.agents.router.nodes import tools_call_node, llm_call_node, final_answer_node
from app.agents.router.conditions import llm_call_condition, tools_call_condition
from app.agents.router.tools import (
    process_with_avian_disease_diagnosis,
    process_with_swine_disease_diagnosis,
    # process_with_drug_instruction,
    process_with_pharmacist,
    process_with_pcr_test_interpretation,
    process_with_elisa_test_interpretation,
    process_with_librarian,
    process_with_combined_general,
)
from app.utils.logger import get_logger
from config.config import Config

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
            # process_with_drug_instruction,
            process_with_pharmacist,
            process_with_pcr_test_interpretation,
            process_with_elisa_test_interpretation,
            process_with_librarian,
            process_with_combined_general,
        ]
        self.tools_open_ai = [
            {"type": "function", "function": convert_to_openai_function(t)} for t in self.tools]
        self.tools_by_name = {tool_.name: tool_ for tool_ in self.tools}

        self.expert_results = []
        self.attempts = 0

    def process(
            self,
            question: str,
            file_path: str = None,
            user_id: str = None
    ) -> TopicRouterAgentResponse:
        """
        Process a question using the router agent system.

        :param question: User question
        :param file_path: Optional file path for test interpretation tools
        :param user_id: Optional user ID for dialog context management
        :return: Dictionary with tag and content of the response, or just the content if return_dict is False
        """

        try:
            self.logger.info(
                f"Processing question with router agent: {question[:100]}...")

            # Create and build the agent
            graph = self.build()

            # Process the question with optional file path and user_id
            if not self.user_dialog_history:
                self.user_dialog_history = []
            self.user_dialog_history.append(
                {"role": "user", "content": question})
            state_input = {"messages": self.user_dialog_history}
            if file_path:
                state_input["file_path"] = file_path
            if user_id:
                state_input["user_id"] = user_id
            result = graph.invoke(state_input, config={"recursion_limit": 100})

            # Extract the response content correctly
            if 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    response = last_message['content']
                else:
                    response = str(last_message)
            else:
                response = "Не удалось получить ответ от агента."

            # если библиотекарь был вызван, ищем препараты по финальному ответу
            librarian_was_called = any(
                r.get("tool") == "process_with_librarian" for r in self.expert_results
            )
            if librarian_was_called:
                try:
                    self.logger.info(
                        f"[footnote] Библиотекарь был вызван, извлекаем вещества из ответа роутера. "
                        f"Инструменты: {[r['tool'] for r in self.expert_results]}"
                    )
                    footnote = extract_substances_and_build_footnote(response, self)
                    if footnote:
                        response += footnote
                except Exception as e:
                    self.logger.warning(f"Ошибка при формировании сноски фармацевта: {e}")

            # Собираем контекст из всех вызванных экспертов
            combined_context = "\n\n".join([
                f"[{result['tool']}]\n\n{result['context']}"
                for result in self.expert_results
                if result.get('context')
            ]) if self.expert_results else ""

            # Собираем контекстные изображения из всех вызванных экспертов
            combined_context_images = []
            for result in self.expert_results:
                context_images = result.get("context_images")
                if context_images:
                    combined_context_images.extend(context_images)

            # Собираем file_requests из всех вызванных экспертов
            combined_file_requests = []
            for result in self.expert_results:
                file_requests = result.get("file_requests")
                if file_requests:
                    combined_file_requests.extend(file_requests)

            self.logger.info(
                "Successfully processed question with router agent")

            return TopicRouterAgentResponse(
                response=response,
                context=combined_context,
                context_images=combined_context_images,
                file_requests=combined_file_requests,
            )
        except Exception as e:
            self.logger.error(f"Error in TopicRouterAgent.process: {e}")
            self.logger.error(f"Full error stack: {traceback.format_exc()}")
            return TopicRouterAgentResponse(
                response="Sorry, an error occurred while processing your question with the router agent.",
            )

    def build(self) -> CompiledStateGraph:
        """Создание графа действия агента.

        Ноды:
            dialog_context_check - нода проверки контекста диалога.
            llm_call - нода вызова llm.
            tools_call - нода выполнения функций, если модель вернула tool_call (function calling).
            validation - нода валидации собранной информации.
            final_answer - нода финального ответа llm, если получены все ответы от экспертов или
            достигнут лимит попыток.
        """
        self.logger.info('Создание графа действий агента')

        workflow = StateGraph(AgentState)

        workflow.add_node('llm_call', lambda state: llm_call_node(self, state))
        workflow.add_node(
            'tools_call', lambda state: tools_call_node(self, state))
        workflow.add_node(
            'final_answer', lambda state: final_answer_node(self, state))

        workflow.set_entry_point('llm_call')

        workflow.add_conditional_edges(
            'llm_call',
            lambda state: llm_call_condition(self, state),
            {
                'continue': 'tools_call',
                'end_by_limit': 'final_answer',
                'end': END,
            }
        )

        workflow.add_conditional_edges(
            'tools_call',
            lambda state: tools_call_condition(self, state),
            {
                'continue': 'llm_call',
            }
        )

        workflow.add_edge('final_answer', END)

        graph = workflow.compile()
        return graph
