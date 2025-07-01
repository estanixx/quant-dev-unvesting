from .base import BaseIndicator
import numpy as np
from typing import List, Union

class ExpectedShortfallMonteCarlo(BaseIndicator):
    """
    Calculates the Expected Shortfall (ES) using the Monte Carlo simulation method.

    Expected Shortfall, also known as Conditional Value at Risk (CVaR), measures
    the expected loss on a portfolio in the worst-case scenarios. It is the average
    of all losses that are greater than or equal to the Value at Risk (VaR) at a
    given confidence level.
    """

    def __init__(self,
                 returns: Union[List[float], np.ndarray],
                 confidence_level: float = 0.95,
                 simulations: int = 10000,
                 time_horizon: int = 1):
        """
        Initializes the ExpectedShortfallMonteCarlo indicator.

        Args:
            returns (Union[List[float], np.ndarray]): A list or NumPy array of historical
                                                     periodic returns (e.g., daily returns).
            confidence_level (float): The confidence level for the ES calculation (e.g., 0.95 for 95%).
                                      Defaults to 0.95.
            simulations (int): The number of Monte Carlo simulations to run.
                               Defaults to 10000.
            time_horizon (int): The time horizon for the projection, in the same period unit
                                as the returns (e.g., days if using daily returns). Defaults to 1.
        """
        super().__init__()
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)

        if returns.ndim != 1 or len(returns) == 0:
            raise ValueError("Returns must be a non-empty 1D array or list.")

        if not (0 < confidence_level < 1):
            raise ValueError("Confidence level must be between 0 and 1.")

        self.returns = returns
        self.confidence_level = confidence_level
        self.simulations = simulations
        self.time_horizon = time_horizon
        self.alpha = 1 - confidence_level

    def calculate(self) -> float:
        """
        Performs the Monte Carlo simulation to calculate Expected Shortfall.

        The method simulates future returns using the historical mean and standard
        deviation of the provided returns data. It then calculates VaR and averages
        the tail losses beyond the VaR to compute ES.

        Returns:
            float: The calculated Expected Shortfall as a negative value,
                   representing a loss.
        """
        # --- Step 1: Calculate historical mean and standard deviation ---
        # These will be the parameters for our random walk simulation.
        mu = np.mean(self.returns)
        sigma = np.std(self.returns)

        # --- Step 2: Run Monte Carlo Simulation ---
        # We simulate 'simulations' number of possible outcomes for the portfolio's
        # return over the specified 'time_horizon'.
        # We assume returns follow a normal distribution (a common assumption in finance).
        simulated_returns = np.random.normal(
            loc=mu * self.time_horizon,
            scale=sigma * np.sqrt(self.time_horizon),
            size=self.simulations
        )

        # --- Step 3: Calculate Value at Risk (VaR) ---
        # VaR is the threshold of loss we don't expect to exceed with the given
        # confidence level. It's calculated as a percentile of the simulated returns.
        # For example, for a 95% confidence level, VaR is the 5th percentile of returns.
        var = np.percentile(simulated_returns, self.alpha * 100)

        # --- Step 4: Calculate Expected Shortfall (ES) ---
        # ES is the average of the returns that are worse (less than or equal to) the VaR.
        # This gives us the expected value of our loss if we hit that tail event.
        tail_losses = simulated_returns[simulated_returns <= var]
        expected_shortfall = np.mean(tail_losses)

        return float(expected_shortfall)


# --- Example Usage ---
if __name__ == '__main__':
    # Generate some sample historical daily returns
    # In a real scenario, you would load this data from a file or API
    np.random.seed(42) # for reproducibility
    sample_returns = np.random.normal(loc=0.0005, scale=0.02, size=252) # 1 year of daily returns

    print("--- Expected Shortfall (ES) Calculation Example ---")
    print(f"Number of historical returns: {len(sample_returns)}")
    print(f"Average historical daily return: {np.mean(sample_returns):.4%}")
    print(f"Historical daily volatility: {np.std(sample_returns):.4%}\n")

    # --- Case 1: 95% Confidence Level ---
    try:
        es_calculator_95 = ExpectedShortfallMonteCarlo(
            returns=sample_returns,
            confidence_level=0.95,
            simulations=20000,
            time_horizon=10 # Projecting over 10 days
        )
        expected_shortfall_95 = es_calculator_95.calculate()

        print(f"Confidence Level: 95%")
        print(f"Time Horizon: {es_calculator_95.time_horizon} days")
        print(f"Simulations: {es_calculator_95.simulations}")
        print(f"Expected Shortfall (10-day): {expected_shortfall_95:.2%}\n")
        print(f"Interpretation: If a 1-in-20 worst-case event occurs over the next 10 days,")
        print(f"we expect an average loss of {abs(expected_shortfall_95):.2%}.\n")

    except (ValueError, NotImplementedError) as e:
        print(f"Error calculating 95% ES: {e}")


    # --- Case 2: 99% Confidence Level ---
    try:
        es_calculator_99 = ExpectedShortfallMonteCarlo(
            returns=sample_returns,
            confidence_level=0.99,
            simulations=20000,
            time_horizon=10 # Projecting over 10 days
        )
        expected_shortfall_99 = es_calculator_99.calculate()

        print(f"Confidence Level: 99%")
        print(f"Time Horizon: {es_calculator_99.time_horizon} days")
        print(f"Simulations: {es_calculator_99.simulations}")
        print(f"Expected Shortfall (10-day): {expected_shortfall_99:.2%}\n")
        print(f"Interpretation: If a 1-in-100 worst-case event occurs over the next 10 days,")
        print(f"we expect an average loss of {abs(expected_shortfall_99):.2%}.\n")

    except (ValueError, NotImplementedError) as e:
        print(f"Error calculating 99% ES: {e}")
