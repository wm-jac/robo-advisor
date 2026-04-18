"""
portfolio.py
Efficient frontier computation (with and without short sales) and GMVP.
"""

import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize


def _portfolio_variance(w: np.ndarray, Sigma: np.ndarray) -> float:
    return float(w @ Sigma @ w)


def _portfolio_return(w: np.ndarray, mu: np.ndarray) -> float:
    return float(w @ mu)


def compute_gmvp(
    mu: np.ndarray,
    Sigma: np.ndarray,
    allow_short: bool,
) -> dict:
    """
    Find the Global Minimum Variance Portfolio.

    allow_short=True  -> closed-form analytic solution
    allow_short=False -> numerical optimisation with long-only bounds

    Returns dict with keys: weights, return, volatility
    """
    n = len(mu)

    if allow_short:
        # Closed-form: w = (Sigma^{-1} @ 1) / (1^T @ Sigma^{-1} @ 1)
        ones = np.ones(n)
        inv_Sigma_ones = np.linalg.solve(Sigma, ones)
        w = inv_Sigma_ones / (ones @ inv_Sigma_ones)
    else:
        w0 = np.ones(n) / n
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0.0, 1.0)] * n
        result = minimize(
            _portfolio_variance,
            w0,
            args=(Sigma,),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        w = result.x

    ret = _portfolio_return(w, mu)
    vol = np.sqrt(_portfolio_variance(w, Sigma))
    return {"weights": w, "return": ret, "volatility": vol}


def compute_efficient_frontier(
    mu: np.ndarray,
    Sigma: np.ndarray,
    allow_short: bool,
    n_points: int = 200,
    target_return_min: float | None = None,
    target_return_max: float | None = None,
) -> pd.DataFrame:
    """
    Trace the efficient frontier by sweeping target returns and minimising variance.

    For allow_short=True : sweeps from min(mu) to max(mu) — returns full parabola
    For allow_short=False: sweeps from GMVP return to max(mu) — returns efficient branch only

    Returns DataFrame with columns: return, volatility, weights
    where weights is a list (stored as JSON string for caching compatibility).
    """
    n = len(mu)
    gmvp = compute_gmvp(mu, Sigma, allow_short)

    r_min = gmvp["return"]
    r_max = float(np.max(mu))

    if allow_short:
        # Include the lower (inefficient) branch for the full parabola
        r_min = float(np.min(mu))

    if target_return_min is not None:
        r_min = min(r_min, float(target_return_min))
    if target_return_max is not None:
        r_max = max(r_max, float(target_return_max))

    if r_max - r_min < 1e-8:
        # All funds have identical returns — degenerate case
        return pd.DataFrame({
            "return": [gmvp["return"]],
            "volatility": [gmvp["volatility"]],
            "weights": [json.dumps(gmvp["weights"].tolist())],
        })

    target_returns = np.linspace(r_min, r_max, n_points)

    rows = []
    w0 = np.ones(n) / n

    for r_target in target_returns:
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, r=r_target: w @ mu - r},
        ]
        bounds = [(0.0, 1.0)] * n if not allow_short else [(None, None)] * n

        result = minimize(
            _portfolio_variance,
            w0,
            args=(Sigma,),
            method="SLSQP",
            bounds=bounds if not allow_short else None,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )

        if result.success:
            w = result.x
            vol = np.sqrt(_portfolio_variance(w, Sigma))
            rows.append({
                "return": r_target,
                "volatility": vol,
                "weights": json.dumps(w.tolist()),
            })
            w0 = result.x  # warm start

    if not rows:
        return pd.DataFrame(columns=["return", "volatility", "weights"])

    return pd.DataFrame(rows)


def portfolio_stats(
    weights: np.ndarray,
    mu: np.ndarray,
    Sigma: np.ndarray,
    rf: float = 0.0,
) -> dict:
    """Compute annualised return, volatility, and Sharpe ratio for given weights."""
    ret = float(weights @ mu)
    vol = float(np.sqrt(weights @ Sigma @ weights))
    sharpe = (ret - rf) / vol if vol > 1e-10 else 0.0
    return {"return": ret, "volatility": vol, "sharpe": sharpe}
