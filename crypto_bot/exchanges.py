import logging
import threading
import time

import requests

from crypto_bot.error import CoinNotFoundException, InvalidCoinException
from crypto_bot.price_indexer import Coin


class Exchange:
    hard_coins = {}

    def __init__(self, config):
        self.priority = int(config['priority'])
        self.base_url = config['api_url']
        self.coins = {}
        self.logger = logging.getLogger("connector")
        self.ready = False
        self.coins_path = None
        self.ticker_path = None

    def call(self, url, method="GET", headers=None, data=None, json=True):
        r = requests.request(method=method, url=url, data=data or {}, headers=headers or {})
        if r.status_code is not 200:
            raise requests.RequestException("{}: {}".format(r.status_code, r.content))
        return r.json() if json else r.content

    def get_tickers(self, symbols):

        coins = {}
        if not symbols:
            return coins
        symbols = {symbols} if isinstance(symbols, str) else set(symbols)

        for c in symbols:
            try:
                coin = self.get_coin_def(c)
                coins[coin.coin_id] = coin
            except CoinNotFoundException:
                continue

        return self.get_ticker_range(coins)

    def get_coins(self):
        while True:
            try:
                response = self.call(self.base_url + self.coins_path)
                if not isinstance(response, list):
                    raise AssertionError("Response is not a list of coins")
                for c in response:
                    try:
                        coin = Coin.create(c)
                        if coin.symbol in self.hard_coins and coin.coin_id != self.hard_coins[coin.symbol]:
                            continue
                        if coin.symbol not in self.coins:
                            self.coins[coin.symbol] = coin
                        else:
                            self.coins[coin.symbol].coin_id = coin.coin_id
                            self.coins[coin.symbol].name = coin.name
                    except InvalidCoinException as e:
                        self.logger.error(e)
            except Exception as e:
                self.logger.error(e)
            self.ready = True
            time.sleep(650)

    def get_coin_def(self, symbol):
        c = self.coins.get(symbol.lower())
        if not c:
            raise CoinNotFoundException(symbol)
        return c

    def start_coin_reads(self):
        threading.Thread(target=self.get_coins).start()

    def get_ticker_range(self, coins):
        pass

    def get_ticker(self, symbol):
        return self.get_tickers(symbol).get(symbol)

    def parse_ticker(self, d):
        pass

    @classmethod
    def create(self, name, config):
        if name.lower() == "coingecko":
            return CoinGeckoExchange(config)
        else:
            raise ValueError("Unknown exchange: {}".format(name))


class CoinGeckoExchange(Exchange):
    hard_coins = {
        'one': 'harmony'
    }

    def __init__(self, config):
        super().__init__(config)
        self.coins_path = "/coins/list"
        self.ticker_path = "/simple/price?ids={}&vs_currencies=usd&include_24hr_change=true"
        self.start_coin_reads()

    def get_ticker_range(self, coins):
        l = ",".join(coins.keys())

        tickers = self.call(self.base_url + self.ticker_path.format(l))
        return {coins[t].symbol: self.parse_ticker(d) for t, d in tickers.items()}

    def parse_ticker(self, d):
        price = d['usd']
        perc = d['usd_24h_change']
        return price, round(perc, 2) if perc else "N/A"
