import asyncio
from abc import ABC, abstractmethod
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


class AbstractBot(ABC):
    def __init__(self, token, state, start_message='Hello') -> None:

        # set bots
        self.bot = Bot(token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.start_message = start_message

        self.state = state

    @abstractmethod
    async def register_handlers(self):
        self.dp.register_message_handler(self.start, commands=['start'])

    async def start(self, message: types.Message):
        await self.bot.send_message(message.from_id, text=self.start_message)
        await self.bot.send_message(message.from_id, 'Введите ваше ФИО через пробел')
        await self.state.FIO.set()

    async def start_polling(self):
        await self.register_handlers()
        await self.dp.start_polling()

    def run(self):
        asyncio.run(self.start_polling())


class BaseBot(AbstractBot):
    def __init__(self, token, state,  start_message='Hello', ) -> None:
        super().__init__(token, start_message, state)

    def set_markup(self):

        markup = ReplyKeyboardMarkup(resize_keyboard=True)

        if self.primary:
            markup.add(
                KeyboardButton(
                    text='Первичная консультация'
                ))

        if self.secondary:
            markup.add(
                KeyboardButton(
                    text='Вторичная консультация'
                ))

        return markup

    async def get_fio(self, message: types.Message, state: FSMContext):
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

        async with state.proxy() as data:
            data['phone'] = message.contact.phone_number

        markup = self.set_markup()

        await self.bot.send_message(message.from_id, text='Выберите тип консультации: ', reply_markup=markup)
        await self.state.OPTION.set()

    async def set_option(self, message: types.Message, state: FSMContext):

        if message.text == 'Первичная консультация':
            await self.bot.send_message(message.from_id, '1Введите данные')
            await self.state.PRIMARY_CONST.set()
        elif message.text == 'Вторичная консультация':
            await self.bot.send_message(message.from_id, '2Введите данные')
            await self.state.CONSULTATION.set()
        else:
            self.bot.send_message(
                message.from_id, 'Извините такая опция отсутсвует')

    async def start_polling(self):
        self.dp.register_message_handler(self.get_fio, state=self.state.FIO)
        self.dp.register_message_handler(
            self.set_option, state=self.state.OPTION)
        self.dp.register_message_handler(self.get_phone, content_types=[
                                         types.ContentType.CONTACT], state=self.state.PHONE)
        return await super().start_polling()
