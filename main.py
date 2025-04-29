
# Example usage
if __name__ == "__main__":
    from config.config import TICKERS, N_CANDLES, LOT
    from strategy import PairTradingStrategy
    from mt5exec import MT5Executor
    
    strategy = PairTradingStrategy(tickers=TICKERS, n_candles=N_CANDLES, lot_size=LOT)
    executor = MT5Executor(strategies=[strategy])
    
    try:
        executor.run_strategies()
    finally:
        executor.shutdown()