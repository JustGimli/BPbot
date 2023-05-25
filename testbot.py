from makets.base import BaseBot, BaseState
import os
from dotenv import load_dotenv
from aiogram.dispatcher.filters.state import State
from aiogram import types
from aiogram.dispatcher import FSMContext


class PrimaryCon(BaseState):
    PRIMARY_CONST = State()


class SecondaryCon(BaseState):
    CONSULTATION = State()


class Unit(PrimaryCon, SecondaryCon):
    pass


class Bot(BaseBot):
    def __init__(self, token, state,  start_message='Hello') -> None:
        self.primary = False
        self.secondary = False

        if isinstance(state, PrimaryCon):
            self.primary = True
            self.secondary = False

        if isinstance(state, SecondaryCon):
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
                self.init_cons, state=state.PRIMARY_CONST)
        if self.secondary:
            self.dp.register_message_handler(
                self.init_cons, state=state.CONSULTATION)
        return await super().register_handlers()


load_dotenv('.env.dev')

if (os.environ.get('PRIMARY_CON', False)):
    state = PrimaryCon()

    if (os.environ.get('SECONDARY_CON', False)):
        state = Unit()


elif os.environ.get('SECONDARY_CON', False):
    state = SecondaryCon()
else:
    state = BaseState()


bot = Bot(os.environ.get(
    'TOKEN', '5337418205:AAF64PcryZpAC61AY0eKNwpBCZD2LVTXA1c'), state=state)
bot.run()
