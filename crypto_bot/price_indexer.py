import logging
import threading
import time

from crypto_bot.error import CoinNotFoundException


class Coin:

    def __init__(self, id, symbol, name=None):
        self.coin_id = id
        self.symbol = symbol.lower()
        self.name = name
        self.price = 0
        self.perc = 0
        self.direction = None
        self.last_exchange = None

    def update(self, price, perc, exchange=None):
        self.price = price
        self.perc = round(perc, 2) if perc else "N/A"
        self.direction = ("↑" if perc >= 0 else "↓") if isinstance(perc, float) else ""
        if exchange:
            self.last_exchange = exchange


class PriceIndexer:

    def __init__(self, exchanges, update_rate):
        self.info_exchange = None
        for e in exchanges:
            if e.name == 'coingecko':
                self.info_exchange = e
        self.exchanges_by_priority = sorted(exchanges, key=lambda x: x.priority, reverse=True)
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
        if self.info_exchange and not c.name:
            try:
                c.name = self.info_exchange.get_coin_def(symbol).name
            except Exception as e:
                self.logger.error("Error setting coin {} name {}".format(c.symbol, e))
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
            threads = []
            remaining = set(self.coins.keys())
            for e in self.exchanges_by_priority:
                e.update_list = remaining.intersection(set(e.coins.keys()))
                remaining -= e.update_list
                threads.append(threading.Thread(target=self.get_coins_from_exchange, args=(e,)))
            [t.start() for t in threads]
            [t.join() for t in threads]
        except Exception as e:
            self.logger.error(e)

    def get_coins_from_exchange(self, exchange):
        try:
            updates = exchange.get_tickers(exchange.update_list)
            for c, v in updates.items():
                self.coins[c].update(v[0], v[1], exchange.name)
        except Exception as e:
            self.logger.error(e)
