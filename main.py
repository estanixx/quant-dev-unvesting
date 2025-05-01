
# Example usage
if __name__ == "__main__":
    from config.config import TICKERS, N_CANDLES, LOT
    from strategies.pair_trading_strategy import PairTradingStrategy
    from executors.mt5_executor import MT5Executor
    
    strategy = PairTradingStrategy(tickers=TICKERS, n_candles=N_CANDLES, lot_size=LOT)
    executor = MT5Executor(strategies=[strategy])
    
    try:
        executor.run_strategies()
    finally:
        executor.shutdown()