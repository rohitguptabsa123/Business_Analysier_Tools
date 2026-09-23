"""Headless smoke test - exercises every module without launching the GUI.

Run:  py smoke_test.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")  # no display needed
from matplotlib.figure import Figure

import pandas as pd
from dataflow import analysis, data_loader, charts, exporter

SAMPLE = os.path.join(os.path.dirname(__file__),
                      "sample_data", "sample_sales.csv")

df = data_loader.load_file(SAMPLE)
print("Loaded:", len(df), "rows x", len(df.columns), "cols")
print("Columns:", list(df.columns))

# Filter
f = analysis.filter_data(df, "region", "==", "North")
print("Filter North rows:", len(f))

# Pivot
pv = analysis.pivot_table(df, "category", "region", "revenue", "sum")
print("Pivot rows:", len(pv))

# Describe
desc = analysis.describe(df)
print("Describe rows:", len(desc))

# Correlation
corr = analysis.correlation(df)
print("Correlation shape:", corr.shape)

# Regression
res = analysis.linear_regression(df, "units", "revenue")
print("Regression R^2:", round(res["r_squared"], 4))

# K-means
km = analysis.kmeans(df, ["units", "revenue"], k=3)
print("K-means clusters:", sorted(km["cluster"].unique().tolist()))

# Chart
fig = Figure(figsize=(5, 3))
charts.create_chart(fig, "bar", "category", ["revenue"], df.head(20),
                    title="test")
print("Chart drawn OK")

# Export Excel + PDF
d = tempfile.mkdtemp()
xp = os.path.join(d, "out.xlsx")
exporter.export_excel(df.head(10), xp)
print("Excel export OK:", os.path.getsize(xp), "bytes")

pp = os.path.join(d, "out.pdf")
exporter.export_pdf(df.head(10), pp, figures=[fig], summary=desc)
print("PDF export OK:", os.path.getsize(pp), "bytes")

print("ALL SMOKE TESTS PASSED")
