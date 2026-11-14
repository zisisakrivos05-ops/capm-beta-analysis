"""Ordinary least squares for the single-index (market) model.

    r_stock = alpha + beta * r_market + e

Implemented from first principles with NumPy so every statistic is visible,
and reproducing the output of Excel's Data Analysis -> Regression tool
(regression statistics, ANOVA table, coefficient table, residuals).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class Coefficient:
    name: str
    estimate: float
    std_error: float
    t_stat: float
    p_value: float
    ci_low: float
    ci_high: float


@dataclass(frozen=True)
class RegressionResult:
    n: int
    multiple_r: float
    r_squared: float
    adj_r_squared: float
    std_error: float  # standard error of the regression (s_e)
    ss_regression: float
    ss_residual: float
    ss_total: float
    f_stat: float
    f_p_value: float
    alpha: Coefficient
    beta: Coefficient
    fitted: np.ndarray = field(repr=False)
    residuals: np.ndarray = field(repr=False)

    @property
    def df_residual(self) -> int:
        return self.n - 2


def ols(y: np.ndarray, x: np.ndarray, confidence: float = 0.95) -> RegressionResult:
    """Fit y = alpha + beta * x by OLS and return the full set of statistics."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    if y.shape != x.shape or y.ndim != 1:
        raise ValueError("x and y must be 1-D arrays of equal length")
    n = y.size
    if n < 3:
        raise ValueError("Need at least 3 observations")

    x_mean, y_mean = x.mean(), y.mean()
    sxx = np.sum((x - x_mean) ** 2)
    sxy = np.sum((x - x_mean) * (y - y_mean))
    if sxx == 0:
        raise ValueError("x has zero variance")

    beta = sxy / sxx
    alpha = y_mean - beta * x_mean

    fitted = alpha + beta * x
    resid = y - fitted

    df_res = n - 2
    ss_tot = np.sum((y - y_mean) ** 2)
    ss_res = np.sum(resid**2)
    ss_reg = ss_tot - ss_res

    r2 = ss_reg / ss_tot
    adj_r2 = 1 - (1 - r2) * (n - 1) / df_res
    s_e = np.sqrt(ss_res / df_res)

    f_stat = (ss_reg / 1) / (ss_res / df_res)
    f_p = stats.f.sf(f_stat, 1, df_res)

    se_beta = s_e / np.sqrt(sxx)
    se_alpha = s_e * np.sqrt(1 / n + x_mean**2 / sxx)

    t_crit = stats.t.ppf(1 - (1 - confidence) / 2, df_res)

    def coef(name: str, est: float, se: float) -> Coefficient:
        t = est / se
        return Coefficient(
            name=name,
            estimate=float(est),
            std_error=float(se),
            t_stat=float(t),
            p_value=float(2 * stats.t.sf(abs(t), df_res)),
            ci_low=float(est - t_crit * se),
            ci_high=float(est + t_crit * se),
        )

    return RegressionResult(
        n=n,
        multiple_r=float(np.sqrt(r2)),
        r_squared=float(r2),
        adj_r_squared=float(adj_r2),
        std_error=float(s_e),
        ss_regression=float(ss_reg),
        ss_residual=float(ss_res),
        ss_total=float(ss_tot),
        f_stat=float(f_stat),
        f_p_value=float(f_p),
        alpha=coef("alpha", alpha, se_alpha),
        beta=coef("beta", beta, se_beta),
        fitted=fitted,
        residuals=resid,
    )
