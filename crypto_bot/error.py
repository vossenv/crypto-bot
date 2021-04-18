class CoinNotFoundException(Exception):

    def __init__(self, symbol):
        self.symbol = symbol
        self.message = "Coin by name: {} was not found".format(symbol.upper())
        super().__init__(self.message)
