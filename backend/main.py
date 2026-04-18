"""
backend/main.py — FastAPI backend for the Robo-Advisor
Run with: uvicorn backend.main:app --reload --port 8000
"""

import io
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Make src/ importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import (
    annualise_stats,
    compute_returns,
    individual_fund_stats,
    load_all_funds,
    normalise_prices,
)
from src.optimizer import find_optimal_portfolio, sensitivity_analysis
from src.portfolio import compute_efficient_frontier, compute_gmvp
from src.risk_assessment import (
    QUESTIONS,
    describe_profile,
    get_score_range,
    score_to_A,
)
from src.risk_free_rate import (
    MAS_ONE_YEAR_TBILL_URL,
    fetch_latest_one_year_tbill_rate,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_RISK_FREE_CACHE_TTL = timedelta(hours=6)
_RISK_FREE_FALLBACK_TTL = timedelta(minutes=5)
_risk_free_cache: dict[str, object] | None = None
_risk_free_cache_at: datetime | None = None

app = FastAPI(title="Robo-Advisor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _humanise(name: str) -> str:
    label = Path(str(name)).stem
    parts = label.split("_", 1)
    if len(parts) == 2 and any(c.isdigit() for c in parts[0]):
        label = parts[1]
    return " ".join(label.replace("_", " ").replace("-", " ").split())


def _nan_safe(v):
    """Convert numpy scalar to Python float, replacing NaN with None."""
    if v is None:
        return None
    f = float(v)
    return None if (f != f) else f  # NaN check


def _risk_free_rate_payload() -> dict[str, object]:
    """Return the cached MAS 1-year T-bill rate, falling back to 0 if unavailable."""
    global _risk_free_cache, _risk_free_cache_at

    now = datetime.now(timezone.utc)
    if _risk_free_cache is not None and _risk_free_cache_at is not None:
        cache_ttl = (
            _RISK_FREE_FALLBACK_TTL
            if _risk_free_cache.get("fallback")
            else _RISK_FREE_CACHE_TTL
        )
        if now - _risk_free_cache_at < cache_ttl:
            return _risk_free_cache

    try:
        risk_free = fetch_latest_one_year_tbill_rate(timeout=5)
        payload: dict[str, object] = {
            "rate": _nan_safe(risk_free.rate),
            "yield_percent": _nan_safe(risk_free.yield_percent),
            "as_of": risk_free.as_of.isoformat(),
            "issue_code": risk_free.issue_code,
            "source_url": risk_free.source_url,
            "fallback": False,
            "error": None,
        }
    except Exception as e:
        payload = {
            "rate": 0.0,
            "yield_percent": 0.0,
            "as_of": None,
            "issue_code": None,
            "source_url": MAS_ONE_YEAR_TBILL_URL,
            "fallback": True,
            "error": str(e),
        }

    _risk_free_cache = payload
    _risk_free_cache_at = now
    return payload


# ── models ────────────────────────────────────────────────────────────────────

class FrontierRequest(BaseModel):
    mu: list[float]
    sigma: list[list[float]]
    allow_short: bool = False


class ProfileRequest(BaseModel):
    total_score: int


class OptimalRequest(BaseModel):
    mu: list[float]
    sigma: list[list[float]]
    A: float
    allow_short: bool = False
    fund_names: list[str] = []


# ── routes ────────────────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze_funds(
    files: list[UploadFile] = File(default=[]),
    freq: str = Form(default="Daily"),
):
    try:
        if files and files[0].filename:
            file_objs, file_names = [], []
            for f in files:
                content = await f.read()
                buf = io.BytesIO(content)
                buf.name = f.filename
                file_objs.append(buf)
                file_names.append(_humanise(f.filename))
            is_default = False
        else:
            paths = sorted(p for p in DATA_DIR.glob("*.csv") if p.is_file())
            if not paths:
                return JSONResponse({"error": "No data files found"}, status_code=400)
            file_objs = [open(p, "rb") for p in paths]
            file_names = [_humanise(p.stem) for p in paths]
            is_default = True

        prices = load_all_funds(file_objs, file_names)
        returns = compute_returns(prices, method="log")
        mu, Sigma = annualise_stats(returns, freq=freq)
        stats_df = individual_fund_stats(mu, Sigma)
        norm = normalise_prices(prices)
        corr = returns.corr()
        risk_free_rate = _risk_free_rate_payload()
        rf = float(risk_free_rate["rate"])

        price_data = {
            col: {
                "dates": norm.index.strftime("%Y-%m-%d").tolist(),
                "values": [_nan_safe(v) for v in norm[col].tolist()],
            }
            for col in norm.columns
        }

        stats_out = []
        for fund in stats_df.index:
            ret = _nan_safe(stats_df.loc[fund, "Return"])
            vol = _nan_safe(stats_df.loc[fund, "Volatility"])
            sharpe = (
                _nan_safe((ret - rf) / vol)
                if (ret is not None and vol and vol > 0)
                else None
            )
            stats_out.append({
                "fund": fund,
                "return": ret,
                "volatility": vol,
                "sharpe": sharpe,
            })

        return {
            "funds": mu.index.tolist(),
            "mu": [_nan_safe(v) for v in mu.tolist()],
            "sigma": [[_nan_safe(v) for v in row] for row in Sigma.values.tolist()],
            "prices": price_data,
            "stats": stats_out,
            "corr": {
                "funds": corr.columns.tolist(),
                "values": [[_nan_safe(v) for v in row] for row in corr.values.tolist()],
            },
            "date_range": {
                "start": prices.index[0].strftime("%Y-%m-%d"),
                "end": prices.index[-1].strftime("%Y-%m-%d"),
                "observations": len(prices),
            },
            "is_default": is_default,
            "risk_free_rate": risk_free_rate,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/frontier")
def frontier(body: FrontierRequest):
    try:
        mu = np.array(body.mu)
        Sigma = np.array(body.sigma)
        allow_short = body.allow_short

        frontier_df = compute_efficient_frontier(mu, Sigma, allow_short)
        gmvp = compute_gmvp(mu, Sigma, allow_short)

        return {
            "frontier": [
                {"return": _nan_safe(r["return"]), "volatility": _nan_safe(r["volatility"])}
                for r in frontier_df[["return", "volatility"]].to_dict(orient="records")
            ],
            "gmvp": {
                "return": _nan_safe(gmvp["return"]),
                "volatility": _nan_safe(gmvp["volatility"]),
                "weights": [_nan_safe(w) for w in gmvp["weights"].tolist()],
            },
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/questions")
def questions():
    min_s, max_s = get_score_range()
    return {"questions": QUESTIONS, "min_score": min_s, "max_score": max_s}


@app.post("/api/profile")
def profile(body: ProfileRequest):
    A = score_to_A(body.total_score)
    p = describe_profile(A)
    return {"A": A, "profile": p}


@app.post("/api/optimal")
def optimal(body: OptimalRequest):
    try:
        mu = np.array(body.mu)
        Sigma = np.array(body.sigma)
        names = body.fund_names or [f"Fund {i+1}" for i in range(len(mu))]
        risk_free_rate = _risk_free_rate_payload()
        rf = float(risk_free_rate["rate"])

        result = find_optimal_portfolio(
            mu,
            Sigma,
            body.A,
            body.allow_short,
            names,
            rf=rf,
        )
        sens_df = sensitivity_analysis(mu, Sigma, body.A, body.allow_short, names, rf=rf)

        allocation = [
            {
                "fund": row["Fund"],
                "weight": _nan_safe(row["Weight"]),
                "weight_pct": _nan_safe(row["Weight (%)"]),
            }
            for row in result["allocation"].to_dict(orient="records")
        ]

        sensitivity = sens_df.to_dict(orient="records")

        return {
            "return": _nan_safe(result["return"]),
            "volatility": _nan_safe(result["volatility"]),
            "utility": _nan_safe(result["utility"]),
            "sharpe": _nan_safe(result["sharpe"]),
            "success": result["success"],
            "allocation": allocation,
            "sensitivity": sensitivity,
            "risk_free_rate": risk_free_rate,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
