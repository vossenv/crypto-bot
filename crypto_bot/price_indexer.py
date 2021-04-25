import logging
import threading
import time


class Coin:
    required_keys = {'id', 'symbol', 'name'}

    def __init__(self, id, symbol, name=None):
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


class PriceIndexer:

    def __init__(self, exchanges, update_rate):
        self.exchanges = exchanges
        self.base_exchange = exchanges[0]
        self.update_rate = update_rate
        self.coins = {}
        self.logger = logging.getLogger("indexer")
        self.ready = False

    def wait_exchanges(self):
        while {e.ready for e in self.exchanges} == {False}:
            self.logger.info("Waiting for exchanges...")
            time.sleep(0.5)

    def add_new_coin(self, symbol):
        c = self.base_exchange.get_coin_def(symbol)
        self.coins[symbol.lower()] = c

    def get_coin(self, symbol, wait=False):
        symbol = symbol.lower()
        if symbol not in self.coins:
            self.add_new_coin(symbol)
            if wait:
                self.update_coins()
        return self.coins[symbol]

    def run(self):
        threading.Thread(target=self.update_loop).start()

    def update_loop(self):
        while True:
            self.update_coins()
            time.sleep(self.update_rate)

    def update_coins(self):
        try:
            updates = self.base_exchange.get_tickers(set(self.coins.keys()))
            for c, v in updates.items():
                self.coins[c].update(v[0], v[1])
        except Exception as e:
            self.logger.error(e)
