from crypto_bot.error import CoinNotFoundException


class Coin:

    def __init__(self, id, symbol, name):
        self.coin_id = id
        self.symbol = symbol
        self.name = name
        self.price = 0
        self.perc = 0

    def update(self, price, perc):
        self.price = price
        self.perc = round(perc, 2) if perc else "N/A"


class PriceIndexer:

    def __init__(self, exchanges):
        self.exchanges = exchanges
        self.base_exchange = exchanges[0]
        self.coins = {}

    def add_new_coin(self, symbol):
        c = self.base_exchange.get_coin_def(symbol)
        if not c:
            raise CoinNotFoundException(symbol)
        c.update(*self.base_exchange.get_ticker(symbol))
        self.coins[symbol.lower()] = c

    async def get_ticker(self, symbol):
        symbol = symbol.lower()
        if symbol not in self.coins:
            self.add_new_coin(symbol)

        c = self.coins[symbol]
        return c.price, c.perc

    def get_name(self, symbol):
        return "ABC"

    # def add_bot(self, bot):

    # def index_coin(self, symbol):
    #     if symbol not in self.coins:
    #         coin = self.info_connector.get_coin(symbol)
    #         if not coin:
    #             raise ValueError("Coin '{}' not found".format(symbol))
    #         for c in self.connectors:
    #             if c.has_coin(symbol):
    #                 coin.exchange = c
    #                 break
    #         coin.update()
    #         self.coins[coin.symbol] = coin
