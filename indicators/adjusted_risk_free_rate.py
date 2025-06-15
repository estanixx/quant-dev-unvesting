# indicators/adjusted_risk_free_rate.py

from .base import BaseIndicator

class AdjustedRiskFreeRate(BaseIndicator):
    """
    Calculates the risk-free rate adjusted for currency risk (riesgo cambiario).

    This indicator is used to determine the equivalent risk-free rate in a
    domestic currency when the original risk-free rate is from a foreign currency.
    The formula applied is:
    Adjusted Rate = (1 + Foreign Risk-Free Rate) * (1 + Expected Exchange Rate Change) - 1
    """

    def __init__(self, foreign_risk_free_rate: float, expected_exchange_rate_change: float):
        """
        Initializes the AdjustedRiskFreeRate indicator.

        Args:
            foreign_risk_free_rate (float): The annualized risk-free rate of the
                                            foreign currency (e.g., US T-Bill rate).
                                            Expressed as a decimal (e.g., 0.05 for 5%).
            expected_exchange_rate_change (float): The expected annualized change in the
                                                   exchange rate. This represents the
                                                   'riesgo cambiario'.
                                                   - A positive value (e.g., 0.03) means the
                                                     foreign currency is expected to
                                                     APPRECIATE against the domestic currency.
                                                   - A negative value (e.g., -0.02) means it
                                                     is expected to DEPRECIATE.
        """
        super().__init__()
        self.foreign_risk_free_rate = foreign_risk_free_rate
        self.expected_exchange_rate_change = expected_exchange_rate_change

    def calculate(self) -> float:
        """
        Performs the calculation for the currency-adjusted risk-free rate.

        Returns:
            float: The calculated annualized risk-free rate in the domestic currency.
        """
        # This formula compounds the foreign interest rate with the expected
        # gain or loss from currency fluctuation to find the effective rate
        # in the domestic currency.
        adjusted_rate = (1 + self.foreign_risk_free_rate) * (1 + self.expected_exchange_rate_change) - 1
        return adjusted_rate

