"""Chart rendering module.

Wraps matplotlib so the GUI never touches matplotlib directly.  Each public
function draws onto a caller-supplied :class:`matplotlib.figure.Figure`, which
keeps the chart lifecycle (create / clear / redraw) in one place.

Three chart types are supported - bar, line and scatter - satisfying the
"at least three chart types" acceptance criterion from the project brief.
"""

from __future__ import annotations

from typing import List, Optional

import matplotlib
# Use the Agg-free backend that integrates with Tkinter.
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt  # noqa: E402  (after backend selection)
from matplotlib.figure import Figure  # noqa: E402

# Colour palette for multi-series charts - pleasant and colour-blind friendly.
PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
           "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]


def create_chart(figure: Figure, chart_type: str, x_col: str,
                 y_cols: List[str], data, title: str = "",
                 color: Optional[str] = None) -> None:
    """Draw *chart_type* onto *figure*.

    Parameters
    ----------
    figure:
        A matplotlib Figure (usually the one embedded in the Tkinter canvas).
    chart_type:
        One of ``bar``, ``line``, ``scatter``.
    x_col:
        Column name for the X axis.
    y_cols:
        List of column names for the Y axis (one series each).
    data:
        pandas DataFrame containing the columns.
    title:
        Optional chart title.
    color:
        Optional override colour for the first series.
    """
    figure.clear()
    ax = figure.add_subplot(111)

    if x_col not in data.columns:
        ax.text(0.5, 0.5, f"Column '{x_col}' not found",
                ha="center", va="center", transform=ax.transAxes)
        return

    x = data[x_col]

    for i, col in enumerate(y_cols):
        if col not in data.columns:
            continue
        y = data[col]
        c = color or PALETTE[i % len(PALETTE)]
        _draw_series(ax, chart_type, x, y, col, c)

    ax.set_title(title or f"{chart_type.capitalize()} chart")
    ax.set_xlabel(x_col)
    ax.set_ylabel(", ".join(y_cols) if len(y_cols) > 1 else y_cols[0])
    if len(y_cols) > 1:
        ax.legend(loc="best")
    figure.tight_layout()


def _draw_series(ax, chart_type: str, x, y, label: str, color: str) -> None:
    """Dispatch a single series to the correct matplotlib plotter."""
    if chart_type == "bar":
        ax.bar(x, y, label=label, color=color, alpha=0.85)
    elif chart_type == "line":
        ax.plot(x, y, label=label, color=color, marker="o", markersize=3,
                linewidth=1.5)
    elif chart_type == "scatter":
        ax.scatter(x, y, label=label, color=color, alpha=0.6, s=20)
    else:
        raise ValueError(
            f"Unknown chart type '{chart_type}'. Use bar, line or scatter.")
