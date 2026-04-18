"""
data_loader.py
Load and preprocess FSMOne fund price CSVs into a unified DataFrame,
then compute returns and annualised statistics.
"""

import io
import numpy as np
import pandas as pd

ANNUALISATION = {"Daily": 252, "Weekly": 52, "Monthly": 12}


def _detect_and_load(file_obj) -> pd.DataFrame:
    """
    Read a FSMOne CSV that may have metadata rows at the top.
    Returns a two-column DataFrame: [Date, Price].
    Handles both file paths (str) and file-like objects (UploadedFile).
    """
    if isinstance(file_obj, (str,)):
        raw = open(file_obj, "rb").read()
    else:
        raw = file_obj.read()
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)

    # Decode, strip BOM
    text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()

    # Find the header row: first row where both a date-like and numeric value appear
    header_idx = 0
    for i, line in enumerate(lines):
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) >= 2:
            try:
                pd.to_datetime(parts[0], dayfirst=True)
                float(parts[1].replace(",", ""))
                header_idx = i
                break
            except (ValueError, TypeError):
                continue

    df = pd.read_csv(
        io.StringIO("\n".join(lines[header_idx:])),
        header=None,
        names=["Date", "Price"],
        usecols=[0, 1],
    )
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["Date", "Price"]).set_index("Date").sort_index()
    return df


def load_fund_csv(file_obj, name: str = None) -> pd.Series:
    """
    Load a single fund CSV.  Returns a named pd.Series of prices indexed by date.
    name: label to give the series (defaults to filename stem if a str path is given).
    """
    df = _detect_and_load(file_obj)
    label = name or (file_obj if isinstance(file_obj, str) else getattr(file_obj, "name", "Fund"))
    # Strip path and extension for display
    if isinstance(label, str):
        import os
        label = os.path.splitext(os.path.basename(label))[0]
    series = df["Price"].rename(label)
    return series


def load_all_funds(file_objs: list, names: list[str] = None) -> pd.DataFrame:
    """
    Load multiple fund CSVs and align them on a common date index (inner join).
    file_objs: list of file paths (str) or file-like objects.
    names: optional list of display names; defaults to filename stems.
    Returns a wide DataFrame: index=Date, columns=fund names.
    Raises ValueError if fewer than 2 funds are loadable.
    """
    if names is None:
        names = [None] * len(file_objs)

    series_list = []
    for fobj, name in zip(file_objs, names):
        try:
            s = load_fund_csv(fobj, name)
            series_list.append(s)
        except Exception as e:
            label = name or getattr(fobj, "name", str(fobj))
            print(f"Warning: could not load {label}: {e}")

    if len(series_list) < 2:
        raise ValueError("At least 2 funds must be loadable.")

    prices = pd.concat(series_list, axis=1).sort_index()
    # Forward-fill gaps (non-trading days), then drop remaining NaNs
    prices = prices.ffill().dropna()
    return prices


def compute_returns(prices: pd.DataFrame, method: str = "log") -> pd.DataFrame:
    """
    Compute per-period returns from a price DataFrame.
    method='log'    -> natural log returns: ln(P_t / P_{t-1})
    method='simple' -> arithmetic returns:  (P_t / P_{t-1}) - 1
    Returns DataFrame of same shape minus the first row.
    """
    if method == "log":
        returns = np.log(prices / prices.shift(1)).dropna()
    else:
        returns = prices.pct_change().dropna()
    return returns


def annualise_stats(
    returns: pd.DataFrame, freq: str = "Daily"
) -> tuple[pd.Series, pd.DataFrame]:
    """
    Convert per-period log returns to annualised mean vector and covariance matrix.
    freq: one of 'Daily', 'Weekly', 'Monthly'.
    Returns (mu: pd.Series, Sigma: pd.DataFrame) both annualised.
    """
    factor = ANNUALISATION.get(freq, 252)
    mu = returns.mean() * factor
    Sigma = returns.cov() * factor

    # Regularise to ensure positive definiteness
    Sigma_arr = Sigma.values + 1e-8 * np.eye(len(Sigma))
    Sigma = pd.DataFrame(Sigma_arr, index=Sigma.index, columns=Sigma.columns)
    return mu, Sigma


def normalise_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Normalise each fund to start at 100 for comparison plotting."""
    return prices / prices.iloc[0] * 100


def individual_fund_stats(mu: pd.Series, Sigma: pd.DataFrame) -> pd.DataFrame:
    """
    Return each fund's standalone annualised return and volatility.
    """
    vols = pd.Series(np.sqrt(np.diag(Sigma.values)), index=mu.index)
    return pd.DataFrame({"Return": mu, "Volatility": vols})
