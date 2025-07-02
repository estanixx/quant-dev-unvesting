import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# --- Custom Indicator Functions ---

def bollinger_bands(close: np.ndarray, length: int = 20, std_devs: float = 2.0, ddof: int = 0, column: str = 'Close') -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Moving average
    df = pd.DataFrame({column: close})
    rolling = df[column].rolling(window=length, min_periods=length)
    df['MA'] = rolling.mean()
    band_distance = std_devs * rolling.std(ddof=ddof)
    df['BB UP'] = df['MA'] + band_distance
    df['BB DOWN'] = df['MA'] - band_distance
    return df['BB UP'].to_numpy(), df['BB DOWN'].to_numpy(), df['MA'].to_numpy()


def trend_indicator(ma, data, up, down) -> np.ndarray:
    """Custom trend indicator based on moving average crossover."""
    close = data.Close
    low = data.Low
    high = data.High
    trend = np.zeros(len(close))
    for i in range(1, len(close)):
        if close[i] > ma[i] and close[i - 1] <= ma[i - 1]:
            trend[i] = 1  # Uptrend
        elif close[i] < ma[i] and close[i - 1] >= ma[i - 1]:
            trend[i] = -1  # Downtrend
        else:
            trend[i] = trend[i - 1]  # No change
            
        if low[i] < down[i] and low[i - 1] < down[i - 1]:
            trend[i] = 0
        elif high[i] > up[i] and high[i - 1] > up[i - 1]:
            trend[i] = 0
            
    return trend
# --- Define the Combined Strategy ---
class BBStrategy(Strategy):
    # --- Define Strategy Parameters for Optimization ---
    length = 15
    std_devs = 2.1
    ddof = 0
    def init(self):
        """This method is called once at the beginning to calculate indicators."""
        self.bb_up, self.bb_down, self.ma = self.I(
            bollinger_bands,
            self.data.Close,
            length=self.length,
            std_devs=self.std_devs,
            ddof=self.ddof,
            name="Bollinger Bands"
        )
        self.trend = self.I(lambda: trend_indicator(self.ma, self.data, self.bb_up, self.bb_down), name='Trend')

    def next(self):
        """This method is called for each bar to define the trading logic."""
        last_bb_down = self.bb_down[-1]
        last_bb_up = self.bb_up[-1]
        
        if self.trend[-1] == 1:
            if not self.position.is_long:
                self.position.close()
                self.buy()
        elif self.trend[-1] == -1:
            if not self.position.is_short:
                self.position.close()
                self.sell()
        else:
            self.position.close()  # Close position if no trend

                
        

# --- Example Usage ---
if __name__ == '__main__':
    today = pd.Timestamp.today().normalize()
    start_date = today - pd.DateOffset(years=2)
    ticker_symbol = 'VOO'
    
    print(f"--- Downloading data for {ticker_symbol} ---")
    data = yf.download(ticker_symbol, start=start_date, end=today, multi_level_index=False)

    bt = Backtest(data, BBStrategy, cash=100_000, commission=.001)
    
    print("\n--- Running Optimization with Wider Ranges ---")
    # stats = bt.run()
    stats = bt.optimize(
        length=range(10, 31, 5),  # Bollinger Bands length from 10 to 30
        std_devs=list(np.arange(1.0, 3.1, 0.1)),  # Standard deviations from 1.0 to 3.0
        ddof=[0, 1],  # Degrees of freedom for std deviation calculation
        # constraint=lambda p: p['length'] < p['std_devs'] * 2,  # Ensure length is less than twice the std devs
        maximize='Sharpe Ratio',  # Optimize for maximum return
    )
    
    # Define a more comprehensive parameter grid for a thorough search

    
    print("\n--- Best Backtest Results ---")
    print(stats)
    
    print("\n--- Optimal Parameters Found ---")
    print(stats._strategy)
    
    print("\n--- Plotting Results of the Best Run ---")
    bt.plot()
