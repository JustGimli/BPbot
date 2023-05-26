from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext


class PrimaryHandl:
    def __init__(self, bot: Bot, dp: Dispatcher, state) -> None:
        self.dp = dp
        self.bot = bot
        self.state = state

        self.register_handlers()

    def register_handlers(self):
        self.dp.register_message_handler(
            self.handler_document, state=self.state.DOCUMENT)

    async def handler_document(self, message: types.Message, state: FSMContext):
        await self.bot.send_message(message.from_id, "hello")
