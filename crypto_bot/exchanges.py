import collections
import logging
import re
import threading
import time
from datetime import datetime
from html.parser import HTMLParser
from io import StringIO

import requests

from crypto_bot.error import CoinNotFoundException
from crypto_bot.price_indexer import Coin


class Exchange:

    def __init__(self, config):
        self.priority = int(config['priority'])
        self.coin_overrides = config.get("coin_overrides") or {}
        self.name = None
        self.coins = {}
        self.logger = logging.getLogger("connector")
        self.ready = False
        self.coins_path = None
        self.ticker_path = None
        self.last_coin_list = set()
        self.new_coins = {}

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

    #
    def get_coin_def(self, symbol, raises=True):
        c = self.coins.get(symbol.lower())
        if not c and raises:
            raise CoinNotFoundException(symbol, self.name)
        return c

    def coins_ready(self):
        if not self.ready:
            self.ready = True
            self.last_coin_list = set(self.coins.keys())

    def get_new_coins(self):
        if not self.ready:
            return set()
        current_coins = set(self.coins.keys())
        for n in (current_coins - self.last_coin_list):
            self.new_coins[n] = datetime.utcnow()
        self.last_coin_list = current_coins
        return self.new_coins

    def clear_new_coins(self):
        self.new_coins = {}

    def get_ticker_range(self, coins):
        pass

    def get_ticker(self, symbol):
        return self.get_tickers(symbol).get(symbol)

    def parse_ticker(self, d):
        pass

    def parse_coins_response(self, resp) -> list:
        pass

    @classmethod
    def create(self, name, config):
        name = name.lower()
        if name == "coingecko":
            return CoinGeckoExchange(config)
        elif name == "kucoin":
            return KucoinExchange(config)
        elif name == "binance_us":
            return BinanceUSExchange(config)
        else:
            raise ValueError("Unknown exchange: {}".format(name))


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


class CoinGeckoExchange(Exchange):

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://api.coingecko.com/api/v3"
        self.coins_path = "/coins/list"
        self.coins_info_path = "/coins"
        self.ticker_path = "/simple/price?ids={}&vs_currencies=usd&include_24hr_change=true"
        self.name = "CoinGecko"
        threading.Thread(target=self.get_coins).start()

    def get_coins(self):
        while True:
            try:
                response = self.call(self.base_url + self.coins_path)
                for coin in self.parse_coins_response(response):
                    if coin.symbol in self.coin_overrides and coin.coin_id != self.coin_overrides[coin.symbol]:
                        continue
                    if coin.symbol not in self.coins:
                        self.coins[coin.symbol] = coin
                    else:
                        self.coins[coin.symbol].coin_id = coin.coin_id
                        self.coins[coin.symbol].name = coin.name
            except Exception as e:
                self.logger.error(e)
            self.coins_ready()
            time.sleep(650)

    def get_coin_info(self, symbol):
        symbol = symbol.lower()
        if symbol.lower() not in self.coins:
            raise CoinNotFoundException(symbol)

        cid = self.coins[symbol].coin_id
        info = self.call(self.base_url + "/{}/{}".format(self.coins_info_path, cid))
        info_dict = {
            'name': info.get('name'),
            'homepage': self.get_nested_key(info, ['links', 'homepage'])[0],
            'reddit': self.get_nested_key(info, ['links', 'subreddit_url']),
            'coingecko': 'https://www.coingecko.com/en/coins/{}'.format(cid),
            'total_coins': self.get_nested_key(info, ['market_data', 'total_supply']),
            'circulating_coins': self.get_nested_key(info, ['market_data', 'circulating_supply']),
            'market_cap': self.get_nested_key(info, ['market_data', 'market_cap', 'usd']),
            'ath': self.get_nested_key(info, ['market_data', 'ath', 'usd']),
            'algorithm': info.get('hashing_algorithm'),
            'block_time': info.get('block_time_in_minutes'),
            'image': self.get_nested_key(info, ['image', 'small']),
        }

        entries = []
        repos = self.get_nested_key(info, ['links', 'repos_url'])
        if repos is not None:
            for r in repos.values():
                entries.extend(r)
        info_dict['repos'] = entries

        desc = self.get_nested_key(info, ['description', 'en'])
        if desc is not None:
            desc = self.strip_tags(desc)
        info_dict['description'] = desc

        ath_date = self.get_nested_key(info, ['market_data', 'ath_date', 'usd'])
        if ath_date is not None:
            ath_date = datetime.strptime(ath_date, '%Y-%m-%dT%H:%M:%S.%fZ')
        info_dict['ath_date'] = ath_date
        return info_dict

    def get_new_coins(self):
        return {}

    def strip_tags(self, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    def get_nested_key(self, d, keys):
        for k in keys:
            if d is None or not isinstance(d, collections.Mapping):
                break
            d = d.get(k)
        return d

    def get_ticker_range(self, coins):
        l = ",".join(coins.keys())
        tickers = self.call(self.base_url + self.ticker_path.format(l))
        return {coins[t].symbol: self.parse_ticker(d) for t, d in tickers.items()}

    def parse_ticker(self, d):
        price = d['usd']
        perc = d['usd_24h_change']
        return price, perc

    def parse_coins_response(self, resp):
        if not isinstance(resp, list):
            raise AssertionError("Response is not a list of coins")

        parsed_coins = []
        for c in resp:
            try:
                parsed_coins.append(Coin(c['id'], c['symbol'], c['name'], exchange=self.name))
            except Exception as e:
                self.logger.error(e)
        return parsed_coins


class KucoinExchange(Exchange):

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://api.kucoin.com"
        self.coins_path = "/api/v1/market/allTickers"
        self.update_rate = config['update_rate']
        self.name = "KuCoin"
        threading.Thread(target=self.get_coins).start()

    def get_coins(self):
        while True:
            try:
                response = self.call(self.base_url + self.coins_path)
                for coin in response['data']['ticker']:
                    s = coin['symbol'].lower()
                    if 'usdt' not in s:
                        continue
                    s = s.split('-')[0]
                    if s not in self.coins:
                        self.coins[s] = Coin(coin['symbol'], symbol=s, exchange=self.name)
                    else:
                        self.coins[s].coin_id = coin['symbol']
                    self.coins[s].update(float(coin['last']), float(coin['changeRate']))
            except Exception as e:
                self.logger.error(e)
            self.coins_ready()
            time.sleep(self.update_rate)

    def get_ticker_range(self, symbols):
        return {v.symbol: (v.price, v.perc) for v in symbols.values()}


class BinanceUSExchange(Exchange):

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://api.binance.us"
        self.coins_path = "/api/v3/ticker/24hr"
        self.update_rate = config['update_rate']
        self.name = "Binance US"
        threading.Thread(target=self.get_coins).start()

    def get_coins(self):
        while True:
            try:
                response = self.call(self.base_url + self.coins_path)
                for coin in response:
                    s = coin['symbol'].lower()
                    if not s.endswith('usd'):
                        continue
                    s = re.sub('usd$', '', s)
                    if s not in self.coins:
                        self.coins[s] = Coin(coin['symbol'], symbol=s, exchange=self.name)
                    else:
                        self.coins[s].coin_id = coin['symbol']
                    self.coins[s].update(float(coin['lastPrice']), float(coin['priceChangePercent']))
            except Exception as e:
                self.logger.error(e)
            self.coins_ready()
            time.sleep(self.update_rate)

    def get_ticker_range(self, symbols):
        return {v.symbol: (v.price, v.perc) for v in symbols.values()}
