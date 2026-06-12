"""
класс для обработки сообщений и генерации ответов пользователю

@author Sergei Romanov
"""
import json
import os
from aiogram.types import Message
from utils.openai_client.client import client
from utils.conversator.conversator import Conversator
from utils.conversator.chat_history import get_history, write_history
from utils.conversator.file_loader import load_files
from utils.conversator.tools import get_full_pricelist, get_prices,  call_manager, generate_tools, pick_products
from utils.charge_logging import log_charges
from utils.summarizer.summarizer import summarizer_promt



class MeatinfConversator(Conversator):
    """класс для обработки сообщений и генерации ответов пользователю
    """

    def __init__(self, table_id, text_id, name, model):
        """ создание экземпляра класса

        Args:
            table_id (str): id гугл-таблицы с прайс-листом
            text_id (str): id гугл-документа с регламентов
            name (str): название компании (для создания папки)
            model (str): используемая модель ChatGPT
        """
        self.path = f'logs/{name}'
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.model = model
        self.table_id = table_id
        self.text_id = text_id
        self.update()

    def update(self):
        """ обновление регламента и прайс-листа

        Args:
            table_id (str): id гугл-таблицы с прайс-листом. Defaults to None.
            text_id (str): id гугл-документа с регламентов. Defaults to None.
        """
        self.price_list, self.reglament = load_files(
            self.table_id, self.text_id, self.path)
        self.reglament += f"""Список продуктов в наличии - {self.price_list.iloc[:, 0].tolist()}
        """
        self.reglament += f"""
        Используй эти функции:

        {json.dumps(generate_tools(), indent=2)}

        Правила:
        1. Определяй КОНКРЕТНЫЙ запрос пользователя
        2. Для цены на один или несколько товаров -> get_prices
        3. Для полного прайс-листа -> get_full_pricelist
        4. Для связи с менеджером -> call_manager
        5. Не выдумывай параметры!
        6. При сомнениях - уточни вопрос
        """

    async def generate_reply(self, message: Message):
        """ генерация ответа пользователю

        Args:
            user_promt (str): сообщение пользователя
            from_id (int): id пользователя

        Returns:
            dict: ответное сообщение
        """
        self.message_for_manager = None
        if message.text is None:
            return {"reply": "К сожалению, пока я могу работать только с текстовыми сообщениями."}

        messages = [
            {"role": "system", "content": self.reglament}
        ]
        for msg in get_history(self.path, message.from_user.id):
            messages.append(msg)
        messages.append({"role": "user", "content": message.text})
        write_history(self.path, message.from_user.id, {
                      "role": "user", "content": message.text})

        tools = generate_tools()

        response = await self._create_chat_completion(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            extra_headers={"X-title": "tg-bots"}
        )
        response_message = response.choices[0].message

        log_charges(self.path, message.from_user.id, self.model, 'text_generation',
                    response.usage.prompt_tokens, response.usage.completion_tokens)

        tool_calls = response_message.tool_calls
        if tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name

                if function_name == "call_manager":
                    self.message_for_manager = message.text
                    function_response = call_manager(self.path, message.text)

                elif function_name == 'get_prices':
                    available_products, _, _ = await pick_products(client=client,
                                                                   model=self.model,
                                                                   products_list=self.price_list.iloc[:, 0].tolist(
                                                                   ),
                                                                   user_promt=message.text)
                    function_response = get_prices(
                        self.price_list, available_products)

                elif function_name == 'get_full_pricelist':
                    function_response = get_full_pricelist(self.price_list)

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
            log_charges(self.path, message.from_user.id, self.model, 'functions',
                        response.usage.prompt_tokens, response.usage.completion_tokens)

        resp_text = response_message.content
        write_history(self.path, message.from_user.id, {
                      "role": "assistant", "content": resp_text})

        reply = {"reply": resp_text}
        if self.message_for_manager:
            reply['message_for_manager'] = self.message_for_manager
        return reply

    def change_model(self, model):
        self.model = model

    async def make_summary(self, from_id):
        """ суммаризация истории сообщений

        Args:
            from_id (int): id пользователя

        Returns:
            str: краткое изложение истории чата
        """

        messages = [
            {"role": "system", "content": summarizer_promt}
        ]
        for msg in get_history(self.path, from_id):
            messages.append(msg)

        response = await self._create_chat_completion(
            model=self.model,
            messages=messages,
            extra_headers={"X-title": "tg-bots"}
        )
        log_charges(self.path, from_id, self.model, 'summary',
                    response.usage.prompt_tokens, response.usage.completion_tokens)
        return response.choices[0].message.content
