import MetaTrader5 as mt5
import pandas as pd
from typing import List, Dict, Optional
from statsmodels.api import OLS, add_constant
from dataclasses import dataclass
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.stattools import coint
import time
from strategies.pair_trading_strategy import PairTradingStrategy, CointegrationResult
from executors.executor import Executor

class MT5Executor(Executor):

    def __init__(self, strategies: List[PairTradingStrategy]):
        self.strategies = strategies
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize MT5 connection"""
        if not mt5.initialize():
            print("MT5 initialization failed:", mt5.last_error())
            quit()
    
    def fetch_data(self, symbols: List[str], n_candles: int) -> Dict[str, pd.DataFrame]:
        """Fetch symbol data from MT5"""
        symbol_data = {}
        for symbol in symbols:
            print("Importing", symbol)
            mt5.symbol_select(symbol, True)
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, n_candles)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                symbol_data[symbol] = df
            else:
                print(f"⚠️ Could not get data for {symbol}")
        return symbol_data
    
    def shutdown(self) -> None:
        """Shutdown MT5 connection"""
        mt5.shutdown()
    
    def get_valid_volume(self, symbol: str, desired_volume: float) -> Optional[float]:
        """Get valid trade volume for a symbol"""
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"❌ Could not get symbol info for {symbol}")
            return None

        min_vol = info.volume_min
        max_vol = info.volume_max
        step = info.volume_step

        volume = max(min_vol, desired_volume)
        volume = min(volume, max_vol)

        steps = round(volume / step)
        valid_volume = round(steps * step, 2)

        print(f"ℹ️ {symbol} - min_vol: {min_vol}, step: {step}, final volume: {valid_volume}")
        return valid_volume
    
    def execute_trade(self, pair: CointegrationResult, direction: int) -> None:
        """Execute a pair trade"""
        sym1, sym2 = pair.sym1, pair.sym2
        print(f"📡 Sending MT5 orders: {'LONG' if direction == 1 else 'SHORT'} spread {sym1} - {sym2}...")
        
        lot1 = self.get_valid_volume(sym1, self.strategies[0].lot_size)
        lot2 = self.get_valid_volume(sym2, abs(pair.hedge_ratio) * self.strategies[0].lot_size)

        if lot1 is None or lot2 is None:
            return

        if not mt5.symbol_select(sym1, True) or not mt5.symbol_select(sym2, True):
            print(f"❌ Could not select one of the symbols: {sym1}, {sym2}")
            return

        price1 = mt5.symbol_info_tick(sym1).ask if direction == 1 else mt5.symbol_info_tick(sym1).bid
        price2 = mt5.symbol_info_tick(sym2).bid if direction == 1 else mt5.symbol_info_tick(sym2).ask

        type1 = mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL
        type2 = mt5.ORDER_TYPE_SELL if direction == 1 else mt5.ORDER_TYPE_BUY

        # Order 1
        order1 = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": sym1,
            "volume": lot1,
            "type": type1,
            "price": price1,
            "deviation": 20,
            "magic": 123456,
            "comment": "Spread Entry",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }

        result1 = mt5.order_send(order1)
        self._process_order_result(result1, sym1)

        time.sleep(1)

        # Order 2
        order2 = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": sym2,
            "volume": lot2,
            "type": type2,
            "price": price2,
            "deviation": 20,
            "magic": 123456,
            "comment": "Spread Entry",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }

        result2 = mt5.order_send(order2)
        self._process_order_result(result2, sym2)

        spread_entry = pair.spread.iloc[-1]
        print(f"🎯 Spread: {spread_entry:.2f} | TP: {pair.mean:.2f} | SL: {spread_entry + direction * 1.5 * pair.std:.2f}")
    
    def _process_order_result(self, result, symbol: str) -> None:
        """Process order result"""
        if result is None:
            print(f"❌ Error sending order for {symbol}. Empty return.")
        elif result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Order {symbol} failed. Code: {result.retcode}")
        else:
            print(f"✅ Order {symbol} sent successfully.")
    
    def run_strategies(self) -> None:
        """Run all strategies and execute trades"""
        for strategy in self.strategies:
            strategy.fetch_data(self)
            signals = strategy.get_trading_signals()
            
            for pair, direction in signals:
                self.execute_trade(pair, direction)