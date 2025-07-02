import pandas as pd
import numpy as np
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# --- Custom Indicator Functions ---

def psar(high, low, initial_acceleration, max_acceleration, acceleration_step):
    """Custom implementation of the Parabolic SAR (PSAR) indicator."""
    length = len(high)
    psar_values = np.zeros(length)
    bull = True
    af = initial_acceleration
    ep = low[0]
    psar_values[0] = high[0]

    for i in range(2, length):
        if bull:
            psar_values[i] = psar_values[i - 1] + af * (ep - psar_values[i - 1])
        else:
            psar_values[i] = psar_values[i - 1] - af * (psar_values[i - 1] - ep)

        reverse = False
        if bull and low[i] < psar_values[i]:
            bull = False
            reverse = True
            psar_values[i] = ep
            ep = low[i]
            af = initial_acceleration
        elif not bull and high[i] > psar_values[i]:
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
                if low[i - 1] < psar_values[i]: psar_values[i] = low[i - 1]
                if low[i - 2] < psar_values[i]: psar_values[i] = low[i - 2]
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + acceleration_step, max_acceleration)
                if high[i - 1] > psar_values[i]: psar_values[i] = high[i - 1]
                if high[i - 2] > psar_values[i]: psar_values[i] = high[i - 2]
    
    psar_values[psar_values == 0] = np.nan
    return psar_values

def relative_strength_indicator(close: np.ndarray, length: int = 14) -> np.ndarray:
    """Calculates the Relative Strength Index (RSI)."""
    close_series = pd.Series(close)
    delta = close_series.diff(1)
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    avg_gains = gains.ewm(com=length - 1, min_periods=length).mean()
    avg_losses = losses.ewm(com=length - 1, min_periods=length).mean()
    rs = avg_gains / avg_losses
    rs = rs.replace([np.inf, -np.inf], np.nan).fillna(0)
    rsi = 100 - (100 / (1 + rs))
    return rsi.to_numpy()

def stochastic_rsi(close: np.ndarray, rsi_length: int, stoch_length: int, k_smooth: int, d_smooth: int) -> tuple[np.ndarray, np.ndarray]:
    """Calculates the Stochastic RSI, returning the %K and %D lines."""
    rsi = relative_strength_indicator(close, length=rsi_length)
    rsi_series = pd.Series(rsi)
    min_rsi = rsi_series.rolling(window=stoch_length).min()
    max_rsi = rsi_series.rolling(window=stoch_length).max()
    stoch_rsi_raw = (rsi_series - min_rsi) / (max_rsi - min_rsi)
    stoch_k = stoch_rsi_raw.rolling(window=k_smooth).mean() * 100
    stoch_d = stoch_k.rolling(window=d_smooth).mean()
    return stoch_k.to_numpy(), stoch_d.to_numpy(), stoch_rsi_raw.to_numpy() * 100

# --- Define the Combined Strategy ---
class PSARStochRSIStrategy(Strategy):
    # --- Define Strategy Parameters for Optimization ---
    psar_iaf = 0.05
    psar_maf = 0.2
    psar_step = 0.03
    rsi_length = 16
    stoch_length = 16
    k_smooth = 3
    d_smooth = 3
    threshold = 30
    def init(self):
        """This method is called once at the beginning to calculate indicators."""
        self.overbought_level = 50 + self.threshold
        self.oversold_level = 50 - self.threshold
        self.psar = self.I(psar, self.data.High, self.data.Low, self.psar_iaf, self.psar_maf, self.psar_step, name="PSAR")
        self.stoch_k, self.stoch_d, self.stoch = self.I(
            stochastic_rsi,
            self.data.Close,
            self.rsi_length,
            self.stoch_length,
            self.k_smooth,
            self.d_smooth,
            name="StochRSI"
        )

    def next(self):
        """This method is called for each bar to define the trading logic."""
        psar_is_below = self.psar[-1] < self.data.Close[-1]
        psar_was_above = self.psar[-2] > self.data.Close[-2]
        stoch_buy_signal = crossover(self.stoch_k, self.stoch_d) and self.stoch_d[-1] < self.oversold_level
        stoch_sell_signal = crossover(self.stoch_d, self.stoch_k) and self.stoch_d[-1] > self.overbought_level
        # stoch_buy_signal = self.stoch[-2] <= self.oversold_level and self.stoch[-1] > self.oversold_level
        # stoch_sell_signal =  self.stoch[-2] >= self.overbought_level and self.stoch[-1] < self.overbought_level


        if psar_is_below and stoch_buy_signal:
            if self.position.is_short:
                self.position.close()
            self.buy()
        elif not psar_is_below and stoch_sell_signal:
            if self.position.is_long:
                self.position.close()
            self.sell()
            
        if self.position.is_long and psar_was_above and self.data.Close[-1] < self.psar[-1]:
            self.position.close()
        elif self.position.is_short and not psar_was_above and self.data.Close[-1] > self.psar[-1]:
            self.position.close()

# --- Example Usage ---
if __name__ == '__main__':
    today = pd.Timestamp.today().normalize()
    start_date = today - pd.DateOffset(years=3)
    ticker_symbol = 'NVDA'
    
    print(f"--- Downloading data for {ticker_symbol} ---")
    data = yf.download(ticker_symbol, start=start_date, end=today, multi_level_index=False)

    bt = Backtest(data, PSARStochRSIStrategy, cash=100_000, commission=.001)
    
    print("\n--- Running Optimization with Wider Ranges ---")
    stats = bt.run()
    # Define a more comprehensive parameter grid for a thorough search
    # stats = bt.optimize(
    #     rsi_length=range(8, 31, 4),
    #     stoch_length=range(8, 31, 4),
    #     psar_iaf=list(np.arange(0.01, 0.06, 0.01)),
    #     psar_maf=list(np.arange(0.1, 0.51, 0.1)),
    #     psar_step=list(np.arange(0.01, 0.04, 0.01)),
    #     maximize='Sharpe Ratio',
    #     # Add constraints to ensure valid PSAR parameter combinations
    #     constraint=lambda p: p.psar_iaf < p.psar_maf and p.psar_step <= p.psar_iaf
    # )
    
    print("\n--- Best Backtest Results ---")
    print(stats)
    
    print("\n--- Optimal Parameters Found ---")
    print(stats._strategy)
    
    print("\n--- Plotting Results of the Best Run ---")
    bt.plot()
