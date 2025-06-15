from .base import BaseIndicator
import numpy as np
import pandas as pd


class SharpeRatio(BaseIndicator):
    """
    Calculates the Sharpe Ratio for a series of returns.

    The Sharpe Ratio is a measure of risk-adjusted return. It is calculated as:
    (Mean Portfolio Return - Risk-Free Rate) / Standard Deviation of Portfolio Return
    """

    def __init__(self, prices: pd.Series, risk_free_rate: float, periods_per_year: int = 252):
        """
        Initializes the SharpeRatio indicator.

        Args:
            portfolio_returns (pd.Series): A list of periodic returns for the portfolio
                                             (e.g., daily, monthly returns).
            risk_free_rate (float): The annualized risk-free rate of return.
            periods_per_year (int, optional): The number of trading periods in a year.
                                               Defaults to 252, the typical number of
                                               trading days in a US stock market year.
                                               Use 12 for monthly, 52 for weekly.
        """
        super().__init__()

        self.portfolio_returns = np.array(prices.pct_change().dropna())
        self.annual_risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year
        
    def calculate(self) -> float:
        """
        Calculates the annualized Sharpe Ratio.

        Returns:
            float: The calculated annualized Sharpe Ratio. Returns 0.0 if the
                   standard deviation of returns is zero.
        """
        # Calculate the standard deviation of the portfolio returns.
        # This represents the portfolio's volatility.
        portfolio_std_dev = np.std(self.portfolio_returns, ddof=1) # Using sample standard deviation

        # If there is no volatility, the Sharpe Ratio is not well-defined.
        # We can return 0.0 or handle it as an exceptional case.
        if portfolio_std_dev == 0:
            return 0.0

        # Calculate the average return for the period.
        mean_portfolio_return = np.mean(self.portfolio_returns)

        # De-annualize the risk-free rate to match the period of the returns.
        periodic_risk_free_rate = (1 + self.annual_risk_free_rate)**(1/self.periods_per_year) - 1

        # Calculate the excess return over the risk-free rate for the period.
        excess_return = mean_portfolio_return - periodic_risk_free_rate

        # Calculate the Sharpe Ratio for the period.
        periodic_sharpe_ratio = excess_return / portfolio_std_dev

        # Annualize the Sharpe Ratio by multiplying by the square root of the number of periods.
        annualized_sharpe_ratio = periodic_sharpe_ratio * np.sqrt(self.periods_per_year)

        return annualized_sharpe_ratio
