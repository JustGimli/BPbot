import os
import io
from aiogram import types
from aiogram.dispatcher import FSMContext
import json
from dotenv import load_dotenv
import requests
# from makets.base import state
from makets.base import base, state


load_dotenv('.env')


class Bot(base.BaseBot):
    def __init__(self, token, state):
        self.state = state
        super().__init__(token)

    async def payments(self, message: types.Message, state: FSMContext):
        if message.text == "Оплатить консультацию":

            try:
                async with state.proxy() as data:
                    cost = data['cost']
                    name = data['cons_name']
                    if os.environ.get("FIO") and data['days']:
                        description = f'Консультация от {os.environ.get("FIO")}. Период {data["days"]} дней.'
                    else:
                        description = "Консультация"
                link = requests.post(
                    f'{os.environ.get("URL_PATH")}payments/link/', data={"id": os.getenv("ID", None),
                                                                         'username': message.from_user.username,
                                                                         'cost': cost,
                                                                         "description": description,
                                                                         'user_id': message.from_id,
                                                                         'name': name,
                                                                         'consultation_id': data['cons_id']
                                                                         }).json().get('link')
            except requests.exceptions.RequestException:
                link = None

            markup = types.InlineKeyboardMarkup(
                resize_keyboard=True)
            button = types.InlineKeyboardButton("Назад", callback_data='back')
            markup.add(button)
            await self.bot.send_message(message.from_id, 'Спасибо!!', reply_markup=types.ReplyKeyboardRemove())
            await self.bot.send_message(message.from_id, f'Ссылка для оплаты: {link}.', reply_markup=markup)
            await self.state.CHAT.set()
        elif message.text == "Назад":
            markup = self.set_markup()
            await self.bot.send_message(message.from_user.id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
            await self.state.OPTION.set()
        else:
            await state.reset_state()
            await self.bot.send_message(message.from_id, "Команда не разпознана введите /start для начала диалога", reply_markup=types.ReplyKeyboardRemove())

    async def chat(self, message: types.Message, state: FSMContext):

        if message.document is not None:

            file_path = f"documents/{message.document.file_name}"

            await self.bot.download_file_by_id(message.document.file_id, file_path)

            data = {
                'type': 'document',
                "id": message.from_id,
            }

            with open(file_path, 'rb') as file:
                files = {'document': file}

                requests.post(
                    f'{os.environ.get("URL_PATH")}chats/', data=data, files=files)

            os.remove(file_path)
        elif message.photo:
            file_path = "output.png"
            photo = message.photo[-1]

            data = {
                'type': 'photo',
                "id": message.from_id,
            }

            await photo.download(file_path)

            with open(file_path, 'rb') as file:
                files = {'photo': file}
                requests.post(
                    f'{os.environ.get("URL_PATH")}chats/', data=data, files=files)

            os.remove(file_path)

        else:
            payload = {
                'type': 'text',
                "text": message.text,
                "id": message.from_id,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "username": message.from_user.username,
            }

            requests.post(
                f'{os.environ.get("URL_PATH")}chats/', data=payload)

    async def back(self, callback_query: types.CallbackQuery):
        markup = self.set_markup()
        await self.bot.send_message(callback_query.from_user.id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
        await self.state.OPTION.set()

    def register_handlers(self):

        self.dp.register_message_handler(
            self.start, commands=['start'], state='*')
        self.dp.register_message_handler(
            self.payments, state=self.state.PAYMENT)
        self.dp.register_message_handler(self.chat, content_types=[
                                         'photo', 'text', 'document'], state=self.state.CHAT)
        self.dp.register_callback_query_handler(self.back, text='back')
        return super().register_handlers()


bot = Bot(token=os.environ.get('TOKEN'), state=state.BaseState())
bot.run()
