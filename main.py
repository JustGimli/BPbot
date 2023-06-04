import os
from aiogram import types, Bot, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
from makets.base import state
from makets.base import base
from makets.primary import primary_state, primary_handl
from makets.repeat import repeat_state
from aiogram.utils.exceptions import ConflictError, CantGetUpdates


class TestBot(base.BaseBot):
    def __init__(self, token, state,  start_message='Hello') -> None:

        # set bot
        self.state = state
        self.bot = Bot(token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.start_message = start_message

        self.primary = False
        self.secondary = False

        if isinstance(state, primary_state.PrimaryCon):
            self.primary = True
            self.secondary = False
            primary_handl.PrimaryHandl(
                bot=self.bot, state=self.state, dp=self.dp)

        if isinstance(state, repeat_state.RepeatCon):
            self.primary = False
            self.secondary = True

        if isinstance(state, Unit):
            self.primary = True
            self.secondary = True

    async def primary_start(self, message: types.Message, state: FSMContext):

        try:
            await self.set_webhook()
        except CantGetUpdates as e:
            print(e)

        await self.bot.send_message(message.from_id, 'asd123')

    async def repeat_start(self, message: types.Message, state: FSMContext):
        await self.bot.send_message(message.from_id, 'dsa')

    async def register_handlers(self):
        if self.primary:
            self.dp.register_message_handler(
                self.primary_start, state=self.state.PRIMARY)
        if self.secondary:
            self.dp.register_message_handler(
                self.repeat_start, state=self.state.REPEAT)
        return await super().register_handlers()

    async def set_webhook(self):
        await self.bot.delete_webhook(drop_pending_updates=True)
        print(os.getenv('WEBHOOK_URL'))

        try:
            await self.bot.set_webhook(url=os.getenv('WEBHOOK_URL'))
        except ConflictError:
            pass


class Unit(primary_state.PrimaryCon, repeat_state.RepeatCon):
    pass


load_dotenv('.env')

if (os.environ.get('PRIMARY_CON', True)):
    state = primary_state.PrimaryCon()

    if (os.environ.get('REPEAT_CON', True)):
        state = Unit()


elif os.environ.get('REPEAT_CON', True):
    state = repeat_state.RepeatCon()
else:
    state = state.BaseState()


bot = TestBot(token=os.environ.get(
    'TOKEN', '5337418205:AAF64PcryZpAC61AY0eKNwpBCZD2LVTXA1c'), state=state)
bot.run()
