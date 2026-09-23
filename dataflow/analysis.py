"""Analysis module - filtering, pivot tables, statistics and ML routines.

All functions are pure (no GUI / no I/O) which makes them trivial to unit
test.  They operate on :class:`pandas.DataFrame` objects and return either a
DataFrame or a small result dict.

The machine-learning routines (linear regression, k-means) are implemented
with NumPy only so the application has no hard dependency on scikit-learn.
This keeps the install light while still covering the "common statistical or
machine-learning routines" requirement from the project brief.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
def filter_data(df: pd.DataFrame, column: str, op: str, value: str
                ) -> pd.DataFrame:
    """Return rows of *df* where *column* satisfies *op value*.

    Supported operators: ``== != > >= < <= contains``.

    The *value* string is coerced to the column dtype so numeric comparisons
    work naturally.  ``contains`` performs a substring match (case-insensitive)
    and is only valid on text columns.
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found")

    series = df[column]
    op = op.strip().lower()

    if op == "contains":
        mask = series.astype(str).str.contains(str(value), case=False, na=False)
        return df[mask]

    # Coerce the comparison value to match the column's dtype.
    try:
        typed = (series.dtype.type(value)
                 if not pd.api.types.is_object_dtype(series) else value)
    except (TypeError, ValueError):
        typed = value

    if op == "==":
        mask = series == typed
    elif op == "!=":
        mask = series != typed
    elif op == ">":
        mask = series > typed
    elif op == ">=":
        mask = series >= typed
    elif op == "<":
        mask = series < typed
    elif op == "<=":
        mask = series <= typed
    else:
        raise ValueError(f"Unsupported operator '{op}'")

    return df[mask]


# ---------------------------------------------------------------------------
# Pivot tables
# ---------------------------------------------------------------------------
def pivot_table(df: pd.DataFrame, index: str, columns: Optional[str],
                values: str, aggfunc: str = "mean") -> pd.DataFrame:
    """Build a pivot-style summary.

    Parameters mirror :func:`pandas.pivot_table`.  *aggfunc* accepts the usual
    names: ``sum mean count min max median std``.
    """
    if index not in df.columns or values not in df.columns:
        raise KeyError("index and values columns must exist in the DataFrame")
    if columns is not None and columns not in df.columns:
        raise KeyError(f"columns '{columns}' not found")

    return pd.pivot_table(
        df, index=index, columns=columns, values=values, aggfunc=aggfunc,
    ).reset_index()


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------
def describe(df: pd.DataFrame) -> pd.DataFrame:
    """Return the pandas ``describe()`` summary for all columns."""
    return df.describe(include="all").T.reset_index().rename(
        columns={"index": "column"})


def correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Return the Pearson correlation matrix for numeric columns."""
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return pd.DataFrame()
    return numeric.corr()


# ---------------------------------------------------------------------------
# Machine-learning routines (NumPy-only implementations)
# ---------------------------------------------------------------------------
def linear_regression(df: pd.DataFrame, x_col: str, y_col: str) -> dict:
    """Ordinary least-squares linear regression of *y_col* on *x_col*.

    Returns a dict with ``slope``, ``intercept``, ``r_squared`` and
    ``predictions`` (a NumPy array of fitted y values).
    """
    sub = df[[x_col, y_col]].dropna()
    if len(sub) < 2:
        raise ValueError("Need at least 2 non-null rows for regression")

    x = sub[x_col].to_numpy(dtype=float)
    y = sub[y_col].to_numpy(dtype=float)

    # Closed-form least squares via NumPy polyfit (degree 1).
    slope, intercept = np.polyfit(x, y, 1)
    predictions = slope * x + intercept

    # Coefficient of determination R^2.
    ss_res = float(np.sum((y - predictions) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "predictions": predictions,
    }


def kmeans(df: pd.DataFrame, columns: List[str], k: int = 3,
          max_iter: int = 100, seed: int = 42) -> pd.DataFrame:
    """Lloyd's k-means clustering implemented with NumPy.

    Adds a ``cluster`` column to a copy of *df* (restricted to *columns*) and
    returns it.  No scikit-learn dependency required.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    sub = df[columns].dropna()
    if len(sub) < k:
        raise ValueError(f"Need at least {k} rows, got {len(sub)}")

    data = sub.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)

    # Initialise centroids by picking k distinct random points.
    idx = rng.choice(len(data), size=k, replace=False)
    centroids = data[idx].copy()

    labels = np.zeros(len(data), dtype=int)
    for _ in range(max_iter):
        # Assign each point to the nearest centroid (Euclidean distance).
        dists = np.linalg.norm(
            data[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = dists.argmin(axis=1)

        # Recompute centroids as the mean of assigned points.
        for c in range(k):
            members = data[new_labels == c]
            if len(members):
                centroids[c] = members.mean(axis=0)

        if np.array_equal(new_labels, labels):
            break  # converged
        labels = new_labels

    result = sub.copy()
    result["cluster"] = labels
    return result

