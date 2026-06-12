"""
класс для обработки сообщений и генерации ответов пользователю

@author Sergei Romanov
"""
import os

from aiogram.types import Message

from utils.client import client
from utils.remove_md import remove_markdown
from conversator.chat_history import get_history, write_history
from conversator.file_loader import load_files
from conversator.gpt_tools import call_manager, generate_tools, get_full_pricelist, get_prices, pick_products
from utils.decorators import exponential_backoff


class Conversator:
    """класс для обработки сообщений и генерации ответов пользователю
    """

    def __init__(self, client_data):
        """ создание экземпляра класса

        Args:
            table_id (str): id гугл-таблицы с прайс-листом
            text_id (str): id гугл-документа с регламентов
            name (str): название компании (для создания папки)
            model (str): используемая модель ChatGPT
        """
        self.client_name = client_data.client_name
        self.path = f'logs/{self.client_name}'
        self.table_id = client_data.table_id
        self.sheet_id = client_data.sheet_id
        self.price_id = client_data.price_id
        self.price_sheet = client_data.price_sheet
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.model = 'openai/gpt-4o-mini'
        self.update()

    def update(self):
        """ обновление регламента и прайс-листа

        Args:
            table_id (str): id гугл-таблицы с прайс-листом. Defaults to None.
            text_id (str): id гугл-документа с регламентов. Defaults to None.
        """
        conversator_data = load_files(
            self.table_id, self.sheet_id, self.price_id, self.price_sheet)

        self.reglament = conversator_data.get('reglament')
        self.buttons = conversator_data.get('buttons', None)
        self.tools = conversator_data.get('tools', None)
        self.price_list = conversator_data.get('price_list', None)
        self.placeholder = conversator_data.get('placeholder', "")

    @exponential_backoff(max_retries=5, base_delay=1)
    async def _create_chat_completion(self, *args, **kwargs):
        """Обертка для chat.completions.create с обработкой ошибок"""
        return await client.chat.completions.create(*args, **kwargs)

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

        response = await self._create_chat_completion(
            model=self.model,
            messages=messages,
            tools=generate_tools(self.tools),
            tool_choice="auto",
            extra_headers={"X-title": "axe-tg-bots"}
        )
        response_message = response.choices[0].message

        tool_calls = response_message.tool_calls
        if tool_calls:
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name

                if function_name == "call_manager":
                    self.message_for_manager = message.text
                    function_response = call_manager(self.path, message.text)
                elif function_name == 'get_prices':
                    available_products = await pick_products(client=client,
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
                extra_headers={"X-title": "axe-tg-bots"}
            )
            response_message = response.choices[0].message

        resp_text = response_message.content
        resp_text = remove_markdown(resp_text)
        write_history(self.path, message.from_user.id, {
                      "role": "assistant", "content": resp_text})

        reply = {"reply": resp_text}
        if self.message_for_manager:
            reply['message_for_manager'] = self.message_for_manager
        return reply

    async def make_summary(self, from_id):
        """ суммаризация истории сообщений

        Args:
            from_id (int): id пользователя

        Returns:
            str: краткое изложение истории чата
        """
        summarizer_promt = f"""
        необходимо суммаризовать историю сообщений чат-бота
        ---
        Краткая историия сообщений:
        [вставьте краткое изложение переговоров], [вставьте ключевые моменты обсуждения].

        Список вопросов, которыми интересовался пользователь:
        1. [Вопрос 1]
        2. [Вопрос 2]
        3. [Вопрос 3]
        ...

        Контактные данные пользователя: (если предоставлены)
        - Имя: [Имя пользователя]
        - Электронная почта: [Email пользователя]
        - Телефон: [Телефон пользователя]
        ---
        """
        messages = [
            {"role": "system", "content": summarizer_promt}
        ]
        for msg in get_history(self.path, from_id):
            messages.append(msg)

        response = await self._create_chat_completion(
            model=self.model,
            messages=messages,
            extra_headers={"X-title": "axe-tg-summary"}
        )
        response = response.choices[0].message.content

        return remove_markdown(response)
