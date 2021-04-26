import logging
import threading
import time
from copy import deepcopy
from datetime import datetime, timedelta
from random import random

import discord
import pytz
from dateutil.parser import parse, ParserError
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


class Countdown():

    def __init__(self, alert_time, name, alert_date=None, message=None):

        self.alert_date = ad = self.parse_date(alert_date).date() if alert_date else None
        self.alert_time = self.parse_date(alert_time)
        if self.alert_date is not None:
            self.alert_time = self.alert_time.replace(year=ad.year, month=ad.month, day=ad.day)
        self.message = message
        self.name = name
        self.logger = logging.getLogger(name)
        self.notifications = [5, 0]
        threading.Thread(target=self.run).start()

        self.check_time()

    def check_time(self) -> timedelta:
        now = datetime.utcnow()
        if self.alert_date is None:
            z = datetime.combine(now.date(), self.alert_time.time()) - now
            if z.total_seconds() < 0:
                z = datetime.combine(now.date() + timedelta(days=1), self.alert_time.time()) - now
            return z
        return self.alert_time - pytz.timezone("UTC").localize(now)

    def parse_date(self, date_str) -> datetime:
        try:
            date_str = parse(date_str, ignoretz=True)
            return pytz.timezone("UTC").localize(date_str)
        except ParserError:
            raise AssertionError(
                "Invalid time format {} - please specific in 24 hour %H:%M:%S".format(date_str))

    def get_delta(self):
        return round(self.check_time().total_seconds() / 60)

    def get_message(self):
        return "Alert! {} minutes to {}!".format(self.get_delta(), self.name)

    def run(self):
        timeslots = deepcopy(self.notifications)
        while True:
            t = self.get_delta()
            if timeslots and t <= timeslots[0]:
                timeslots.pop(0)
                if not timeslots:
                    msg = self.message
                    self.logger.info(msg)
                    if not self.alert_date:
                        timeslots = deepcopy(self.notifications)
                    else:
                        break
                else:
                    msg = self.get_message()
                    self.logger.info(msg)
            time.sleep(30)


class CryptoBot(Bot):

    def __init__(self, token, name, avatar, countdowns, command_roles, indexer, *args, **kwargs):
        super(CryptoBot, self).__init__(*args, **kwargs)
        self.token = token
        self.name = name
        self.avatar = avatar
        self.countdowns = [Countdown(**c) for c in countdowns]
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
            if self.avatar:
                self.logger.info("Updating avatar to: {}".format(self.avatar))
                with open(self.avatar, 'rb') as image:
                    await self.user.edit(avatar=image.read())
                    self.logger.info("Updated avatar")

    async def start(self):
        await super().start(self.token)


def create_bot(token, name, avatar, countdowns, command_roles, indexer):
    bot = CryptoBot(command_prefix="!",
                    token=token,
                    name=name,
                    avatar=avatar,
                    countdowns=countdowns,
                    command_roles=command_roles,
                    indexer=indexer,
                    case_insensitive=True)

    @bot.event
    async def on_ready():
        bot.logger.info("{} is ready!".format(bot.name))
        await bot.ready()

    @bot.command(name='feed', help='Get some soup - !feed')
    async def feed(ctx):
        if random() >= 0.7:
            await ctx.send("You may eat today {}, Qapla'!".format(ctx.author.name))
        else:
            await ctx.send("No soup for you!")

    @bot.command(name='info', help='Get coin info. Usage: !info DOGE')
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
            if isinstance(d, datetime):
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
                    mined = round(c.info['circulating_coins'] / c.info['total_coins'] * 100, 2)
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

    @bot.command(name='price', help='Get a price. Usage: !price doge')
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
