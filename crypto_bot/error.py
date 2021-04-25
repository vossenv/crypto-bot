class CoinNotFoundException(Exception):

    def __init__(self, symbol, exchange=None):
        self.symbol = symbol
        self.message = "Coin by name: {} was not found or no USDT pair available".format(symbol.upper())
        if exchange:
            self.message += " (on exchange {})".format(exchange)
        super().__init__(self.message)

class InvalidCoinException(Exception):
    pass