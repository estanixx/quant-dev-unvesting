# A recommended base class for all financial indicators
class BaseIndicator:
    def __init__(self, *args, **kwargs):
        """Initializes the base indicator."""
        pass


    def calculate(self):
        """
        Each indicator must implement its own calculate method.
        This method should perform the actual calculation and return the result.
        """
        raise NotImplementedError("Calculation logic not implemented.")
