import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy

# --- Custom Indicator Function ---
def psar(high, low, initial_acceleration, max_acceleration, acceleration_step):
    """
    Custom implementation of the Parabolic SAR (PSAR) indicator.
    """
    close = (high + low) / 2 # Use a proxy for close if not available
    length = len(high)
    psar_values = np.zeros(length)
    psar_bull = np.zeros(length)
    psar_bear = np.zeros(length)
    bull = True
    af = initial_acceleration
    ep = low[0]

    psar_values[0] = high[0]
    psar_bull[0] = high[0]
    psar_bear[0] = low[0]

    for i in range(2, length):
        if bull:
            psar_values[i] = psar_values[i - 1] + af * (ep - psar_values[i - 1])
        else:
            psar_values[i] = psar_values[i - 1] - af * (psar_values[i - 1] - ep)

        reverse = False

        if bull:
            if low[i] < psar_values[i]:
                bull = False
                reverse = True
                psar_values[i] = ep
                ep = low[i]
                af = initial_acceleration
        else:
            if high[i] > psar_values[i]:
                bull = True
                reverse = True
                psar_values[i] = ep
                ep = high[i]
                af = initial_acceleration

        if not reverse:
            if bull:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + acceleration_step, max_acceleration)
                if low[i - 1] < psar_values[i]:
                    psar_values[i] = low[i - 1]
                if low[i - 2] < psar_values[i]:
                    psar_values[i] = low[i - 2]
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + acceleration_step, max_acceleration)
                if high[i - 1] > psar_values[i]:
                    psar_values[i] = high[i - 1]
                if high[i - 2] > psar_values[i]:
                    psar_values[i] = high[i - 2]
    
    # Replace zeros with NaNs for cleaner plotting
    psar_values[psar_values == 0] = np.nan
    return psar_values
  
  

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
class NWEPSARStrategy(Strategy):
    """
    A trading strategy based on the Parabolic SAR (PSAR) indicator.
    - Enters long when PSAR flips below the price.
    - Enters short when PSAR flips above the price.
    - Uses the PSAR value as a trailing stop-loss.
    """
    # --- Define Strategy Parameters for Optimization ---
    initial_acceleration = 0.01
    max_acceleration = 0.1
    acceleration_step = 0.01
    nw_length = 80
    nw_bandwidth = 19.0
    
    def init(self):
        """
        This method is called once at the beginning to calculate indicators.
        """
        # Calculate the Parabolic SAR using our custom function.
        self.psar = self.I(
            psar,
            self.data.High,
            self.data.Low,
            self.initial_acceleration,
            self.max_acceleration,
            self.acceleration_step,
            name="PSAR"
        )
        
        # Primary Indicators
        self.nwe = self.I(nwe, self.data.Close, length=self.nw_length, bandwidth=self.nw_bandwidth, name="NWE")
        # Logic Indicators (not plotted)
        self.nwe_direction = self.I(lambda x: np.sign(np.diff(x, prepend=np.nan)), self.nwe, plot=False)

    def next(self):
        """
        This method is called for each bar to define the trading logic.
        """
        psar_below = self.data.Close[-1] > self.psar[-1]
        nwe_bullish = self.nwe_direction[-1] >= 0 
        psar_above = self.data.Close[-1] < self.psar[-1]
        nwe_bearish = self.nwe_direction[-1] <= 0
        
        # # --- Exit Logic (PSAR as a Trailing Stop-Loss) ---
        if self.position.is_long and (psar_above or nwe_bearish):
            self.position.close()
            
        elif self.position.is_short and (psar_below or nwe_bullish):
            self.position.close()

        # --- Entry Logic ---
        # A buy signal is when the PSAR flips from above the price to below it.
        if psar_below and nwe_bullish:
            if not self.position.is_long:
                self.position.close()
                self.buy()

        # A sell signal is when the PSAR flips from below the price to above it.
        elif psar_above and nwe_bearish:
            if not self.position.is_short:
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
    bt = Backtest(data, NWEPSARStrategy, cash=100_000, commission=.001)
    
    print("\n--- Running Parameter Optimization ---")
    # Define the parameter grid for the optimizer to test.
    
    stats = bt.run()
    print("\n--- Backtest Results ---")
    print(stats)

    
    print("\n--- Plotting Results of the Best Run ---")
    bt.plot()

    
    # stats = bt.optimize(
    #     initial_acceleration=list(np.arange(0.01, 0.05, 0.01)),
    #     max_acceleration=list(np.arange(0.1, 0.4, 0.05)),
    #     acceleration_step=list(np.arange(0.01, 0.05, 0.01)),
    #     nw_length=range(40, 101, 10),
    #     nw_bandwidth=list(np.arange(5.0, 20.0, 2.0)),

    #     maximize='Sharpe Ratio',
    #     constraint=lambda p: p.initial_acceleration < p.max_acceleration # A necessary PSAR constraint
    # )
    
    # print("\n--- Best Backtest Results ---")
    # print(stats)
    
    # print("\n--- Optimal Parameters Found ---")
    # print(stats._strategy)
    
    # print("\n--- Plotting Results of the Best Run ---")
    # bt.plot()
