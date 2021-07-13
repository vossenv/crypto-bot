from discord.ext.commands import CommandNotFound, MissingRequiredArgument

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


def add_shared_setup(bot):

    @bot.event
    async def on_ready():
        bot.logger.info("{} is ready!".format(bot.name))
        await bot.ready()

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
