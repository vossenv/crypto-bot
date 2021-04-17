import json
import logging
import threading
import time

import aiohttp
import requests


class Coin:

    def __init__(self, id, symbol, name):
        self.coin_id = id
        self.symbol = symbol
        self.name = name


class ApiConnector:
    hard_coins = {
        'one': 'harmony'
    }

    def __init__(self, base_url):
        self.logger = logging.getLogger("connector")
        self.base_url = base_url
        self.coins = {}
        threading.Thread(target=self.get_coins).start()

    async def call(self, url, method="GET", headers=None, data=None, json=True):
        async with aiohttp.request(method=method, url=url, data=data or {}, headers=headers or {}) as r:
            if json:
                body = await r.json()
            else:
                body = await r.read()
        return body, r.status

    async def get_ticker(self, symbol):
        path = "/simple/price?ids={}&vs_currencies=usd&include_24hr_change=true"
        c = self.coins.get(symbol.lower())
        if not c:
            raise AssertionError("Coin by name: {} was not found".format(symbol))
        ticker = await self.call(self.base_url + path.format(c.coin_id))
        return self.parse_ticker(c.coin_id, ticker)

    def parse_ticker(self, id, ticker):
        d = ticker[0][id]
        price = d['usd']
        perc = d['usd_24h_change']
        return price, round(perc, 2) if perc else "N/A"

    async def get_icon(self, symbol):
        path = "/coins/{}"
        c = self.coins.get(symbol.lower())
        if not c:
            raise AssertionError("Coin by name: {} was not found".format(symbol))
        r = await self.call(self.base_url + path.format(c.coin_id))
        url = r[0]['image']['thumb']
        return (await self.call(url, headers={'Accept': 'image/png'}, json=False))[0]

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

    def get_name(self, symbol):
        symbol = symbol.lower()
        if symbol in self.coins:
            return self.coins[symbol].name

