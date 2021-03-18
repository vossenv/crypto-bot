import asyncio
import logging
import random
import threading
import time
from datetime import datetime

import discord
from discord.ext.commands import Bot, MissingRequiredArgument


class CoinAssociation:

    def __init__(self, coin, membership):
        self.update(coin)
        self.membership = membership

    def update(self, coin):
        self.coin = coin.upper()
        self.last_update = datetime.now()


class CryptoBot(Bot):

    def __init__(self, coin, chat_id, command_roles, *args, **kwargs):
        super(CryptoBot, self).__init__(*args, **kwargs)
        self.coin = coin.upper()
        self.chat_id = chat_id
        self.command_roles = {c.lower() for c in command_roles}
        self.associations = {}
        self.logger = logging.getLogger("{} bot".format(coin))
        self.logger.info("Starting bot...")

    def set_coin(self, guild, coin):
        self.associations[guild].update(str(coin))

    async def ready(self):
        threading.Thread(target=self.update_memberships).start()
        await self.status_loop()

    async def status_loop(self):
        while True:
            r = random.random()
            for g, a in self.associations.items():
                await a.membership.edit(nick="#{0} {1} {2}".format(self.chat_id, a.coin, r))
                game = discord.Game("{} %".format(random.random() * 100))
                await self.change_presence(status=discord.Status.online, activity=game)
            await asyncio.sleep(2)

    def update_memberships(self):
        while True:
            for g in self.guilds:
                if g.id not in self.associations:
                    m = [u for u in g.members if u.id == self.user.id]
                    if not m:
                        self.logger.warning("No matching member id found for {}".format(g.id))
                        continue
                    elif len(m) > 1:
                        self.logger.warning("Multiple matches found for id for {} - using first match".format(g.id))
                    self.associations[g.id] = CoinAssociation(self.coin, m[0])
            time.sleep(60)


def create_bot(coin, chat_id, command_roles):
    bot = CryptoBot(command_prefix="!{} ".format(chat_id), coin=coin, chat_id=chat_id, command_roles=command_roles)

    @bot.event
    async def on_ready():
        bot.logger.info("{} is ready!".format(bot.coin))
        await bot.ready()

    @bot.command(name='set', help='Sets a specific coin by code')
    async def set_coin(ctx, shortcode):
        if not ctx.author.id == ctx.guild.owner_id:
            return
        elif not {r.name.lstrip('@').lower() for r in ctx.author.roles} & bot.command_roles:
            return
        try:
            bot.set_coin(ctx.guild.id, shortcode)
            await ctx.send("Set bot {0} to {1} successfully!".format(bot.chat_id, shortcode))
        except:
            await ctx.send("Error setting shortcode {}!".format(shortcode))

    @set_coin.error
    async def on_error(ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Missing required parameter: coin name - EG: !1 SET BTC")
        else:
            bot.logger.error("{} - {}".format(type(error), error.args[0]))
            raise error

    return bot
