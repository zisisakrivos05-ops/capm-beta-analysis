"""t-tests on the regression coefficients.

For each stock we test, at significance level 0.05:

* beta = 1  - does the stock move one-for-one with the market?
* beta = 0  - is the stock related to the market at all?
* alpha = 0 - is there abnormal return (Jensen's alpha) beyond what beta explains?

each as a two-sided, left-tailed and right-tailed test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from scipy import stats

from .regression import Coefficient, RegressionResult

Tail = Literal["two-sided", "less", "greater"]

_H1_SYMBOL = {"two-sided": "≠", "less": "<", "greater": ">"}
_GREEK = {"alpha": "α", "beta": "β"}


@dataclass(frozen=True)
class TestResult:
    parameter: str
    null_value: float
    tail: Tail
    t_stat: float
    p_value: float
    significance: float

    @property
    def reject_null(self) -> bool:
        return self.p_value < self.significance

    @property
    def hypotheses(self) -> str:
        p = _GREEK.get(self.parameter, self.parameter)
        v = f"{self.null_value:g}"
        return f"H0: {p}={v}  H1: {p}{_H1_SYMBOL[self.tail]}{v}"

    @property
    def decision(self) -> str:
        return "Reject H0" if self.reject_null else "Fail to reject H0"


def t_test(
    coef: Coefficient,
    df: int,
    null_value: float = 0.0,
    tail: Tail = "two-sided",
    significance: float = 0.05,
) -> TestResult:
    """t-test of H0: coefficient = null_value against the given alternative."""
    t = (coef.estimate - null_value) / coef.std_error
    if tail == "two-sided":
        p = 2 * stats.t.sf(abs(t), df)
    elif tail == "less":
        p = stats.t.cdf(t, df)
    elif tail == "greater":
        p = stats.t.sf(t, df)
    else:
        raise ValueError(f"Unknown tail: {tail!r}")
    return TestResult(coef.name, null_value, tail, float(t), float(p), significance)


def standard_tests(result: RegressionResult, significance: float = 0.05) -> list[TestResult]:
    """The nine tests from the original analysis: {β=1, β=0, α=0} × {≠, <, >}."""
    tests = []
    for tail in ("two-sided", "less", "greater"):
        for coef, null in ((result.beta, 1.0), (result.beta, 0.0), (result.alpha, 0.0)):
            tests.append(t_test(coef, result.df_residual, null, tail, significance))
    return tests
