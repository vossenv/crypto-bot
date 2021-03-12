
import asyncio
import os
import random
import threading
import time

import discord
from discord.ext.commands import Bot

TOKEN = os.environ['TOKEN']


class CryptoBot(Bot):

    def __init__(self, *args, **kwargs):
        super(CryptoBot, self).__init__(*args, **kwargs)
        self.memberships = []

    async def ready(self):
        threading.Thread(target=self.update_memberships).start()
        await self.status_loop()

    async def status_loop(self):
        while True:
            r = random.random()
            for m in self.memberships:
                await m.edit(nick="BTC {}".format(r))

                game = discord.Game("{} %".format(random.random() * 100))
                await self.change_presence(status=discord.Status.online, activity=game)
            await asyncio.sleep(5)

    def update_memberships(self):
        while True:
            self.memberships.clear()
            for g in self.guilds:
                self.memberships.extend([b for b in g.members if b.id == self.user.id])
            time.sleep(60)


def create_bot():
    bot = CryptoBot(command_prefix='!')

    @bot.event
    async def on_ready():
        print("READY")
        await bot.ready()

    @bot.command(name='99', help='Responds with a random quote from Brooklyn 99')
    async def nine_nine(ctx):
        brooklyn_99_quotes = [
            'I\'m the human form of the 💯 emoji.',
            'Bingpot!',
            (
                'Cool. Cool cool cool cool cool cool cool, '
                'no doubt no doubt no doubt no doubt.'
            ),
        ]

        response = random.choice(brooklyn_99_quotes)
        await ctx.send(response)

    return bot


x = create_bot()
x.run(TOKEN)
