"""
optimizer.py
Find the optimal portfolio that maximises investor utility:
    U = w^T mu - (A/2) * w^T Sigma w
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.risk_assessment import calculate_utility


def find_optimal_portfolio(
    mu: np.ndarray,
    Sigma: np.ndarray,
    A: float,
    allow_short: bool,
    fund_names: list[str] = None,
    rf: float = 0.0,
) -> dict:
    """
    Maximise U = w^T mu - (A/2) * w^T Sigma w  subject to sum(w) = 1.
    Bounds: (0, 1) per asset if allow_short=False.

    Returns dict:
        weights    : np.ndarray
        return     : float (annualised)
        volatility : float (annualised)
        utility    : float
        sharpe     : float, computed using excess return over rf
        allocation : pd.DataFrame with Fund / Weight columns
    """
    n = len(mu)
    w0 = np.ones(n) / n

    def neg_utility(w):
        ret = float(w @ mu)
        var = float(w @ Sigma @ w)
        return -(ret - (A / 2) * var)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    bounds = [(0.0, 1.0)] * n if not allow_short else None

    result = minimize(
        neg_utility,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 2000},
    )

    w = result.x
    # Clean up tiny weights
    w = np.clip(w, 0 if not allow_short else -np.inf, np.inf)
    if not allow_short:
        w = np.where(w < 1e-6, 0.0, w)
        total = w.sum()
        if total > 0:
            w = w / total

    ret = float(w @ mu)
    var = float(w @ Sigma @ w)
    vol = np.sqrt(var)
    utility = calculate_utility(ret, var, A)
    sharpe = (ret - rf) / vol if vol > 1e-10 else 0.0

    allocation = _format_allocation(w, fund_names or [f"Fund {i+1}" for i in range(n)])

    return {
        "weights": w,
        "return": ret,
        "volatility": vol,
        "utility": utility,
        "sharpe": sharpe,
        "allocation": allocation,
        "success": result.success,
    }


def _format_allocation(weights: np.ndarray, names: list[str]) -> pd.DataFrame:
    """Return a tidy allocation DataFrame sorted descending, filtering near-zero."""
    df = pd.DataFrame({"Fund": names, "Weight": weights})
    df = df[df["Weight"].abs() > 0.005].copy()
    df["Weight (%)"] = (df["Weight"] * 100).round(2)
    df = df.sort_values("Weight", ascending=False).reset_index(drop=True)
    return df[["Fund", "Weight", "Weight (%)"]]


def sensitivity_analysis(
    mu: np.ndarray,
    Sigma: np.ndarray,
    A_center: float,
    allow_short: bool,
    fund_names: list[str] = None,
    n_steps: int = 9,
    delta: float = 3.0,
    rf: float = 0.0,
) -> pd.DataFrame:
    """
    Compute optimal portfolios across a range of A values centred on A_center.
    Returns a DataFrame with rows = A values and columns = fund allocations (%).
    """
    names = fund_names or [f"Fund {i+1}" for i in range(len(mu))]
    A_values = np.linspace(max(1.0, A_center - delta), min(8.0, A_center + delta), n_steps)
    rows = []
    for A in A_values:
        result = find_optimal_portfolio(mu, Sigma, A, allow_short, names, rf=rf)
        row = {"A": round(A, 2)}
        for name, w in zip(names, result["weights"]):
            row[name] = round(w * 100, 1)
        rows.append(row)
    return pd.DataFrame(rows)
