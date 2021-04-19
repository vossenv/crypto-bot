import logging
import threading
import time

import requests

from crypto_bot.error import CoinNotFoundException, InvalidCoinException
from crypto_bot.price_indexer import Coin


class Exchange:
    hard_coins = {
        'one': 'harmony'
    }

    def __init__(self, config):
        self.priority = int(config['priority'])
        self.name = config['name']
        self.base_url = config['api_url']
        self.coins = {}
        self.logger = logging.getLogger("connector")
        threading.Thread(target=self.get_coins).start()

    def call(self, url, method="GET", headers=None, data=None, json=True):
        r = requests.request(method=method, url=url, data=data or {}, headers=headers or {})
        if r.status_code is not 200:
            raise requests.RequestException("{}: {}".format(r.status_code, r.content))
        return r.json() if json else r.content

    def get_ticker(self, symbol):
        path = "/simple/price?ids={}&vs_currencies=usd&include_24hr_change=true"
        c = self.get_coin_def(symbol)
        ticker = self.call(self.base_url + path.format(c.coin_id))
        return self.parse_ticker(c.coin_id, ticker)

    def parse_ticker(self, id, ticker):
        d = ticker[id]
        price = d['usd']
        perc = d['usd_24h_change']
        return price, round(perc, 2) if perc else "N/A"

    def get_coins(self):
        path = "/coins/list"
        while True:
            try:
                response = self.call(self.base_url + path)

                if not isinstance(response, list):
                    raise AssertionError("Response is not a list of coins")

                for c in response:
                    try:
                        coin = Coin.create(c)

                        hc = self.hard_coins.get(coin.symbol)
                        if hc and coin.coin_id != self.hard_coins[coin.symbol]:
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

            time.sleep(650)

    def get_coin_def(self, symbol):
        c = self.coins.get(symbol.lower())
        if not c:
            raise CoinNotFoundException(symbol)
        return c
