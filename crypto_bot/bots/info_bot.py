import datetime
import logging
import threading
import time
from random import random

import discord
from discord.ext.commands import Bot, CommandNotFound

from crypto_bot.bots import bot_globals

config_loader = None


class CoinAssociation:

    def __init__(self, coin, membership):
        self.coin = coin
        self.update(coin)
        self.membership = membership

    def update(self, coin):
        self.coin = coin.upper()
        self.image = None


class CryptoBot(Bot):

    def __init__(self, token, name, command_roles, indexer, *args, **kwargs):
        super(CryptoBot, self).__init__(*args, **kwargs)
        self.token = token
        self.name = name
        self.command_roles = {c.lower() for c in command_roles}
        self.logger = logging.getLogger("{} bot".format(self.name))
        self.logger.info("Starting {} bot...".format(self.name))
        self.indexer = indexer

    async def ready(self):
        await self.update_nick()

    async def update_nick(self):
        for g in self.guilds:
            m = [u for u in g.members if u.id == self.user.id]
            if not m:
                self.logger.warning("No matching member id found for {}".format(g.id))
                continue
            elif len(m) > 1:
                self.logger.warning("Multiple matches found for id for {} - using first match".format(g.id))

            act = discord.Activity(type=discord.ActivityType.watching, name="you")
            await m[0].edit(nick="{}".format(self.name))
            await self.change_presence(status=discord.Status.online, activity=act)


    async def start(self):
        await super().start(self.token)


def create_bot(token, name, command_roles, indexer):
    bot = CryptoBot(command_prefix="!",
                    token=token,
                    name=name,
                    command_roles=command_roles,
                    indexer=indexer,
                    case_insensitive=True)

    @bot.event
    async def on_ready():
        bot.logger.info("{} is ready!".format(bot.name))
        await bot.ready()

    @bot.command(name='feed', help='Get some soup')
    async def feed(ctx):
        if random() >= 0.7:
            await ctx.send("You may eat today {}, Qapla'!".format(ctx.author.name))
        else:
            await ctx.send("No soup for you!")

    @bot.command(name='info', help='Get coin info. Usage: 1[#] info DOGE - # indicates bot number')
    async def get_info(ctx, symbol):
        try:
            c = bot.indexer.get_coin(symbol, wait=True, info=True)
            message = \
                """
**Ticker**: {ticker}
**Name**: {name}
**Price**: ${price} / {change} %
**ATH**: ${ath} on {ath_date}
**Total Supply**: {supply}
**Circulating Supply**: {circulating}
**Percent Mined**: {mined}
**Market Cap**: {cap}
**Current Index**: {exchange}
**Homepage**: <{homepage}>
**Coingecko**: <{coingecko}>
**Development**: {repos}"""
            repos = c.info['repos']
            if repos:
                repos = ["<{}>".format(z) for z in c.info['repos']]
                if len(repos) > 1:
                    repos = "\n" + "\n".join(repos)
                else:
                    repos = repos[0]

            d = c.info['ath_date']
            if isinstance(d, datetime.datetime):
                d = d.strftime('%m/%d/%Y')

            mined = "N/A"
            supply = "Uncapped"
            circulating = "Unknown"
            market_cap = "Unknown"
            if c.info['circulating_coins']:
                circulating = "{:,}".format(round(c.info['circulating_coins']))
            if c.info['market_cap']:
                market_cap = "$" + "{:,}".format(c.info['market_cap'])
            if c.info['total_coins']:
                supply = "{:,}".format(round(c.info['total_coins']))
                if circulating != "Unknown":
                    mined = round(c.info['circulating_coins'] / c.info['total_coins'], 4) * 100
                    mined = str(mined) + "%"

            msg = message.format(
                image=c.info['image'],
                ticker=symbol.upper(),
                name=c.name,
                price=c.price,
                change=c.perc,
                ath=c.info['ath'],
                ath_date=d,
                supply=supply,
                mined=mined,
                circulating=circulating,
                cap=market_cap,
                exchange=c.last_exchange,
                homepage=c.info['homepage'],
                coingecko=c.info['coingecko'],
                repos=repos or "None provided"
            )

            if c.info['algorithm']:
                message += "\n**Hashing Algorithm**: {}".format(c.info['algorithm'])
            if c.info['block_time']:
                message += "\n**Block Time**: {} minutes".format(c.info['block_time'])

            await ctx.send(c.info['image'])
            await ctx.send(msg)
            desc = c.info['description']
            message = "**Description**: \n{description}"
            if not desc:
                await ctx.send("**Description**: None provided")
                return
            if len(desc) > 500:
                message += "... \nTruncated - for a longer description, see <{}> ".format(c.info['coingecko'])
            await ctx.send(message.format(description=desc[0:500]))

        except Exception as e:
            await ctx.send("Error: {}".format(e))

    @bot.command(name='price', help='Get a price. Usage: 1[#] price DOGE - # indicates bot number')
    async def get_price(ctx, symbol):
        await bot_globals.get_symbol_price(ctx, symbol)

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, CommandNotFound):
            try:
                int(ctx.invoked_with)
                return
            except Exception:
                await ctx.send(error.args[0])
        raise error

    return bot
