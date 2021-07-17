import asyncio
import logging
import threading
import time

import discord
from discord.ext.commands import MissingRequiredArgument

from crypto_bot.bots import bot_globals
from crypto_bot.bots.base_bot import BaseBot
from crypto_bot.error import CoinNotFoundException


class CoinAssociation:

    def __init__(self, coin, membership):
        self.coin = coin
        self.update(coin)
        self.membership = membership

    def update(self, coin):
        self.coin = coin.upper()
        self.image = None


class PriceBot(BaseBot):

    def __init__(self, coin, chat_id, command_roles, indexer, *args, **kwargs):
        super(PriceBot, self).__init__(name=coin, *args, **kwargs)
        self.coin = coin.upper()
        self.chat_id = chat_id
        self.command_roles = self.parse_command_roles(command_roles)
        self.associations = {}
        self.indexer = indexer

    async def set_coin(self, guild, symbol):
        symbol = str(symbol).lower()
        coin = self.indexer.get_coin(symbol, wait=True)
        self.associations[guild].update(symbol)
        self.logger = logging.getLogger("{} bot".format(symbol.upper()))
        await self.update()
        return coin

    async def ready(self):
        threading.Thread(target=self.update_memberships).start()
        await self.status_loop()

    async def status_loop(self):
        while True:
            await self.update()
            await asyncio.sleep(0.5)

    async def update(self):
        for g, a in self.associations.items():
            try:
                c = self.indexer.get_coin(a.coin)
                act = discord.Activity(type=discord.ActivityType.watching, name="{0} % {1}".format(c.perc, c.direction))
                await a.membership.edit(nick="!{0} {1} {2}".format(self.chat_id, a.coin, c.price))
                await self.change_presence(status=discord.Status.online, activity=act)
            except Exception as e:
                self.logger.error(e)

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


def create_bot(**kwargs):
    bot = PriceBot(command_prefix="!{} ".format(kwargs['chat_id'].lstrip("0")), **kwargs)
    bot_globals.add_shared_setup(bot)
    bot_globals.add_price_commands(bot)

    @bot.command(name='set', help='Sets a specific coin by symbol. Usage: ![#] set DOGE - # indicates bot number')
    async def set_coin(ctx, symbol):
        if not bot.user_role_allowed(ctx):
            await ctx.send("You do not have permission to use this function")
            return
        try:
            await ctx.send("Attempting to set coin to {}".format(symbol))
            c = await bot.set_coin(ctx.guild.id, symbol)
            cl = bot_globals.config_loader
            if cl.is_home_id(ctx.guild.id):
                cl.update_bot_coin(bot.token, symbol)
            await ctx.send("Set bot #{} to {} - {} successfully! - indexed from {}"
                           .format(bot.chat_id, c.symbol.upper(), c.name or c.coin_id, c.last_exchange))
        except CoinNotFoundException as e:
            await ctx.send(e)
        except Exception as e:
            await ctx.send("An unexpected error occured")
            bot.logger.error(e)

    @set_coin.error
    async def on_error(ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Missing required parameter: coin name - EG: !1 SET BTC")
        else:
            bot.logger.error("{} - {}".format(type(error), error.args[0]))
            raise error

    return bot
