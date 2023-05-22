from aiogram.dispatcher.filters.state import State, StatesGroup


class BotState(StatesGroup):
    FIO = State()
    PHONE = State()
