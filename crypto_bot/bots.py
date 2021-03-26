import asyncio
import logging
import threading
import time
from random import random

import discord
from discord.ext.commands import Bot, MissingRequiredArgument


class CoinAssociation:

    def __init__(self, coin, membership):
        self.coin = coin
        self.update(coin)
        self.membership = membership

    def update(self, coin):
        self.coin = coin.upper()
        self.image = None


class CryptoBot(Bot):

    def __init__(self, coin, chat_id, command_roles, connector, *args, **kwargs):
        super(CryptoBot, self).__init__(*args, **kwargs)
        self.coin = coin.upper()
        self.chat_id = chat_id
        self.command_roles = {c.lower() for c in command_roles}
        self.associations = {}
        self.logger = logging.getLogger("{} bot".format(coin))
        self.logger.info("Starting bot...")
        self.connector = connector

    async def set_coin(self, guild, coin):
        coin = str(coin).lower()
        full = self.connector.coins.get(coin)
        if not full:
            raise discord.DiscordException("Invalid coin selection: {}".format(coin.upper()))
        self.associations[guild].update(coin)
        await self.update()
        return full

    async def ready(self):
        threading.Thread(target=self.update_memberships).start()
        await self.status_loop()

    async def status_loop(self):

        while True:
            try:
                await self.update()
                await asyncio.sleep(6)
            except Exception as e:
                self.logger.error(e)

    async def update(self):
        for g, a in self.associations.items():
            # if not a.image:
            #     a.image = await self.connector.get_icon(a.coin)
            #     await edit_server()
            # await self.user.edit(avatar=None)
            price, perc = await self.connector.get_ticker(a.coin)
            dir = ("↑" if perc >= 0 else "↓") if isinstance(perc, float) else ""
            await a.membership.edit(nick="!{0} {1} {2}".format(self.chat_id, a.coin, price))
            act = discord.Activity(type=discord.ActivityType.watching, name="{0} % {1}".format(perc, dir))
            await self.change_presence(status=discord.Status.online, activity=act)

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

    def describe(self):
        data = {}
        for a in self.associations.values():
            data[a.membership.guild.name] = a.membership.nick
        return data


def create_bot(coin, chat_id, command_roles, connector):
    bot = CryptoBot(command_prefix="!{} ".format(chat_id),
                    coin=coin,
                    chat_id=chat_id,
                    command_roles=command_roles,
                    connector=connector,
                    case_insensitive=True)

    @bot.event
    async def on_ready():
        bot.logger.info("#{} - {} is ready!".format(bot.chat_id, bot.coin))
        await bot.ready()

    @bot.command(name='feed', help='Get some soup')
    async def feed(ctx):
        if random() >= 0.7:
            await ctx.send("You may eat today {}, Qapla'!".format(ctx.author.name))
        else:
            await ctx.send("No soup for you!")

    @bot.command(name='set', help='Sets a specific coin by symbol. Usage: ![#] set DOGE - # indicates bot number')
    async def set_coin(ctx, symbol):
        if not ctx.author.id == ctx.guild.owner_id and \
                not {r.name.lstrip('@').lower() for r in ctx.author.roles} & bot.command_roles:
            return
        try:
            coin = await bot.set_coin(ctx.guild.id, symbol)
            await ctx.send("Set bot {0} to {1} - {2} successfully!"
                           .format(bot.chat_id, coin.symbol.upper(), coin.name))
        except discord.DiscordException as e:
            await ctx.send("Error: {}".format(e))

    @bot.command(name='price', help='Get a price. Usage: 1[#] price DOGE - # indicates bot number')
    async def get_price(ctx, symbol):
        try:
            s = await bot.connector.get_ticker(symbol)
            await ctx.send("{}: ${}, change: {}%".format(symbol.upper(), s[0], s[1]))
        except Exception as e:
            await ctx.send("Error: {}".format(e))

    @set_coin.error
    async def on_error(ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Missing required parameter: coin name - EG: !1 SET BTC")
        else:
            bot.logger.error("{} - {}".format(type(error), error.args[0]))
            raise error

    return bot
