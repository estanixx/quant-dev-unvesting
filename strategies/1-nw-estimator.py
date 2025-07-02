import pandas as pd
import numpy as np
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
from typing import Dict, Callable
from backtesting import Backtest, Strategy

def nwe(source: np.ndarray, length: int, bandwidth: float) -> np.ndarray:
    """
    Calculates the Nadaraya-Watson Estimator for a NumPy array.
    This version is optimized for use with the backtesting.py library.
    """
    nwe_values = np.full_like(source, np.nan)
    
    for i in range(length, len(source)):
        y_ = source[i - length : i]
        sum_w, sum_wy = 0.0, 0.0
        
        for k in range(length):
            w = np.exp(-((k - (length - 1))**2) / (2 * bandwidth**2))
            sum_w += w
            sum_wy += y_[k] * w
            
        if sum_w != 0:
            nwe_values[i] = sum_wy / sum_w
            
    return nwe_values





# --- Define the Strategy ---
class NWEStrategy(Strategy):
    # --- Define Strategy Parameters for Optimization ---
    nw_length = 50
    nw_bandwidth = 10.0

    
    def init(self):
        """
        This method is called once at the beginning to calculate indicators.
        """
        # Primary Indicators
        self.nwe = self.I(nwe, self.data.Close, length=self.nw_length, bandwidth=self.nw_bandwidth, name="NWE")
        # Logic Indicators (not plotted)
        self.nwe_direction = self.I(lambda x: np.sign(np.diff(x, prepend=np.nan)), self.nwe, plot=False)
        
        


    def next(self):
        """
        This method is called for each bar to define trading logic.
        """

        # Reset trailing stop when not in a position
        if self.nwe_direction[-1] == 1 and self.nwe_direction[-2] == -1:
            self.position.close()
            self.buy()

        elif self.nwe_direction[-1] == -1 and self.nwe_direction[-2] == 1:
            self.position.close()
            self.sell()




# --- Example Usage ---
if __name__ == '__main__':
    # --- Download Data ---
    today = pd.Timestamp.today().normalize()
    start_date = today - pd.DateOffset(years=2)
    ticker_symbol = 'NVDA'
    
    print(f"--- Downloading data for {ticker_symbol} ---")
    data = yf.download(ticker_symbol, start=start_date, end=today, multi_level_index=False)

    # --- Run the Optimization ---
    bt = Backtest(data, NWEStrategy, cash=100_000, commission=.001)

    print("\n--- Running Parameter Optimization ---")
    # Define the parameter grid for the optimizer to test
    stats = bt.optimize(
        nw_length=range(40, 101, 10),
        nw_bandwidth=range(8, 16, 2),
        maximize='Sharpe Ratio',
    )
    
    print("\n--- Best Backtest Results ---")
    print(stats)
    
    print("\n--- Optimal Parameters Found ---")
    print(stats._strategy)
    
    print("\n--- Plotting Results of the Best Run ---")
    bt.plot()
