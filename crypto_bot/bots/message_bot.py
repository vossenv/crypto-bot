from crypto_bot.bots import bot_globals
from crypto_bot.bots.base_bot import BaseBot


class MessageBot(BaseBot):

    def __init__(self,
                 *args,
                 **kwargs):
        super(MessageBot, self).__init__(*args, **kwargs)

    async def ready(self):
        await self.update_nick()


def create_bot(config):
    bot = MessageBot(command_prefix="!",
                     token=config['token'],
                     name=config['name'],
                     avatar=config.get('avatar'),
                     case_insensitive=True)

    bot_globals.add_price_commands(bot)

    @bot.command(name='ath', help='Get all time high - !ath')
    async def ath(ctx, symbol):
        pass

    return bot
