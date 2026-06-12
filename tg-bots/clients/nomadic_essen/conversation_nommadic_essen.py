"""
класс для обработки сообщений и генерации ответов пользователю

@author Nikolay Zhabchikov
"""
import json
from aiogram.types import Message
from clients.nomadic_essen.file_loader import load_files
from utils.charge_logging import log_charges
from utils.conversator.chat_history import get_history, write_history
from utils.conversator.conversator import Conversator
from utils.conversator.tools import generate_tools, call_manager
from utils.openai_client.client import client


class ConversatorNomadicEssen(Conversator):
    def __init__(self, table_id, text_id, name, model):
        super().__init__(table_id, text_id, name, model)
        self.products_list = []

    def update(self):
        """обновление регламента"""

        self.reglament = load_files(self.text_id, self.path)

    async def generate_reply(self, message: Message):
        """ генерация ответа пользователю

        Args:
            user_promt (str): сообщение пользователя
            user_id (int): id пользователя

        Returns:
            dict: ответное сообщение
        """

        if message.text is None:
            return {"reply": "К сожалению, пока я могу работать только с текстовыми сообщениями."}

        call_manager_flag = None

        messages = [{
            "role": "system",
            "content": self.reglament
        }]

        for history_message in get_history(self.path, message.from_user.id):
            messages.append(history_message)

        user_message_obj = {
            "role": "user",
            "content": message.text
        }
        messages.append(user_message_obj)
        write_history(self.path, message.from_user.id, user_message_obj)

        tools = generate_tools()

        response = await self._create_chat_completion(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            extra_headers={"X-title": "tg-bots"}
        )

        response_message = response.choices[0].message
        log_charges(self.path, message.from_user.id, self.model, 'text_generation', response.usage.prompt_tokens,
                    response.usage.completion_tokens)

        tool_calls = response_message.tool_calls
        if tool_calls:
            available_functions = {
                "call_manager": call_manager
            }
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                if function_to_call:
                    function_args = json.loads(tool_call.function.arguments)

                    function_args['path'] = self.path
                    call_manager_flag = True
                    function_response = function_to_call(**function_args)

                    func_message = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                    messages.append(func_message)
                    write_history(self.path, message.from_user.id, func_message)

            response = await self._create_chat_completion(
                model=self.model,
                messages=messages,
                extra_headers={"X-title": "tg-bots"}
            )
            response_message = response.choices[0].message
            log_charges(self.path, message.from_user.id, self.model, 'functions', response.usage.prompt_tokens,
                        response.usage.completion_tokens)

        response_text = response_message.content
        write_history(self.path, message.from_user.id, {"role": "assistant", "content": response_text})

        reply = {"reply": response_text}
        if call_manager_flag:
            reply['message_for_manager'] = message.text
        return reply
