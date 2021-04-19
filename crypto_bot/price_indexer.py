import logging
import threading
import time

from crypto_bot.error import InvalidCoinException


class Coin:
    required_keys = {'id', 'symbol', 'name'}

    def __init__(self, id, symbol, name):
        self.coin_id = id
        self.symbol = symbol.lower()
        self.name = name
        self.price = 0
        self.perc = 0
        self.direction = ""

    def update(self, price, perc):
        self.price = price
        self.perc = round(perc, 2) if perc else "N/A"
        self.direction = ("↑" if perc >= 0 else "↓") if isinstance(perc, float) else ""

    @classmethod
    def create(cls, data):
        ks = set(data.keys())
        if not cls.required_keys.issubset(ks):
            missing = cls.required_keys - ks
            raise InvalidCoinException("Cannot create coin - missing keys: {}".format(missing))

        return Coin(data['id'], data['symbol'], data['name'])


class PriceIndexer:

    def __init__(self, exchanges, update_rate):
        self.exchanges = exchanges
        self.base_exchange = exchanges[0]
        self.update_rate = update_rate
        self.coins = {}
        self.logger = logging.getLogger("indexer")

    def add_new_coin(self, symbol):
        c = self.base_exchange.get_coin_def(symbol)
        c.update(*self.base_exchange.get_ticker(symbol))
        self.coins[symbol.lower()] = c

    def get_coin(self, symbol):
        symbol = symbol.lower()
        if symbol not in self.coins:
            self.add_new_coin(symbol)
        return self.coins[symbol]

    def run(self):
        threading.Thread(target=self.update_loop).start()

    def update_loop(self):
        while True:
            for c in self.coins:
                try:
                    data = self.base_exchange.get_ticker(c)
                    self.coins[c].update(data[0], data[1])
                   #self.logger.debug("{} {}".format(c, data))
                except Exception as e:
                    self.logger.error(e)
            time.sleep(self.update_rate)
