"""Command-line entry point: ``python -m capm_beta``."""

from __future__ import annotations

import argparse
from pathlib import Path

from .report import write_report

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Estimate CAPM betas of stocks against the S&P 500 and test hypotheses."
    )
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "prices.csv",
                        help="CSV with a 'date' column and one closing-price column per ticker")
    parser.add_argument("--out", type=Path, default=ROOT / "results",
                        help="Output folder for tables, figures and report.md")
    parser.add_argument("--alpha-level", type=float, default=0.05,
                        help="Significance level for the hypothesis tests (default 0.05)")
    args = parser.parse_args(argv)

    summary = write_report(args.data, args.out, args.alpha_level)
    cols = ["ticker", "beta", "beta_ci_low", "beta_ci_high", "alpha", "r_squared"]
    print(summary[cols].to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"\nReport written to {args.out / 'report.md'}")


if __name__ == "__main__":
    main()
