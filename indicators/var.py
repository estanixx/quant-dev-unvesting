import numpy as np
from .base import BaseIndicator


class MonteCarloVaR(BaseIndicator):
    def __init__(self, simulated_returns, current_variables, previous_variables, confidence_level=0.95):
        super().__init__()
        self.simulated_returns = simulated_returns
        self.current_variables = current_variables
        self.previous_variables = previous_variables
        self.confidence_level = confidence_level

    def calculate(self):
        """
        Calcula el Value at Risk (VaR) usando simulaciones de Montecarlo,
        y luego lo ajusta con la fórmula: VaR = Vm * (vi / vi-1)

        Returns:
            float: Valor en Riesgo ajustado.
        """
        if self.previous_variables == 0:
            raise ValueError("previous_variables no puede ser cero.")

        # Paso 1: calcular el VaR base desde Montecarlo
        var_base = -np.percentile(self.simulated_returns, (1 - self.confidence_level) * 100)

        # Paso 2: ajustar el VaR con la fórmula de la imagen
        var_adjusted = var_base * (self.current_variables / self.previous_variables)

        return var_adjusted
