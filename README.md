# UNvesting: Quant Stratarb
This project is intended to develop a quantitative trading strategy based on statistical arbitrage.

## How to run
### 1. Install requirements
`pip install --upgrade pip
pip install -r requirements.txt`
De esta forma tendrán instalado lo necesario.

### Willing to add a new lib to the project?
1. You need to have installed the initial requirements (IMPORTANT).
2. Install the lib on your pc `pip install xxx`
3. `pip list --format=freeze > requirements.txt`

### Correr la app
`python main.py`

## File explanation.
### Configuration
- `config/config.py` contains global variables and constants.
- `test.ipynb` is a notebook for strategy testing.
### Executors
This class is responsible of performing broker-related actions, such as fetching data and executing purchase/selling operations. In this case we have:
- `executors/executor.py` contains the `Executor`, an abstract class that contains the methods and properties required for an executor.
- `executors/mt5_executor.py` contains the `MT5Executor`, a class that runs given strategies on MT5.
### Strategies
- `strategies/strategy.py` contains a guideline strategy.
- `strategies/pair_trading_strategy.py` contains the developed strategy.