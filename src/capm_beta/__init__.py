"""CAPM beta estimation and hypothesis testing for equities vs the S&P 500."""

from .data import load_prices, log_returns
from .hypothesis import standard_tests, t_test
from .regression import ols

__all__ = ["load_prices", "log_returns", "ols", "t_test", "standard_tests"]
__version__ = "1.0.0"
