from discord import Message

from crypto_bot.bots import bot_globals
from crypto_bot.bots.base_bot import BaseBot


class MessageBot(BaseBot):

    def __init__(self,
                 mappings,
                 *args,
                 **kwargs):
        super(MessageBot, self).__init__(*args, **kwargs)

        self.mappings = [dict(m) for m in mappings]
        self.mappings_by_channel = mc = {}

        for m in self.mappings:
            for c in m['read_channels']:
                if c not in mc:
                    mc[c] = []
                mc[c].extend(m['write_channels'])

    async def ready(self):
        self.cmd_callbacks = {c.name: c.callback for c in self.commands}
        await self.update_nick()

    async def handle_message(self, message):

        content = str(message.content)
        if content.startswith(self.command_prefix):
            cmd = content[1:].lower().strip()

        from_id = message.channel.id
        if from_id in self.mappings_by_channel:
            await self.message_channels(message.content, self.mappings_by_channel[from_id])


def create_bot(**kwargs):
    bot = MessageBot(command_prefix="!", **kwargs)
    bot_globals.add_shared_setup(bot)

    @bot.event
    async def on_message(message: Message, *args, **kwargs):
        await bot.handle_message(message)

    return bot
