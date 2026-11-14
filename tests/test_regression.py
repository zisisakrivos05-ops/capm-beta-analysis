from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from capm_beta import load_prices, log_returns, ols, standard_tests, t_test

DATA = Path(__file__).resolve().parents[1] / "data" / "prices.csv"

# Values produced by Excel's regression on the same data (original workbook).
EXCEL = {
    "AMZN": dict(beta=0.8029317521544677, alpha=0.0005978321600823657, r2=0.15742157235674642),
    "STX": dict(beta=0.9814303776987026, alpha=0.0005060846210724469, r2=0.12986510139081045),
    "F": dict(beta=1.0662873560727493, alpha=-0.0002701151166044839, r2=0.2060983493815768),
    "NVDA": dict(beta=1.531699867412599, alpha=0.0008556278397415587, r2=0.3564663620886297),
    "MSFT": dict(beta=0.9821755358935567, alpha=0.0002461424685423757, r2=0.4715251971884358),
}


@pytest.fixture(scope="module")
def returns():
    return log_returns(load_prices(DATA))


def test_matches_scipy_linregress():
    rng = np.random.default_rng(0)
    x = rng.normal(size=500)
    y = 0.3 + 1.7 * x + rng.normal(scale=0.5, size=500)
    ours = ols(y, x)
    ref = stats.linregress(x, y)
    assert ours.beta.estimate == pytest.approx(ref.slope)
    assert ours.alpha.estimate == pytest.approx(ref.intercept)
    assert ours.beta.std_error == pytest.approx(ref.stderr)
    assert ours.alpha.std_error == pytest.approx(ref.intercept_stderr)
    assert ours.r_squared == pytest.approx(ref.rvalue**2)
    assert ours.beta.p_value == pytest.approx(ref.pvalue)


@pytest.mark.parametrize("ticker", EXCEL)
def test_reproduces_excel(returns, ticker):
    res = ols(returns[ticker].to_numpy(), returns["SPX"].to_numpy())
    exp = EXCEL[ticker]
    assert res.n == 4532
    assert res.beta.estimate == pytest.approx(exp["beta"], rel=1e-9)
    assert res.alpha.estimate == pytest.approx(exp["alpha"], rel=1e-9)
    assert res.r_squared == pytest.approx(exp["r2"], rel=1e-9)


def test_anova_identity():
    rng = np.random.default_rng(1)
    x = rng.normal(size=200)
    res = ols(2 * x + rng.normal(size=200), x)
    assert res.ss_regression + res.ss_residual == pytest.approx(res.ss_total)
    assert res.f_stat == pytest.approx(res.beta.t_stat**2)


def test_one_sided_p_values_sum_to_one():
    rng = np.random.default_rng(2)
    x = rng.normal(size=300)
    res = ols(1.1 * x + rng.normal(size=300), x)
    less = t_test(res.beta, res.df_residual, 1.0, "less")
    greater = t_test(res.beta, res.df_residual, 1.0, "greater")
    two = t_test(res.beta, res.df_residual, 1.0, "two-sided")
    assert less.p_value + greater.p_value == pytest.approx(1.0)
    assert two.p_value == pytest.approx(2 * min(less.p_value, greater.p_value))


def test_standard_tests_count():
    rng = np.random.default_rng(3)
    x = rng.normal(size=100)
    assert len(standard_tests(ols(x + rng.normal(size=100), x))) == 9


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        ols(np.ones(5), np.ones(5))
    with pytest.raises(ValueError):
        ols(np.arange(3.0), np.arange(4.0))
