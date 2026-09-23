"""Report export module - Excel and PDF.

* Excel export uses ``xlsxwriter`` to write a formatted workbook with the data
  table, an auto-filter and frozen header row.
* PDF export uses ``reportlab`` to lay out a title, a summary table and any
  matplotlib figures the user has generated.

Both exporters accept a :class:`pandas.DataFrame` plus optional chart figures
so the exported report matches what the user sees on screen.
"""

from __future__ import annotations

import os
from typing import List, Optional

import pandas as pd
from matplotlib.figure import Figure


def export_excel(df: pd.DataFrame, path: str,
                sheet_name: str = "Data") -> str:
    """Write *df* to *path* as a formatted .xlsx file.

    Returns the absolute path written.  The header row is bold, the first row
    is frozen and an auto-filter is applied so the file is immediately useful
    in Excel.
    """
    # Use xlsxwriter as the engine for formatting support.
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Bold header format.
        header_fmt = workbook.add_format({"bold": True, "bg_color": "#1f77b4",
                                         "font_color": "white", "border": 1})
        for col_idx, col_name in enumerate(df.columns):
            worksheet.write(0, col_idx, col_name, header_fmt)

        # Freeze the header and add an auto-filter across all columns.
        worksheet.freeze_panes(1, 0)
        n_cols = len(df.columns)
        col_letter = _col_letter(n_cols - 1)
        worksheet.autofilter(0, 0, len(df), n_cols - 1)

        # Auto-size columns based on a sample of values.
        for i, col in enumerate(df.columns):
            max_len = max(len(str(col)),
                          int(df[col].astype(str).str.len().quantile(0.95)))
            worksheet.set_column(i, i, min(max_len + 2, 50))

    return os.path.abspath(path)


def export_pdf(df: pd.DataFrame, path: str,
               figures: Optional[List[Figure]] = None,
               summary: Optional[pd.DataFrame] = None,
               title: str = "DataFlow Analyzer Report") -> str:
    """Write a PDF report to *path*.

    The report contains a title, an optional summary table, the first 50 rows
    of *df* and any matplotlib *figures* the user created.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, Image as RLImage)
    from reportlab.lib.units import cm

    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(
        f"{len(df):,} rows x {len(df.columns)} columns", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Optional summary table (e.g. describe() output).
    if summary is not None and not summary.empty:
        story.append(Paragraph("Summary statistics", styles["Heading2"]))
        story.append(_df_to_table(summary.head(20), styles))
        story.append(Spacer(1, 0.5 * cm))

    # Data preview - first 50 rows.
    story.append(Paragraph("Data preview (first 50 rows)", styles["Heading2"]))
    story.append(_df_to_table(df.head(50), styles))
    story.append(Spacer(1, 0.5 * cm))

    # Embedded charts.
    if figures:
        story.append(Paragraph("Charts", styles["Heading2"]))
        for fig in figures:
            tmp = path + ".tmp_chart.png"
            fig.savefig(tmp, dpi=120, bbox_inches="tight")
            story.append(RLImage(tmp, width=16 * cm, height=9 * cm))
            story.append(Spacer(1, 0.3 * cm))

    doc.build(story)

    # Clean up temp chart images.
    if figures:
        for i in range(len(figures)):
            tmp = f"{path}.tmp_chart.png"
            try:
                os.remove(tmp)
            except OSError:
                pass
    return os.path.abspath(path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _df_to_table(df: pd.DataFrame, styles) -> Table:
    """Convert a DataFrame to a reportlab Table with a styled header."""
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    # Truncate long cell text so the table stays readable.
    cols = [str(c) for c in df.columns]
    rows = [[_short(v) for v in row] for row in df.itertuples(index=False,
                                                              name=None)]
    table_data = [cols] + rows

    tbl = Table(table_data, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#eef3f9")]),
    ]))
    return tbl


def _short(value, limit: int = 25) -> str:
    """Truncate a cell value to *limit* characters for PDF display."""
    s = str(value)
    return s if len(s) <= limit else s[: limit - 1] + "\u2026"


def _col_letter(zero_based: int) -> str:
    """Convert a 0-based column index to an Excel column letter (A, B, ...)."""
    result = ""
    n = zero_based + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result
