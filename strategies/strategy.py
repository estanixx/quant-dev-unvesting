from typing import List
class Strategy:
    _v = '1.0.0'
    author = 'Your Name'
    def __init__(self, tickers: List[str], n_candles: int = 1000):
        """Constructor for the Strategy class."""
        pass

    def get_trading_signals(self):
        """Given a certain ticker, return the trading signals."""
        pass
    
    def backtest(self):
        """Backtest the strategy."""
        pass
    
    def optimize(self):
        """Optimize the strategy parameters."""
        pass