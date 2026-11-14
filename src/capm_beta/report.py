"""Run the full analysis and write tables, figures and a Markdown report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import plots
from .data import MARKET, TICKER_NAMES, load_prices, log_returns
from .hypothesis import TestResult, standard_tests
from .regression import RegressionResult, ols


@dataclass
class StockAnalysis:
    ticker: str
    name: str
    result: RegressionResult
    tests: list[TestResult]


def analyse(prices: pd.DataFrame, market: str = MARKET, significance: float = 0.05):
    returns = log_returns(prices)
    x = returns[market].to_numpy()
    out = []
    for ticker in returns.columns:
        if ticker == market:
            continue
        res = ols(returns[ticker].to_numpy(), x)
        out.append(
            StockAnalysis(ticker, TICKER_NAMES.get(ticker, ticker), res,
                          standard_tests(res, significance))
        )
    return returns, out


def summary_table(analyses: list[StockAnalysis]) -> pd.DataFrame:
    rows = []
    for a in analyses:
        r = a.result
        rows.append({
            "ticker": a.ticker,
            "name": a.name,
            "n": r.n,
            "alpha": r.alpha.estimate,
            "alpha_se": r.alpha.std_error,
            "alpha_p": r.alpha.p_value,
            "beta": r.beta.estimate,
            "beta_se": r.beta.std_error,
            "beta_ci_low": r.beta.ci_low,
            "beta_ci_high": r.beta.ci_high,
            "r_squared": r.r_squared,
            "adj_r_squared": r.adj_r_squared,
            "std_error": r.std_error,
            "f_stat": r.f_stat,
        })
    return pd.DataFrame(rows)


def tests_table(analyses: list[StockAnalysis]) -> pd.DataFrame:
    rows = []
    for a in analyses:
        for t in a.tests:
            rows.append({
                "ticker": a.ticker,
                "hypotheses": t.hypotheses,
                "tail": t.tail,
                "t_stat": t.t_stat,
                "p_value": t.p_value,
                "decision": t.decision,
            })
    return pd.DataFrame(rows)


def _interpret(a: StockAnalysis) -> str:
    b = a.result.beta
    by_key = {(t.parameter, t.null_value, t.tail): t for t in a.tests}
    two_sided_1 = by_key[("beta", 1.0, "two-sided")]
    if not two_sided_1.reject_null:
        risk = "statistically indistinguishable from the market (β = 1 not rejected)"
    elif b.estimate > 1:
        risk = "**more volatile** than the market (β > 1)"
    else:
        risk = "**less volatile** than the market (β < 1)"
    alpha = by_key[("alpha", 0.0, "two-sided")]
    alpha_txt = (
        f"a significant daily alpha of {a.result.alpha.estimate:.5f}"
        if alpha.reject_null
        else "no significant abnormal return (α = 0 not rejected)"
    )
    return (f"- **{a.name} ({a.ticker})** — β = {b.estimate:.3f} "
            f"[{b.ci_low:.3f}, {b.ci_high:.3f}]: {risk}; {alpha_txt}. "
            f"The market explains {a.result.r_squared:.0%} of daily variance.")


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def write_report(
    data_path: str | Path, out_dir: str | Path, significance: float = 0.05
) -> pd.DataFrame:
    out_dir = Path(out_dir)
    fig_dir = out_dir / "figures"
    prices = load_prices(data_path)
    returns, analyses = analyse(prices, significance=significance)

    summary = summary_table(analyses)
    tests = tests_table(analyses)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "summary.csv", index=False)
    tests.to_csv(out_dir / "hypothesis_tests.csv", index=False)

    x = returns[MARKET].to_numpy()
    for a in analyses:
        plots.diagnostics(x, returns[a.ticker].to_numpy(), a.result, a.name,
                          fig_dir / f"{a.ticker}_diagnostics.png")
    plots.beta_comparison(summary, fig_dir / "beta_comparison.png")

    view = summary[["ticker", "name", "beta", "beta_ci_low", "beta_ci_high",
                    "alpha", "alpha_p", "r_squared"]].copy()
    for c in ("beta", "beta_ci_low", "beta_ci_high", "r_squared"):
        view[c] = view[c].map("{:.3f}".format)
    view["alpha"] = view["alpha"].map("{:.5f}".format)
    view["alpha_p"] = view["alpha_p"].map("{:.4f}".format)

    tview = tests.copy()
    tview["t_stat"] = tview["t_stat"].map("{:.3f}".format)
    tview["p_value"] = tview["p_value"].map("{:.5f}".format)

    start, end = returns.index.min().date(), returns.index.max().date()
    md = [
        "# CAPM beta analysis — results",
        "",
        f"Daily log returns, {start} to {end} ({len(returns)} observations per stock). "
        f"Market proxy: S&P 500. Significance level: {significance}.",
        "",
        "## Summary",
        "",
        _md_table(view),
        "",
        "![Beta comparison](figures/beta_comparison.png)",
        "",
        "## Interpretation",
        "",
        *[_interpret(a) for a in analyses],
        "",
        "## Hypothesis tests",
        "",
        _md_table(tview),
        "",
        "## Diagnostics",
        "",
        *[f"### {a.name}\n\n![{a.name}](figures/{a.ticker}_diagnostics.png)\n" for a in analyses],
    ]
    (out_dir / "report.md").write_text("\n".join(md), encoding="utf-8")
    return summary
