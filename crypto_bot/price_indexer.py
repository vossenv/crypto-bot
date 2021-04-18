class Coin:

    def __init__(self, id, symbol, name):
        self.coin_id = id
        self.symbol = symbol
        self.name = name
        self.price = 0
        self.perc = 0

    #    self.exchange = None
    # def update(self):
    #     v, p = self.exchange.get_ticker(self.symbol)
    #     self.price = v
    #     self.perc = round(p, 2) if p else "N/A"


class PriceIndexer:

    def __init__(self, exchanges):
        self.exchanges = exchanges
        self.coins = {}


    async def get_ticker(self, symbol):
        return ("0.01", "5.32")

    def get_name(self, symbol):
        return "ABC"

    #def add_bot(self, bot):




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