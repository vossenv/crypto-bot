from crypto_bot.bots import bot_globals
from crypto_bot.bots.base_bot import BaseBot


class MessageBot(BaseBot):

    def __init__(self,
                 *args,
                 **kwargs):
        super(MessageBot, self).__init__(*args, **kwargs)

    async def ready(self):
        await self.update_nick()


def create_bot(**kwargs):
    bot = MessageBot(command_prefix="!", **kwargs)

    bot_globals.add_price_commands(bot)

    @bot.command(name='ath', help='Get all time high - !ath')
    async def ath(ctx, symbol):
        pass

    return bot
