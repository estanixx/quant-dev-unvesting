from base import BaseIndicator
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

class CorrelationIndicator(BaseIndicator):
    """
    Calcula la correlación móvil entre los precios de dos activos.

    Este indicador es útil para estrategias de pairs trading, diversificación o para
    identificar cambios de régimen en la relación entre dos activos.
    """

    def __init__(self, asset_a_prices: pd.Series, asset_b_prices: pd.Series, window_size: int):
        """
        Inicializa el CorrelationIndicator.

        Args:
            asset_a_prices (pd.Series): Una serie de pandas con los precios históricos del activo A.
                                        El índice debe ser de tipo datetime.
            asset_b_prices (pd.Series): Una serie de pandas con los precios históricos del activo B.
                                        Debe tener el mismo índice y longitud que asset_a_prices.
            window_size (int): El número de períodos (ej. días) para calcular la correlación móvil.
                               Por ejemplo, 20 para una correlación móvil de 20 días.
        """
        super().__init__()

        self.asset_a_prices = asset_a_prices
        self.asset_b_prices = asset_b_prices
        self.window_size = window_size

    def calculate(self) -> pd.Series:
        """
        Realiza el cálculo de la correlación móvil.

        Returns:
            pd.Series: Una serie de pandas que contiene la correlación móvil
                       entre los dos activos para cada punto en el tiempo.
                       Los primeros 'window_size - 1' valores serán NaN.
        """
        rolling_correlation = self.asset_a_prices.rolling(
            window=self.window_size
        ).corr(
            self.asset_b_prices
        )
        return rolling_correlation
    

# El ejemplo no estaba funcionando a la hora de codificar el método. YFRateLimitError('Too Many Requests. Rate limited. Try after a while.')
# Puede que tenga errores.

# 1. Definir los tickers y el período de tiempo
ticker_a = 'KO'  
ticker_b = 'PEP'  
start_date = datetime.now() - timedelta(days=365)
end_date = datetime.now()

# 2. Descargar los datos históricos usando yfinance
data = yf.download([ticker_a, ticker_b], start=start_date, end=end_date)

precios_a = data['Close'][ticker_a]
precios_b = data['Close'][ticker_b]

# Eliminar cualquier fila con datos faltantes si yfinance no devuelve datos para un día
precios_a.dropna(inplace=True)
precios_b.dropna(inplace=True)
common_index = precios_a.index.intersection(precios_b.index)
precios_a = precios_a.loc[common_index]
precios_b = precios_b.loc[common_index]


# 3. Instanciar y usar el indicador
# Usaremos una correlación móvil de 60 días (aprox. 3 meses de trading)
ventana_correlacion = 60
corr_indicator = CorrelationIndicator(
    asset_a_prices=precios_a,
    asset_b_prices=precios_b,
    window_size=ventana_correlacion
)

# 4. Calcular los valores del indicador
serie_correlacion = corr_indicator.calculate()

# 5. Mostrar los últimos valores de la correlación
print(f"\n--- Correlación Móvil de {ventana_correlacion} días para {ticker_a}/{ticker_b} (últimos 10 valores) ---")
print(serie_correlacion.tail(10))


