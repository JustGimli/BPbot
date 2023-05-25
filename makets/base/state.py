from aiogram.dispatcher.filters.state import State, StatesGroup


class BaseState(StatesGroup):
    FIO = State()
    PHONE = State()
    OPTION = State()
