import logging
import threading
import time

from crypto_bot.error import CoinNotFoundException


class Coin:

    def __init__(self, id, symbol, name):
        self.coin_id = id
        self.symbol = symbol
        self.name = name
        self.price = 0
        self.perc = 0
        self.direction = ""

    def update(self, price, perc):
        self.price = price
        self.perc = round(perc, 2) if perc else "N/A"
        self.direction = ("↑" if perc >= 0 else "↓") if isinstance(perc, float) else ""


class PriceIndexer:

    def __init__(self, exchanges, update_rate):
        self.exchanges = exchanges
        self.base_exchange = exchanges[0]
        self.update_rate = update_rate
        self.coins = {}
        self.logger = logging.getLogger("indexer")

    def add_new_coin(self, symbol):
        c = self.base_exchange.get_coin_def(symbol)
        if not c:
            raise CoinNotFoundException(symbol)
        c.update(*self.base_exchange.get_ticker(symbol))
        self.coins[symbol.lower()] = c

    def get_coin(self, symbol):
        symbol = symbol.lower()
        if symbol not in self.coins:
            self.add_new_coin(symbol)
        return self.coins[symbol]

    def run(self):
        pass
        threading.Thread(target=self.update_loop).start()

    def update_loop(self):

        while True:
            for c in self.coins.values():

                try:
                    data = self.base_exchange.get_ticker(c.symbol)
                    c.update(data[0], data[1])
                except Exception as e:
                    self.logger.error(e)

            time.sleep(self.update_rate)
