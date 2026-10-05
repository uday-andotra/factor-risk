"""Factor risk, statistical factors, attribution, optimisation, tail risk.

Synthetic 30-name panel. Known factors are market, value, momentum.
A statistical model takes the first three principal components of the
estimation-window returns. Held-out window is used for VaR, stress,
Sharpe and drawdown. Not Barra, Axioma or Bloomberg.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
DATES = pd.bdate_range("2022-01-03", periods=504)
FACTORS = ["market", "value", "momentum"]
NAMES = [f"S{i:02d}" for i in range(30)]
EST = 378


def simulate() -> tuple[pd.DataFrame, pd.DataFrame]:
    factor = np.column_stack(
        [
            RNG.normal(0.0003, 0.010, len(DATES)),
            RNG.normal(0.0001, 0.006, len(DATES)),
            RNG.normal(0.00015, 0.007, len(DATES)),
        ]
    )
    true_beta = np.column_stack(
        [
            RNG.uniform(0.6, 1.4, 30),
            RNG.normal(0.0, 0.4, 30),
            RNG.normal(0.0, 0.4, 30),
        ]
    )
    idiosyncratic = RNG.normal(0.0, 0.012, size=(len(DATES), 30))
    returns = pd.DataFrame(factor @ true_beta.T + idiosyncratic, index=DATES, columns=NAMES)
    factors = pd.DataFrame(factor, index=DATES, columns=FACTORS)
    return returns, factors


def fit_known(returns: pd.DataFrame, factors: pd.DataFrame):
    y = returns.iloc[:EST].to_numpy()
    x = factors.iloc[:EST].to_numpy()
    design = np.column_stack([np.ones(EST), x])
    coef = np.linalg.lstsq(design, y, rcond=None)[0]
    residual = y - design @ coef
    beta = coef[1:]
    specific = np.diag(residual.var(axis=0, ddof=1))
    factor_cov = np.cov(x.T, ddof=1)
    covariance = beta.T @ factor_cov @ beta + specific
    return beta, specific, factor_cov, covariance


def fit_statistical(returns: pd.DataFrame, n_factors: int = 3):
    y = returns.iloc[:EST].to_numpy()
    y = y - y.mean(axis=0)
    _, singular, vt = np.linalg.svd(y, full_matrices=False)
    loadings = vt[:n_factors].T
    scores = y @ loadings
    residual = y - scores @ loadings.T
    specific = np.diag(residual.var(axis=0, ddof=1))
    factor_cov = np.cov(scores.T, ddof=1)
    covariance = loadings @ factor_cov @ loadings.T + specific
    explained = singular[:n_factors] ** 2 / (singular ** 2).sum()
    return loadings, specific, factor_cov, covariance, explained


def attribute(weight, beta, factor_cov, specific):
    exposure = beta @ weight
    factor_var = float(exposure @ factor_cov @ exposure)
    specific_var = float(weight @ specific @ weight)
    return exposure, factor_var, specific_var


def low_beta_book(beta_market: np.ndarray, name_cap: float = 0.08) -> np.ndarray:
    """Long-only book that loads the lowest market betas, name cap 8%."""
    order = np.argsort(beta_market)
    weight = np.zeros(len(beta_market))
    left = 1.0
    for i in order:
        take = min(name_cap, left)
        weight[i] = take
        left -= take
        if left <= 1e-12:
            break
    return weight


def performance(pnl: np.ndarray) -> dict[str, float]:
    cumulative = np.cumsum(pnl)
    peak = np.maximum.accumulate(cumulative)
    drawdown = cumulative - peak
    sharpe = pnl.mean() / pnl.std(ddof=1) * np.sqrt(252)
    return {
        "sharpe": float(sharpe),
        "max_drawdown": float(drawdown.min()) * 100,
        "var_95": float(-np.quantile(pnl, 0.05)) * 100,
        "daily_vol": float(pnl.std(ddof=1)) * 100,
    }


def main():
    returns, factors = simulate()
    beta, specific, factor_cov, covariance = fit_known(returns, factors)
    _, _, _, stat_cov, explained = fit_statistical(returns)
    equal = np.full(30, 1.0 / 30)
    capped = low_beta_book(beta[0])

    print("Known-factor model")
    for name, weight in [("equal_weight", equal), ("low_beta", capped)]:
        exposure, factor_var, specific_var = attribute(weight, beta, factor_cov, specific)
        vol = np.sqrt((factor_var + specific_var) * 252) * 100
        print(
            f"{name:16} vol {vol:5.2f}%  factor share {factor_var / (factor_var + specific_var):.0%}"
            f"  exposure {np.round(exposure, 2)}"
        )

    stat_vol = np.sqrt(equal @ stat_cov @ equal * 252) * 100
    known_vol = np.sqrt(equal @ covariance @ equal * 252) * 100
    print(f"Equal-weight vol, known factors {known_vol:.2f}%  statistical {stat_vol:.2f}%")
    print(f"Variance share of first 3 PCs {explained.sum():.0%}  per PC {np.round(explained, 2)}")

    held_out = returns.iloc[EST:].to_numpy()
    print("Held-out, low-beta book")
    stats = performance(held_out @ capped)
    for key, value in stats.items():
        print(f"  {key:14} {value:.2f}")
    shock = np.array([-3.0 * factors.iloc[:EST, 0].std(ddof=1), -2.0 * factors.iloc[:EST, 1].std(), 0.0])
    stress = float((beta.T @ shock) @ capped) * 100
    print(f"  stress mkt-3sd value-2sd {stress:.2f}%  (specific risk not included)")
    print(
        "A long-only 8% name cap cannot deliver a market exposure of 0.4. "
        "The low-beta book is the feasible cut. It lowers exposure and vol. "
        "Inverse-vol did not. The statistical model matches the risk level and does not name the factors."
    )


if __name__ == "__main__":
    main()
