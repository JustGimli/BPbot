import asyncio
import uvloop
# from aiologger import Logger
# from aiologger.handlers.files import AsyncFileHandler
from abc import ABC, abstractmethod
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from .state import BotState


class AbstractBot(ABC):
    def __init__(self, token, start_message='Hello', state=BotState) -> None:

        # set bots
        self.bot = Bot(token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.start_message = start_message

        # add handler
       # self.logger = Logger.with_default_handlers()
       # self.logger.add_handler(AsyncFileHandler(filename="bot.log"))

        # set state
        self.state = state

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @abstractmethod
    async def register_handlers(self):
        # self.logger.info("INFO: register message handlers")
        self.dp.register_message_handler(self.start, commands=['start'])
        self.dp.register_message_handler(self.get_fio, state=self.state.FIO)
        self.dp.register_message_handler(self.get_phone, content_types=[
                                         types.ContentType.CONTACT], state=self.state.PHONE)

    async def start(self, message: types.Message):
       # self.logger.info(
        #   f"INFO: Start message from user {message.from_id}")
        await self.bot.send_message(message.from_id, text=self.start_message)
        await self.bot.send_message(message.from_id, 'Введите ваше ФИО через пробел')
        await self.state.FIO.set()

    async def get_fio(self, message: types.Message, state: FSMContext):
        # self.logger.info(f"INFO: {message.text}")
        text = message.text.strip(' ').split()

        if len(text) == 3:

            async with state.proxy() as data:
                data['fio'] = ''.join(text)

            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(
                KeyboardButton(
                    text='Поделиться Номером',
                    request_contact=True
                )
            )

            await self.bot.send_message(message.from_id, text='Хорошо, теперь введите телефон', reply_markup=markup)
            await self.state.PHONE.set()
        else:
            await self.bot.send_message(message.from_id, 'Извините, повторите попытку')

    async def get_phone(self, message: types.Message, state: FSMContext):
        # self.logger.info(f'INFO: phone: {message.contact.phone_number}')

        async with state.proxy() as data:
            data['phone'] = message.contact.phone_number

        await self.bot.message(message.from_id, 'ok')

    async def start_polling(self):
        await self.register_handlers()
        await self.dp.start_polling()

    def run(self):
        asyncio.run(self.start_polling())
