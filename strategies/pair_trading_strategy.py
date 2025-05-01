import numpy as np
import pandas as pd
from itertools import combinations
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from statsmodels.tsa.stattools import adfuller
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from strategies.strategy import Strategy
@dataclass
class CointegrationResult:
    sym1: str
    sym2: str
    hedge_ratio: float
    pvalue: float
    spread: pd.Series
    mean: float = 0.0
    std: float = 0.0
    zscore: Optional[pd.Series] = None

class PairTradingStrategy(Strategy):
    _v = '1.0.1'
    def __init__(self, tickers: List[str], n_candles: int = 1000, lot_size: float = 0.1):
        self.tickers = tickers
        self.n_candles = n_candles
        self.lot_size = lot_size
        self.symbol_data: Dict[str, pd.DataFrame] = {}
        self.cointegrated_pairs: List[CointegrationResult] = []
    
    def fetch_data(self, executor) -> None:
        """Fetch price data for all tickers"""
        self.symbol_data = executor.fetch_data(self.tickers, self.n_candles)

    def test_cointegration(self, sym1: str, sym2: str) -> Optional[CointegrationResult]:
        """Test for cointegration between two symbols"""
        s1 = self.symbol_data.get(sym1)
        s2 = self.symbol_data.get(sym2)

        if s1 is None or s2 is None:
            return None
        s1 = s1['close']
        s2 = s2['close']
            
        df_pair = pd.concat([s1, s2], axis=1, join='inner').dropna()
        df_pair.columns = ['y', 'x']
        
        if len(df_pair) < 200:
            return None

        X = add_constant(df_pair['x'])
        model = OLS(df_pair['y'], X).fit()
        hedge_ratio = model.params['x']
        spread = df_pair['y'] - hedge_ratio * df_pair['x']
        adf_pvalue = adfuller(spread)[1]

        if adf_pvalue < 0.05:
            mean = spread.mean()
            std = spread.std()
            zscore = (spread - mean) / std
            
            return CointegrationResult(
                sym1=sym1,
                sym2=sym2,
                hedge_ratio=hedge_ratio,
                pvalue=adf_pvalue,
                spread=spread,
                mean=mean,
                std=std,
                zscore=zscore
            )
        return None
    
    def find_cointegrated_pairs(self) -> None:
        """Find all cointegrated pairs among tickers"""
        self.cointegrated_pairs = []
        for sym1, sym2 in combinations(self.symbol_data.keys(), 2):
            result = self.test_cointegration(sym1, sym2)
            if result:
                self.cointegrated_pairs.append(result)
                current_z = result.zscore.iloc[-1]
                print(f"✅ {sym1}-{sym2} cointegrated | p={result.pvalue:.4f} | β={result.hedge_ratio:.4f} | z={current_z:.2f}")
    
    def get_trading_signals(self) -> List[Tuple[CointegrationResult, int]]:
        """Get trading signals based on current z-score"""
        signals = []
        self.find_cointegrated_pairs()
        for pair in self.cointegrated_pairs:
            current_z = pair.zscore.iloc[-1]
            if 2 <= abs(current_z) < 3:
                direction = -1 if current_z > 0 else 1
                signals.append((pair, direction))
        return signals
    
    def backtest(self) -> None:
        """Backtest the strategy (to be implemented)"""
        raise NotImplementedError("Backtesting functionality not yet implemented")



