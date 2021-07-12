import asyncio
import random
from datetime import datetime

from crypto_bot.bots import bot_globals
from crypto_bot.bots.base_bot import BaseBot
from crypto_bot.countdown import Countdown
from crypto_bot.resources.rules import RULES


class InfoBot(BaseBot):

    def __init__(self,
                 indexer,
                 twitter_collector=None,
                 countdowns=None,
                 twitter_notifications=None,
                 new_coin_notifications=None,
                 *args,
                 **kwargs):
        super(InfoBot, self).__init__(*args, **kwargs)
        countdowns = countdowns or []
        self.countdowns = [Countdown(**c, callback=self.message_channels) for c in countdowns]
        self.new_coin_notifications = new_coin_notifications
        self.twitter_notifications = twitter_notifications
        self.indexer = indexer
        self.twitter_collector = twitter_collector

        if self.twitter_notifications and not self.twitter_collector:
            raise AssertionError("Cannot use twitter notifications without twitter configuration")

    async def ready(self):
        await self.update_nick()
        for c in self.countdowns:
            asyncio.ensure_future(c.run_loop())
        if self.new_coin_notifications:
            asyncio.ensure_future(self.check_new_coins())
        if self.twitter_notifications:
            asyncio.ensure_future(self.check_new_tweets())

    async def check_new_tweets(self):

        tweets = {u: None for u in self.twitter_notifications['users']}
        channels = self.twitter_notifications['channels']
        tag_ids = self.twitter_notifications.get('tags')
        tags = " ".join(["<@{}>".format(t) for t in tag_ids]) if tag_ids else ''
        startup = True
        while True:
            try:
                for u, i in tweets.items():
                    for k, s in enumerate(self.twitter_collector.get_latest(u, i)):
                        if k == 0:
                            tweets[u] = s.id
                        if startup:
                            continue
                        tweet = "\n **New tweet: {} (@{})** {} \n https://twitter.com/{}/status/{}" \
                            .format(s.user.name, u, tags, u, s.id)

                        if s.in_reply_to_status_id:
                            tweet += "\n in reply to: https://twitter.com/{}/status/{}".format(
                                s.in_reply_to_screen_name, s.in_reply_to_status_id)

                        await self.message_channels(tweet, channels)

                startup = False

            except Exception as e:
                self.logger.error("Warning: failed to fetch tweets for user {}: {}".format("", e))
            await asyncio.sleep(self.twitter_collector.update_rate)

    async def check_new_coins(self):
        while True:
            try:
                new_coins_by_exch = self.indexer.check_new_coins()
                for e, coins in new_coins_by_exch.items():
                    for c in coins:
                        info = self.indexer.get_coin(c, wait=True, info=True).info
                        msg = "New coin {}/{} added to exchange: {}!".format(c.upper(), info['name'], e)
                        self.logger.info(msg)
                        await self.message_channels(msg, self.new_coin_notifications['channels'])
            except Exception as e:
                self.logger.error("Error checking new coins: {}".format(e))
            self.indexer.clear_new_coins()
            await asyncio.sleep(360)


def create_bot(**kwargs):
    bot = InfoBot(command_prefix="!", **kwargs)
    bot_globals.add_shared_setup(bot)
    bot_globals.add_price_commands(bot)

    @bot.command(name='ath', help='Get all time high - !ath')
    async def ath(ctx, symbol):
        try:
            c = bot.indexer.get_coin(symbol, wait=True, info=True)
            d = c.info['ath_date']
            if isinstance(d, datetime):
                d = d.strftime('%m/%d/%Y')
            msg = "**ATH**: ${ath} on {ath_date} for {id}/{name} (as reported by CoinGecko)".format(
                ath=c.info['ath'],
                ath_date=d,
                id=symbol.upper(),
                name=c.name or c.coin_id
            )
            await ctx.send(msg)
        except Exception as e:
            bot.logger.error("Error in commmand ath: {}".format(e))
            await ctx.send("Error: {}".format(e))

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
            bot.logger.error("Error in commmand get_info: {}".format(e))
            await ctx.send("Error: {}".format(e))

    @bot.command(name='feed', help='Get some soup - !feed')
    async def feed(ctx):
        try:
            if random.random() >= 0.7:
                await ctx.send("You may eat today {}, Qapla'!".format(ctx.author.name))
            else:
                await ctx.send("https://tenor.com/view/seinfeld-soupnazi-nosoup-gif-5441633")
        except Exception as e:
            bot.logger.error("Error in commmand feed: {}".format(e))
            await ctx.send("Error: {}".format(e))

    @bot.command(name='rule', help='Rule of acquisition - !rule or !rule #')
    async def rule(ctx, num=None):
        try:

            num = str(num) if num else random.choice(list(RULES.keys()))

            try:
                if "." in num:
                    raise ValueError
                int(num)
            except (ValueError, TypeError):
                await ctx.send("{} is not a rule number, you fool!".format(num))
                return

            rule = RULES.get(num)
            if rule:
                await ctx.send("**Rule of Acquisition #{}**: {}".format(num, rule))
            else:
                await ctx.send("Sorry, rule #{} has never been revealed to us".format(num))

        except Exception as e:
            bot.logger.error("Error in commmand new coins: {}".format(e))
            await ctx.send("Error: {}".format(e))

    return bot
