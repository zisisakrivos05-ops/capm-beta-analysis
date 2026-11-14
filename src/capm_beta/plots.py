"""Diagnostic charts for each regression."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

from .regression import RegressionResult  # noqa: E402

DOT = "#2a6fdb"
LINE = "#d1495b"
GRID = dict(color="#dddddd", linewidth=0.6)


def _style(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, **GRID)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def diagnostics(
    x: np.ndarray, y: np.ndarray, res: RegressionResult, name: str, out: Path, bins: int = 67
) -> Path:
    """Line-fit plot, residual plot and residual histogram in one figure."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))

    ax = axes[0]
    ax.scatter(x, y, s=4, alpha=0.35, color=DOT, linewidths=0)
    xs = np.linspace(x.min(), x.max(), 2)
    ax.plot(xs, res.alpha.estimate + res.beta.estimate * xs, color=LINE, lw=2,
            label=f"β = {res.beta.estimate:.3f}, R² = {res.r_squared:.3f}")
    ax.legend(frameon=False, loc="upper left")
    _style(ax, f"{name}: line fit", "S&P 500 log return", f"{name} log return")

    ax = axes[1]
    ax.scatter(x, res.residuals, s=4, alpha=0.35, color=DOT, linewidths=0)
    ax.axhline(0, color=LINE, lw=1.2)
    _style(ax, "Residuals vs market return", "S&P 500 log return", "Residual")

    ax = axes[2]
    ax.hist(res.residuals, bins=bins, color=DOT, alpha=0.8, density=True, label="Residuals")
    grid = np.linspace(res.residuals.min(), res.residuals.max(), 400)
    ax.plot(grid, stats.norm.pdf(grid, 0, res.std_error), color=LINE, lw=1.6,
            label="Normal, same σ")
    ax.legend(frameon=False)
    _style(ax, "Residual distribution", "Residual", "Density")

    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


def beta_comparison(summary, out: Path) -> Path:
    """Bar chart of beta with 95% confidence intervals for every stock."""
    s = summary.sort_values("beta")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    err = np.vstack([s["beta"] - s["beta_ci_low"], s["beta_ci_high"] - s["beta"]])
    ax.barh(s["name"], s["beta"], xerr=err, color=DOT, alpha=0.85, capsize=4)
    ax.axvline(1, color=LINE, lw=1.2, ls="--", label="β = 1 (moves with market)")
    for i, (b, hi) in enumerate(zip(s["beta"], s["beta_ci_high"])):
        ax.text(hi + 0.03, i, f"{b:.2f}", va="center", fontsize=9)
    ax.set_xlim(0, s["beta_ci_high"].max() + 0.2)
    ax.legend(frameon=False, loc="lower right")
    _style(ax, "Market beta vs S&P 500 (95% CI)", "β", "")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out
