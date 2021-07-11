import random

from discord.ext.commands import CommandNotFound, MissingRequiredArgument

from crypto_bot.resources.rules import RULES

config_loader = None
indexer = None


def add_price_commands(bot):
    @bot.command(name='price', help='Get a price. Usage: !price doge')
    async def get_price(ctx, symbol):
        try:
            c = indexer.get_coin(symbol, wait=True)
            msg = "{}/{}: ${}, change: {}% - indexed from {}" \
                .format(symbol.upper(), c.name or c.coin_id, c.price, c.perc, c.last_exchange)
            await ctx.send(msg)
        except Exception as e:
            await ctx.send("Error: {}".format(e))


def add_base_commands(bot):
    @bot.event
    async def on_ready():
        bot.logger.info("{} is ready!".format(bot.name))
        await bot.ready()

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

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, CommandNotFound) or isinstance(error, MissingRequiredArgument):
            try:
                int(ctx.invoked_with)
                return
            except Exception:
                await ctx.send(error.args[0])
        raise error

    return bot
