import os
import json
import asyncio
import requests
from abc import ABC, abstractmethod
from aiogram import types,  Bot, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage


class AbstractBot(ABC):
    @abstractmethod
    async def register_handlers(self):
        # self.dp.register_message_handler(self.start, commands=['start'])
        pass

    async def start(self, message: types.Message, state: FSMContext):
        await state.reset_state()

        if message.text == '/start':

            if self.start_img is not None:
                await self.bot.send_photo(chat_id=message.chat.id, photo=self.start_img, caption=self.start_message)
            else:
                await self.bot.send_message(message.from_id, text=self.start_message)

            await self.bot.send_message(message.from_id, 'Пожалуйста, напишите ваши Фамилию, Имя и Отчество: 👇')
            await self.state.FIO.set()

    async def start_polling(self):
        await self.bot.delete_webhook()
        await self.register_handlers()
        await self.dp.start_polling()

    def run(self):
        asyncio.run(self.start_polling())


class BaseBot(AbstractBot):
    def __init__(self, token):
        self.bot = Bot(token)
        self._get_start_message()
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())

    def set_markup(self):

        markup = ReplyKeyboardMarkup(resize_keyboard=True)

        try:
            self.consultations = json.loads(os.environ.get('CONSULTATIONS'))
            for i in self.consultations.keys():
                markup.add(KeyboardButton(text=i))

            return markup
        except Exception as e:
            print(e)
            return None

    def send_create_user(self, req):
        requests.post(
            f'{os.environ.get("URL")}botusers/users/create/', data=req)

    def _get_start_message(self):
        try:
            data = requests.get(
                f'{os.environ.get("URL")}bots/message/', data={"token": os.getenv("TOKEN", None)}).json()
            self.start_message = data.get('start_message')
            self.start_img = data.get('bot_img', None)
        except:
            self.start_message = "Привет!"

        if self.start_message is None:
            self.start_message = "Привет!"

    async def get_fio(self, message: types.Message, state: FSMContext):
        text = message.text.strip(' ').split()

        # async with self.state.proxy() as data:
        #     data['user_message_count'] += 1

        if len(text) == 3:

            async with state.proxy() as data:
                data['first_name'] = text[0].strip()
                data['last_name'] = text[1].strip()

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                KeyboardButton(
                    text='Поделиться Номером',
                    request_contact=True
                )
            )

            await self.bot.send_message(message.from_id, text='Напишите ваш номер телефона или нажмите на кнопку "Поделиться номером".', reply_markup=markup)
            await self.state.PHONE.set()
        else:
            await self.bot.send_message(message.from_id, 'Извините, повторите попытку')

    async def get_phone(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['phone'] = message.contact.phone_number
            req = {'username': message.from_user.username,
                   "token": os.getenv("TOKEN", None),
                   "first_name": data['first_name'],
                   "last_name": data['last_name'],
                   "phone": data['phone'],
                   }

        self.send_create_user(req)

        markup = self.set_markup()

        await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
        await self.state.OPTION.set()

    async def get_phone_by_typing(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['phone'] = message.text
            req = {'username': message.from_user.username,
                   "token": os.getenv("TOKEN", None),
                   "first_name": data['first_name'],
                   "last_name": data['last_name'],
                   "phone": data['phone']
                   }

        self.send_create_user(req)
        markup = self.set_markup()

        await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
        await self.state.OPTION.set()

    async def set_option(self, message: types.Message, state: FSMContext):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton(text="Оплатить консультацию"))

        if message.text in self.consultations.keys():
            text = f'''Доступ к консультации открывается после оплаты.
Стоимость консультации составляет {self.consultations[message.text].get('cost', None)} рублей.
После оплаты у вас будет неделя, чтобы задать дополнительные вопросы.'''

            async with state.proxy() as data:
                data['cost'] = self.consultations[message.text].get(
                    'cost', None)
                data['days'] = self.consultations[message.text].get(
                    'days', None)

            await self.bot.send_message(message.from_id, text, reply_markup=markup)
            await self.state.PAYMENT.set()

        else:
            self.bot.send_message(
                message.from_id, 'Извините такая опция отсутсвует')

    async def start_polling(self):
        self.dp.register_message_handler(self.get_fio, state=self.state.FIO)
        self.dp.register_message_handler(
            self.set_option, state=self.state.OPTION)
        self.dp.register_message_handler(
            self.get_phone, content_types=[types.ContentType.CONTACT],  state=self.state.PHONE)
        self.dp.register_message_handler(
            self.get_phone_by_typing, content_types=[types.ContentType.TEXT],  state=self.state.PHONE)
        await super().start_polling()
