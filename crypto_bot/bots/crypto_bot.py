# import asyncio
# import datetime
# import logging
# import threading
# import time
# from random import random
#
# import discord
# from discord.ext.commands import Bot, MissingRequiredArgument, CommandNotFound
#
# from crypto_bot.error import CoinNotFoundException
#
# config_loader = None
#
#
# class CoinAssociation:
#
#     def __init__(self, coin, membership):
#         self.coin = coin
#         self.update(coin)
#         self.membership = membership
#
#     def update(self, coin):
#         self.coin = coin.upper()
#         self.image = None
#
#
# class CryptoBot(Bot):
#
#     def __init__(self, token, coin, chat_id, command_roles, indexer, *args, **kwargs):
#         super(CryptoBot, self).__init__(*args, **kwargs)
#         self.token = token
#         self.coin = coin.upper()
#         self.chat_id = chat_id
#         self.command_roles = {c.lower() for c in command_roles}
#         self.associations = {}
#         self.logger = logging.getLogger("{} bot".format(coin))
#         self.logger.info("Starting {} bot...".format(self.coin))
#         self.indexer = indexer
#
#     async def set_coin(self, guild, symbol):
#         symbol = str(symbol).lower()
#         coin = self.indexer.get_coin(symbol, wait=True)
#         self.associations[guild].update(symbol)
#         await self.update()
#         return coin
#
#     async def ready(self):
#         threading.Thread(target=self.update_memberships).start()
#         await self.status_loop()
#
#     async def status_loop(self):
#         while True:
#             await self.update()
#             await asyncio.sleep(0.5)
#
#     async def update(self):
#         for g, a in self.associations.items():
#             try:
#                 c = self.indexer.get_coin(a.coin)
#                 act = discord.Activity(type=discord.ActivityType.watching, name="{0} % {1}".format(c.perc, c.direction))
#                 await a.membership.edit(nick="!{0} {1} {2}".format(self.chat_id, a.coin, c.price))
#                 await self.change_presence(status=discord.Status.online, activity=act)
#             except Exception as e:
#                 self.logger.error(e)
#
#     def update_memberships(self):
#         while True:
#             for g in self.guilds:
#                 if g.id not in self.associations:
#                     m = [u for u in g.members if u.id == self.user.id]
#                     if not m:
#                         self.logger.warning("No matching member id found for {}".format(g.id))
#                         continue
#                     elif len(m) > 1:
#                         self.logger.warning("Multiple matches found for id for {} - using first match".format(g.id))
#                     self.associations[g.id] = CoinAssociation(self.coin, m[0])
#             time.sleep(60)
#
#     def describe(self):
#         data = {}
#         for a in self.associations.values():
#             data[a.membership.guild.name] = a.membership.nick
#         return data
#
#     async def start(self):
#         await super().start(self.token)
#
#
# def create_bot(token, coin, chat_id, command_roles, indexer):
#     bot = CryptoBot(command_prefix="!{} ".format(chat_id.lstrip("0")),
#                     token=token,
#                     coin=coin,
#                     chat_id=chat_id,
#                     command_roles=command_roles,
#                     indexer=indexer,
#                     case_insensitive=True)
#
#     @bot.event
#     async def on_ready():
#         bot.logger.info("#{} - {} is ready!".format(bot.chat_id, bot.coin))
#         await bot.ready()
#
#     @bot.command(name='feed', help='Get some soup')
#     async def feed(ctx):
#         if random() >= 0.7:
#             await ctx.send("You may eat today {}, Qapla'!".format(ctx.author.name))
#         else:
#             await ctx.send("No soup for you!")
#
#     @bot.command(name='set', help='Sets a specific coin by symbol. Usage: ![#] set DOGE - # indicates bot number')
#     async def set_coin(ctx, symbol):
#         if not ctx.author.id == ctx.guild.owner_id and \
#                 not {r.name.lstrip('@').lower() for r in ctx.author.roles} & bot.command_roles:
#             await ctx.send("You do not have permission to use this function")
#             return
#         try:
#             await ctx.send("Attempting to set coin to {}".format(symbol))
#             c = await bot.set_coin(ctx.guild.id, symbol)
#             if config_loader.is_home_id(ctx.guild.id):
#                 config_loader.update_bot_coin(bot.token, symbol)
#             await ctx.send("Set bot #{} to {} - {} successfully! - indexed from {}"
#                            .format(bot.chat_id, c.symbol.upper(), c.name or c.coin_id, c.last_exchange))
#         except CoinNotFoundException as e:
#             await ctx.send(e)
#         except Exception as e:
#             await ctx.send("An unexpected error occured")
#             bot.logger.error(e)
#
#     @bot.command(name='price', help='Get a price. Usage: 1[#] price DOGE - # indicates bot number')
#     async def get_price(ctx, symbol):
#         try:
#             c = bot.indexer.get_coin(symbol, wait=True)
#             msg = "{}/{}: ${}, change: {}% - indexed from {}" \
#                 .format(symbol.upper(), c.name or c.coin_id, c.price, c.perc, c.last_exchange)
#             await ctx.send(msg)
#         except Exception as e:
#             await ctx.send("Error: {}".format(e))
#
#     @bot.command(name='info', help='Get coin info. Usage: 1[#] info DOGE - # indicates bot number')
#     async def get_info(ctx, symbol):
#         try:
#             c = bot.indexer.get_coin(symbol, wait=True, info=True)
#             message = \
#                 """
# **Ticker**: {ticker}
# **Name**: {name}
# **Price**: ${price} / {change} %
# **ATH**: ${ath} on {ath_date}
# **Total Supply**: {supply}
# **Circulating Supply**: {circulating}
# **Percent Mined**: {mined}
# **Market Cap**: {cap}
# **Current Index**: {exchange}
# **Homepage**: <{homepage}>
# **Coingecko**: <{coingecko}>
# **Development**: {repos}"""
#             repos = c.info['repos']
#             if repos:
#                 repos = ["<{}>".format(z) for z in c.info['repos']]
#                 if len(repos) > 1:
#                     repos = "\n" + "\n".join(repos)
#                 else:
#                     repos = repos[0]
#
#             d = c.info['ath_date']
#             if isinstance(d, datetime.datetime):
#                 d = d.strftime('%m/%d/%Y')
#
#             mined = "N/A"
#             supply = "Uncapped"
#             circulating = "Unknown"
#             market_cap = "Unknown"
#             if c.info['circulating_coins']:
#                 circulating = "{:,}".format(round(c.info['circulating_coins']))
#             if c.info['market_cap']:
#                 market_cap = "$" + "{:,}".format(c.info['market_cap'])
#             if c.info['total_coins']:
#                 supply = "{:,}".format(round(c.info['total_coins']))
#                 if circulating != "Unknown":
#                     mined = round(c.info['circulating_coins'] / c.info['total_coins'], 4) * 100
#                     mined = str(mined) + "%"
#
#             msg = message.format(
#                 image=c.info['image'],
#                 ticker=symbol.upper(),
#                 name=c.name,
#                 price=c.price,
#                 change=c.perc,
#                 ath=c.info['ath'],
#                 ath_date=d,
#                 supply=supply,
#                 mined=mined,
#                 circulating=circulating,
#                 cap=market_cap,
#                 exchange=c.last_exchange,
#                 homepage=c.info['homepage'],
#                 coingecko=c.info['coingecko'],
#                 repos=repos or "None provided"
#             )
#
#             if c.info['algorithm']:
#                 message += "\n**Hashing Algorithm**: {}".format(c.info['algorithm'])
#             if c.info['block_time']:
#                 message += "\n**Block Time**: {} minutes".format(c.info['block_time'])
#
#             await ctx.send(c.info['image'])
#             await ctx.send(msg)
#             desc = c.info['description']
#             message = "**Description**: \n{description}"
#             if not desc:
#                 await ctx.send("**Description**: None provided")
#                 return
#             if len(desc) > 500:
#                 message += "... \nTruncated - for a longer description, see <{}> ".format(c.info['coingecko'])
#             await ctx.send(message.format(description=desc[0:500]))
#
#         except Exception as e:
#             await ctx.send("Error: {}".format(e))
#
#     @bot.event
#     async def on_command_error(ctx, error):
#         if isinstance(error, CommandNotFound):
#             await ctx.send(error.args[0])
#         raise error
#
#     @set_coin.error
#     async def on_error(ctx, error):
#         if isinstance(error, MissingRequiredArgument):
#             await ctx.send("Missing required parameter: coin name - EG: !1 SET BTC")
#         else:
#             bot.logger.error("{} - {}".format(type(error), error.args[0]))
#             raise error
#
#     return bot
