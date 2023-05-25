import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from dotenv import load_dotenv
from makets.base import base
from makets.primary.state import PrimaryCon
from makets.repeat.state import RepeatCon


class Bot(base.BaseBot):
    def __init__(self, token, state,  start_message='Hello') -> None:
        self.state = state
        self.primary = False
        self.secondary = False

        if isinstance(state, PrimaryCon):
            self.primary = True
            self.secondary = False

        if isinstance(state, RepeatCon):
            self.primary = False
            self.secondary = True

        if isinstance(state, Unit):
            self.primary = True
            self.secondary = True

        super().__init__(token, start_message, state)

    async def init_cons(self, message: types.Message, state: FSMContext):
        await self.bot.send_message(message.from_id, 'asd123')

    async def cons(self, message: types.Message, state: FSMContext):
        await self.bot.send_message(message.from_id, 'dsa')

    async def register_handlers(self):
        if self.primary:
            self.dp.register_message_handler(
                self.init_cons, state=self.state.PRIMARY_CONST)
        if self.secondary:
            self.dp.register_message_handler(
                self.init_cons, state=self.state.CONSULTATION)
        return await super().register_handlers()


class Unit(PrimaryCon, RepeatCon):
    pass


load_dotenv('.env.dev')

if (os.environ.get('PRIMARY_CON', False)):
    state = PrimaryCon()

    if (os.environ.get('REPEAT_CON', False)):
        state = Unit()


elif os.environ.get('REPEAT_CON', False):
    state = RepeatCon()
else:
    state = base.BaseState()


bot = Bot(os.environ.get(
    'TOKEN', '5337418205:AAF64PcryZpAC61AY0eKNwpBCZD2LVTXA1c'), state=state)
bot.run()
