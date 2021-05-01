import logging
import threading
import time

from crypto_bot.error import CoinNotFoundException


class Coin:

    def __init__(self, id, symbol, name=None, exchange=None):
        self.coin_id = id
        self.symbol = symbol.lower()
        self.name = name
        self.price = 0
        self.perc = 0
        self.direction = ""
        self.last_exchange = exchange
        self.info = {}

    def update(self, price, perc, exchange=None):
        self.price = float(price)
        try:
            self.perc = round(float(perc), 2)
            self.direction = ("↑" if self.perc >= 0 else "↓")
        except ValueError:
            self.perc = perc or "N/A"
        if exchange:
            self.last_exchange = exchange


class PriceIndexer:

    def __init__(self, exchanges, update_rate):
        self.info_exchange = None
        for e in exchanges:
            if e.name.lower() == 'coingecko':
                self.info_exchange = e
        self.exchanges_by_priority = sorted(exchanges, key=lambda x: x.priority)
        self.update_rate = update_rate
        self.coins = {}
        self.logger = logging.getLogger("indexer")
        self.ready = False

    def wait_exchanges(self):
        while set([e.ready for e in self.exchanges_by_priority]) != {True}:
            self.logger.info("Waiting for exchanges...")
            time.sleep(0.5)

    def add_new_coin(self, symbol):
        c = None
        for e in self.exchanges_by_priority:
            try:
                c = e.get_coin_def(symbol)
                break
            except CoinNotFoundException:
                pass
        if not c:
            raise CoinNotFoundException(symbol)
        if self.info_exchange:
            try:
                c.name = self.info_exchange.get_coin_def(symbol).name
            except Exception as e:
                self.logger.error("Error setting coin {} name {}".format(c.symbol, e))
        self.coins[symbol.lower()] = c
        # self.info_exchange.get_coin_info('doge')

    def get_coin(self, symbol, wait=False, info=False):
        symbol = symbol.lower()
        if symbol not in self.coins:
            self.add_new_coin(symbol)
            if wait:
                self.update_coins(wait)
        if info:
            if self.info_exchange:
                self.coins[symbol].info = self.info_exchange.get_coin_info(symbol)
            else:
                raise AssertionError("Coingecko API not present, info for {} not available".format(symbol))
        return self.coins[symbol]

    def run(self):
        threading.Thread(target=self.update_loop).start()

    def update_loop(self):
        while True:
            self.update_coins()
            time.sleep(self.update_rate)

    def update_coins(self, wait=False):
        try:
            remaining = set(self.coins.keys())
            for e in self.exchanges_by_priority:
                e.update_list = remaining.intersection(set(e.coins.keys()))
                remaining -= e.update_list
                if wait:
                    self.get_coins_from_exchange(e)
                else:
                    threading.Thread(target=self.get_coins_from_exchange, args=(e,)).start()
        except Exception as e:
            self.logger.error(e)

    def get_coins_from_exchange(self, exchange):
        try:
            updates = exchange.get_tickers(exchange.update_list)
            for c, v in updates.items():
                self.coins[c].update(v[0], v[1], exchange.name)
        except Exception as e:
            self.logger.error(e)
