import asyncio
import logging
import threading
import time

import discord
from discord.ext.commands import Bot, MissingRequiredArgument, CommandNotFound

from crypto_bot.bots import bot_globals
from crypto_bot.error import CoinNotFoundException


class CoinAssociation:

    def __init__(self, coin, membership):
        self.coin = coin
        self.update(coin)
        self.membership = membership

    def update(self, coin):
        self.coin = coin.upper()
        self.image = None


class CryptoPriceBot(Bot):

    def __init__(self, token, coin, avatar, chat_id, command_roles, indexer, *args, **kwargs):
        super(CryptoPriceBot, self).__init__(*args, **kwargs)
        self.token = token
        self.coin = coin.upper()
        self.avatar = avatar
        self.chat_id = chat_id
        self.command_roles = {c.lower() for c in command_roles}
        self.associations = {}
        self.logger = logging.getLogger("{} bot".format(coin))
        self.logger.info("Starting {} bot...".format(self.coin))
        self.indexer = indexer


    async def set_coin(self, guild, symbol):
        symbol = str(symbol).lower()
        coin = self.indexer.get_coin(symbol, wait=True)
        self.associations[guild].update(symbol)
        await self.update()
        return coin

    async def ready(self):
        if self.avatar:
            self.logger.info("Updating avatar to: {}".format(self.avatar))
            with open(self.avatar, 'rb') as image:
                await self.user.edit(avatar=image.read())
                self.logger.info("Updated avatar")
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

    async def start(self):
        await super().start(self.token)


def create_bot(token, coin, avatar, chat_id, command_roles, indexer):
    bot = CryptoPriceBot(command_prefix="!{} ".format(chat_id.lstrip("0")),
                         token=token,
                         coin=coin,
                         avatar=avatar,
                         chat_id=chat_id,
                         command_roles=command_roles,
                         indexer=indexer,
                         case_insensitive=True)

    @bot.event
    async def on_ready():
        bot.logger.info("#{} - {} is ready!".format(bot.chat_id, bot.coin))
        await bot.ready()

    @bot.command(name='set', help='Sets a specific coin by symbol. Usage: ![#] set DOGE - # indicates bot number')
    async def set_coin(ctx, symbol):
        if not ctx.author.id == ctx.guild.owner_id and \
                not {r.name.lstrip('@').lower() for r in ctx.author.roles} & bot.command_roles:
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

    @bot.command(name='price', help='Get a price. Usage: 1[#] price DOGE - # indicates bot number')
    async def get_price(ctx, symbol):
        await bot_globals.get_symbol_price(ctx, symbol)

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, CommandNotFound):
            if ctx.invoked_with.lower() in {'feed', 'info'}:
                await ctx.send("Command moved - use !{} instead".format(ctx.invoked_with))
                return
            await ctx.send(error.args[0])
        raise error

    return bot
