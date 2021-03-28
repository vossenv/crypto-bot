class Coin:

    def __init__(self, id, symbol, name):
        self.coin_id = id
        self.symbol = symbol
        self.name = name
        self.price = 0
        self.perc = 0
        self.exchange = None

    def set_values(self, price, perc):
        self.price = price
        self.perc = perc


class PriceIndexer:

    def __init__(self, connectors):

        self.coins = {}
        self.connectors = connectors

        print()

    def index_coin(self, symbol):
        if symbol not in self.coins:
            for c in self.connectors:
                if c.has_coin(symbol):
                    coin = c.get_coin(symbol)
                    
            coin.set_prices(self.fetch_price(coin.symbol))
            self.coins[coin.symbol] = coin

    def fetch_price(self, symbol):
        for c in self.connectors:
            if c.has_coin(symbol):
                return c.get_ticker(symbol)
        raise ValueError("Coin '{}' not found in any exchange".format(symbol))
