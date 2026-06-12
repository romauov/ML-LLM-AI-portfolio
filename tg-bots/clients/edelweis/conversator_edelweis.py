"""
класс для обработки сообщений и генерации ответов пользователю

@author Sergei Romanov
"""
import json
from aiogram.types import Message
from clients.edelweis.file_loader import load_files
from utils.charge_logging import log_charges
from utils.conversator.chat_history import get_history, write_history
from utils.conversator.conversator import Conversator
from utils.conversator.tools import call_manager, generate_tools, get_full_pricelist, get_prices, pick_products
from utils.openai_client.client import client


class ConversatorEdelweis(Conversator):

    def __init__(self, table_id, text_id, name, model):
        super().__init__(table_id, text_id, name, model)

    def update(self):
        """ обновление регламента и прайс-листа

        Args:
            table_id (str): id гугл-таблицы с прайс-листом. Defaults to None.
            text_id (str): id гугл-документа с регламентов. Defaults to None.
        """
        self.price_list, self.reglament = load_files(self.text_id, self.path)
    
    async def generate_reply(self, message: Message):
        """ генерация ответа пользователю

        Args:
            user_promt (str): сообщение пользователя
            from_id (int): id пользователя

        Returns:
            dict: ответное сообщение
        """
        if message.text is None:
            return {"reply": "К сожалению, пока я могу работать только с текстовыми сообщениями."}
        call_manager_flag = None
        send_price_flag = None
        products_list = self.price_list['product'].unique(
        ).tolist()
        messages = [
            {"role": "system", "content": self.reglament}
        ]

        for msg in get_history(self.path, message.from_user.id):
            messages.append(msg)
        messages.append({"role": "user", "content": message.text})
        write_history(self.path, message.from_user.id, {
                      "role": "user", "content": message.text})

        tools = generate_tools('Получение цен, сроков реализации и веса упаковки для списка продуктов')

        response = await self._create_chat_completion(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            extra_headers={"X-title": "tg-bots"}
        )
        response_message = response.choices[0].message
        log_charges(self.path, message.from_user.id, self.model, 'text_generation', response.usage.prompt_tokens, response.usage.completion_tokens)

        tool_calls = response_message.tool_calls
        if tool_calls:
            available_functions = {
                "get_prices": get_prices,
                "get_full_pricelist": get_full_pricelist,
                "call_manager": call_manager
            }
            messages.append(response_message)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                if function_to_call:
                    function_args = json.loads(tool_call.function.arguments)

                    if function_name == 'get_prices':
                        picked_producsts, prompt_tokens, completion_tokens = await pick_products(client=client,
                                                                                                 model=self.model,
                                                                                                 products_list=products_list,
                                                                                                 user_promt=message.text)
                        log_charges(self.path, message.from_user.id, self.model, 'pick products', prompt_tokens, completion_tokens)
                        function_response = get_prices(df=self.price_list,
                                                       products=picked_producsts,
                                                       product_col_name='product',
                                                       cols_to_drop=['product', 'halal'])
                    elif function_name == 'call_manager':
                        function_args['path'] = self.path
                        call_manager_flag = True
                        function_response = function_to_call(**function_args)
                    else:
                        send_price_flag = True
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
            log_charges(self.path, message.from_user.id, self.model, 'functions', response.usage.prompt_tokens, response.usage.completion_tokens)

        resp_text = response_message.content
        write_history(self.path, message.from_user.id, {
                      "role": "assistant", "content": resp_text})
        
        reply = {"reply": resp_text}
        if send_price_flag:
            reply['send_price'] = True
        if call_manager_flag:
            reply['message_for_manager'] = message.text
        return reply
