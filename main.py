import os
from aiogram import types
from aiogram.dispatcher import FSMContext

from dotenv import load_dotenv
import requests
# from makets.base import state
from makets.base import base, state
from makets.primary import primary_state, primary_handl
from makets.repeat import repeat_state
# from aiogram.utils.exceptions import CantGetUpdates````

# import requests


# class TestBot(base.BaseBot):
#     def __init__(self, token, state,  start_message) -> None:

#         # set bot
#         self.state = state
#         self.bot = Bot(token)
#         self.dp = Dispatcher(self.bot, storage=MemoryStorage())
#         self.dp.skip_updates()
#         self.start_message = start_message
#         self.primary = False
#         self.secondary = False

#         if isinstance(state, primary_state.PrimaryCon):
#             self.primary = True
#             self.secondary = False
#             primary_handl.PrimaryHandl(
#                 bot=self.bot, state=self.state, dp=self.dp)

#         if isinstance(state, repeat_state.RepeatCon):
#             self.primary = False
#             self.secondary = True

#         if isinstance(state, Unit):
#             self.primary = True
#             self.secondary = True

#     async def primary_start(self, message: types.Message, state: FSMContext):
#         try:
#             async with state.proxy() as data:
#                 requests.post(f'{os.getenv("URL")}chats/create/', {
#                     'chat_id': message.chat.id,
#                     'phone': data['phone'],
#                     'token': os.environ.get('TOKEN'),
#                 })
#         except Exception as e:
#             print(e)

#         try:
#             await self.set_webhook()
#         except CantGetUpdates as e:
#             await self.bot.delete_webhook()

#         try:
#             requests.post(f'{os.getenv("URL")}chats/bot/', {
#                 'chat_id': message.chat.id,
#                 'token': os.environ.get('TOKEN')
#             })

#             requests.post(f'{os.getenv("URL")}chats/consultation/create/', {
#                 "token": os.environ.get('TOKEN'),
#                 'username': message.from_user.username,
#                 "consultation_type": "primary",
#             })
#         except requests.exceptions.HTTPError as e:
#             print(e)

#         await self.bot.send_message(message.from_id, 'Начало:')
#         await self.state.DOCUMENT.set()

#     # async def handle_message(self, message: types.Message, state: FSMContext):

#     async def repeat_start(self, message: types.Message, state: FSMContext):
#         await self.bot.send_message(message.from_id, 'dsa')

#     async def register_handlers(self):
#         if self.primary:
#             self.dp.register_message_handler(
#                 self.primary_start, state=self.state.PRIMARY)
#         if self.secondary:
#             self.dp.register_message_handler(
#                 self.repeat_start, state=self.state.REPEAT)
#         return await super().register_handlers()

#     async def set_webhook(self):
#         WEBHOOK_URL = f"{os.getenv('URL')}chats/"

#         await self.bot.delete_webhook(drop_pending_updates=True)

#         await self.bot.set_webhook(WEBHOOK_URL)


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
                    if os.environ.get("FIO") and data['days']:
                        description = f'Консультация от {os.environ.get("FIO")}. Период {data["days"]} дней.'
                    else:
                        description = "Консультация"
                link = requests.post(
                    f'{os.environ.get("URL")}payments/link/', data={"id": os.getenv("ID", None),
                                                                    'username': message.from_user.username,
                                                                    'cost': cost,
                                                                    "description": description,
                                                                    'user_id': message.from_id
                                                                    }).json().get('link')
            except requests.exceptions.RequestException:
                link = None

            await self.bot.send_message(message.from_id, f'Ссылка для оплаты: {link}.')
        else:
            await state.reset_state()
            await self.bot.send_message(message.from_id, "Команда не разпознана введите /start для начала диалога", reply_markup=types.ReplyKeyboardRemove())

    def register_handlers(self):
        self.dp.register_message_handler(
            self.start, commands=['start'], state='*')
        self.dp.register_message_handler(
            self.payments, state=self.state.PAYMENT)
        return super().register_handlers()


bot = Bot(token=os.environ.get('TOKEN'), state=state.BaseState())
bot.run()
