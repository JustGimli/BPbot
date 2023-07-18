import os
import json
import asyncio
import requests
from abc import ABC, abstractmethod
from aiogram import types,  Bot, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import CantGetUpdates


class AbstractBot(ABC):
    @abstractmethod
    async def register_handlers(self):
        # self.dp.register_message_handler(self.start, commands=['start'])
        pass

    async def get_avatar(self, message: types.Message):
        user_id = message.from_user.id

        try:
            user = await self.bot.get_chat(user_id)
            photo = user.photo.big_file_id
            if photo:
                file = await self.bot.get_file(photo)
                avatar_url = file.file_path

                response = requests.get(
                    f"https://api.telegram.org/file/bot{os.environ.get('TOKEN')}/{avatar_url}")
                response.raise_for_status()

                return (f'{message.user.id}.jpg', response.content)
        except:
            return None

    async def start(self, message: types.Message, state: FSMContext):
        await state.reset_state()

        if message.text == '/start':

            if self.start_img:
                await self.bot.send_photo(chat_id=message.chat.id, photo=self.start_img, caption=self.start_message)
            else:
                await self.bot.send_message(message.from_id, text=self.start_message)

            data = requests.post(f'{os.environ.get("URL_PATH")}botusers/me/',
                                 {'username': message.from_user.username, "token": os.getenv("TOKEN", None)})
            if data.status_code == 200:
                markup = self.set_markup()
                await self.bot.send_message(message.from_id, text='Выберите тип консультации: ', reply_markup=markup)
                await self.state.OPTION.set()
            else:
                if int(os.getenv('IS_FIO')):
                    await self.bot.send_message(message.from_id, 'Пожалуйста, напишите ваши Фамилию, Имя и Отчество: 👇')
                    await self.state.FIO.set()
                elif int(os.getenv('IS_PHONE')):
                    await self.bot.send_message(message.from_id, 'Пожалуйста, напишите ваши Фамилию, Имя и Отчество: 👇')
                    await self.state.PHONE.set()
                elif json.loads(os.environ.get('PARAMS')) != '' and json.loads(os.environ.get('PARAMS')):
                    async with state.proxy() as data:
                        data['params'] = json.loads(os.environ.get('PARAMS'))
                        data['res_params'] = {}
                        params = data['params']

                        for key, value in params.items():
                            del params[key]
                            data['current'] = key
                            data['params'] = params
                            await self.bot.send_message(message.from_id, text=value, reply_markup=types.ReplyKeyboardRemove())
                            await self.state.PARAMS.set()
                            break
                else:
                    req = {'username': message.from_user.username,
                           "token": os.getenv("TOKEN", None),
                           }

                    self.send_create_user(req)

                    markup = self.set_markup()

                    await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
                    await self.state.OPTION.set()

    async def start_polling(self):
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
            f'{os.environ.get("URL_PATH")}botusers/create/', data=req)

    def _get_start_message(self):
        try:
            data = requests.get(
                f'{os.environ.get("URL_PATH")}bots/message/', data={"token": os.getenv("TOKEN", None)}).json()
            self.start_message = data.get('start_message')
            self.start_img = data.get('bot_img', None)

        except:
            self.start_message = "Привет!"
            self.start_img = None

        if self.start_message is None:
            self.start_message = "Привет!"

    async def get_fio(self, message: types.Message, state: FSMContext):
        text = message.text.strip().split(" ")

        async with state.proxy() as data:
            data['first_name'] = text[0].strip()
            data['last_name'] = text[1].strip()
            data['surname'] = text[2].strip() if len(text) > 1 else ""

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton(
                text='Поделиться Номером',
                request_contact=True
            )
        )
        if (int(os.environ.get('IS_PHONE'))):
            await self.bot.send_message(message.from_id, text='Напишите ваш номер телефона или нажмите на кнопку "Поделиться номером".', reply_markup=markup)
            await self.state.PHONE.set()
        elif json.loads(os.environ.get('PARAMS')) != '' and json.loads(os.environ.get('PARAMS')):
            async with state.proxy() as data:
                data['params'] = json.loads(os.environ.get('PARAMS'))
                data['res_params'] = {}
                params = data['params']

                for key, value in params.items():
                    del params[key]
                    data['current'] = key
                    data['params'] = params
                    await self.bot.send_message(message.from_id, text=value, reply_markup=types.ReplyKeyboardRemove())
                    await self.state.PARAMS.set()
                    break
        else:
            async with state.proxy() as data:
                req = {'username': message.from_user.username,
                       "token": os.getenv("TOKEN", None),
                       "first_name": data['first_name'],
                       "last_name": data['last_name'],
                       'surname': data['surname'],
                       }

            self.send_create_user(req)

            markup = self.set_markup()

            await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
            await self.state.OPTION.set()

    async def get_phone(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['phone'] = message.contact.phone_number
            params = json.loads(os.environ.get('PARAMS'))

            if params != '' and params:
                data['params'] = params
                data['res_params'] = {}

                for key, value in params.items():
                    del params[key]
                    data['current'] = key
                    data['params'] = params
                    await self.bot.send_message(message.from_id, text=value, reply_markup=types.ReplyKeyboardRemove())
                    await self.state.PARAMS.set()
                    break
            else:
                req = {'username': message.from_user.username,
                       "token": os.getenv("TOKEN", None),
                       "first_name": data['first_name'],
                       "last_name": data['last_name'],
                       "phone": data['phone'],
                       'surname': data['surname'],
                       'photo': await self.get_avatar(message)
                       }

                self.send_create_user(req)

                markup = self.set_markup()

                await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
                await self.state.OPTION.set()

    async def get_phone_by_typing(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['phone'] = message.text
            params = json.loads(os.environ.get('PARAMS'))
            if params != '' and params:
                data['params'] = params
                data['res_params'] = {}
                params = data['params']

                for key, value in params.items():
                    del params[key]
                    data['current'] = key
                    data['params'] = params
                    await self.bot.send_message(message.from_id, text=value, reply_markup=types.ReplyKeyboardRemove())
                    await self.state.PARAMS.set()
                    break

            else:
                req = {'username': message.from_user.username,
                       "token": os.getenv("TOKEN", None),
                       "first_name": data['first_name'],
                       "last_name": data['last_name'],
                       "phone": data['phone'],
                       'surname': data['surname'],
                       'photo': await self.get_avatar(message)
                       }

                self.send_create_user(req)

                markup = self.set_markup()

                await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
                await self.state.OPTION.set()

    async def handle_params(self, message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            if data.get('current', None):

                data['res_params'].update(
                    {data['current']: message.text})

                data['current'] = False

            if data['params']:
                params = data['params']

                for key, value in params.items():
                    del params[key]
                    data['current'] = key
                    data['params'] = params
                    await self.bot.send_message(message.from_id, text=value)
                    break

            else:
                req = {'username': message.from_user.username,
                       "token": os.getenv("TOKEN", None),
                       "first_name": data['first_name'],
                       "last_name": data['last_name'],
                       "phone": data['phone'],
                       "params": json.dumps(data['res_params']),
                       'surname': data['surname'],
                       'photo': await self.get_avatar(message)
                       }

                self.send_create_user(req)

                markup = self.set_markup()
                await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
                await self.state.OPTION.set()

    async def set_option(self, message: types.Message, state: FSMContext):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton(text="Оплатить консультацию"))
        markup.add(KeyboardButton(text="Назад"))

        if message.text in self.consultations.keys():
            text = f'''Доступ к консультации открывается после оплаты.
Стоимость консультации составляет {self.consultations[message.text].get('cost', None)} рублей.
После оплаты у вас будет неделя, чтобы задать дополнительные вопросы.'''

            async with state.proxy() as data:
                data['cost'] = self.consultations[message.text].get(
                    'cost', None)
                data['days'] = self.consultations[message.text].get(
                    'days', None)
                data['cons_id'] = self.consultations[message.text].get(
                    'id', None)
                data['cons_name'] = message.text

            await self.bot.send_message(message.from_id, text, reply_markup=markup)
            await self.state.PAYMENT.set()

        else:
            await self.bot.send_message(
                message.from_id, 'Извините такая опция отсутсвует')

    async def start_polling(self):
        self.dp.register_message_handler(self.get_fio, state=self.state.FIO)
        self.dp.register_message_handler(
            self.handle_params, state=self.state.PARAMS)
        self.dp.register_message_handler(
            self.set_option, state=self.state.OPTION)
        self.dp.register_message_handler(
            self.get_phone, content_types=[types.ContentType.CONTACT],  state=self.state.PHONE)
        self.dp.register_message_handler(
            self.get_phone_by_typing, content_types=[types.ContentType.TEXT],  state=self.state.PHONE)
        await super().start_polling()
