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
- `config/config.py` contains global variables and constants.
- `mt5exec.py` contains the `MT5Executor`, a class that runs given strategies on MT5.
- `strategy.py` contains the developed strategy.
- `test.ipynb` is a notebook for strategy testing.