from .makets.ABCbot import *


class Bot(AbstractBot):
    def __init__(self, token, start_message='Hello') -> None:
        super().__init__(token, start_message)

    async def hello(self, message: types.Message):
        await self.bot.send_message(message.from_id, 'asd')

    async def register_handlers(self):
        # self.dp.register_message_handler(self.hello)
        return await super().register_handlers()
       
