config_loader = None
indexer = None


async def get_symbol_price(ctx, symbol):
    try:
        c = indexer.get_coin(symbol, wait=True)
        msg = "{}/{}: ${}, change: {}% - indexed from {}" \
            .format(symbol.upper(), c.name or c.coin_id, c.price, c.perc, c.last_exchange)
        await ctx.send(msg)
    except Exception as e:
        await ctx.send("Error: {}".format(e))
