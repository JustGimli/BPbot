import asyncio
from abc import ABC, abstractmethod
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


class AbstractBot(ABC):
    @abstractmethod
    async def register_handlers(self):
        self.dp.register_message_handler(self.start, commands=['start'])

    async def start(self, message: types.Message):
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
                    text='Повторная консультация'
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

            await self.bot.send_message(message.from_id, text='Напишите ваш номер телефона или нажмите на кнопку "Поделиться номером".', reply_markup=markup)
            await self.state.PHONE.set()
        else:
            await self.bot.send_message(message.from_id, 'Извините, повторите попытку')

    async def get_phone(self, message: types.Message, state: FSMContext):

        async with state.proxy() as data:
            data['phone'] = message.contact.phone_number

        markup = self.set_markup()

        await self.bot.send_message(message.from_id, text='Спасибо! Выберите тип консультации: ', reply_markup=markup)
        await self.state.OPTION.set()

    async def set_option(self, message: types.Message, state: FSMContext):

        if message.text == 'Первичная консультация':

            text = '''Доступ к консультации открывается после оплаты.
Стоимость первичной онлайн-консультации составляет 3 000 рублей.
После оплаты у вас будет неделя, чтобы задать дополнительные вопросы'''

            await self.bot.send_message(message.from_id, text)
            await self.state.PRIMARY.set()

        elif message.text == 'Повторная консультация':

            text = '''Доступ к консультации открывается после оплаты.
Стоимость повторной онлайн-консультации составляет 3 000 рублей.
После оплаты у вас будет неделя, чтобы задать дополнительные вопросы'''

            await self.bot.send_message(message.from_id, text)
            await self.state.REPEAT.set()
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

    # def send_message(self, message: types.Message):
