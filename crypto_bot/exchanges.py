import json
import logging
import threading
import time

import requests

from crypto_bot.error import CoinNotFoundException
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
        return r.json() if json else r.content, r.status_code

    def get_ticker(self, symbol):
        path = "/simple/price?ids={}&vs_currencies=usd&include_24hr_change=true"
        c = self.get_coin_def(symbol)
        if not c:
            raise CoinNotFoundException(symbol)
        ticker = self.call(self.base_url + path.format(c.coin_id))
        return self.parse_ticker(c.coin_id, ticker)

    def parse_ticker(self, id, ticker):
        d = ticker[0][id]
        price = d['usd']
        perc = d['usd_24h_change']
        return price, round(perc, 2) if perc else "N/A"

    def get_coins(self):
        path = "/coins/list"
        while True:
            try:
                response = requests.get(self.base_url + path)
                if response.status_code is not 200:
                    raise requests.RequestException("{}: {}".format(response.status_code, response.content))
                try:
                    coins = json.loads(response.content)
                    if not isinstance(coins, list) or not self.is_coin(coins[0]):
                        raise TypeError
                    coins = {c['id']: c for c in coins}
                    self.coins = {c['symbol'].lower(): Coin(**c) for c in coins.values()}
                    for c, i in self.hard_coins.items():
                        if c in coins:
                            self.coins[c] = Coin(**coins[i])
                except TypeError as e:
                    raise requests.RequestException("Content was not expected: {}".format(response.content))
            except Exception as e:
                self.logger.error(e)
            time.sleep(650)

    def is_coin(self, d):
        return set(d.keys()) - {'id', 'symbol', 'name'} == set()

    def get_coin_def(self, symbol):
        return self.coins.get(symbol.lower())
