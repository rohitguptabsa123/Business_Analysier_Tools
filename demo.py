"""End-to-end demo of DataFlow Analyzer (headless, no GUI).

Loads the sample dataset, runs every analysis feature, generates all three
chart types as PNG images, and exports Excel + PDF reports.  Prints a full
narrative report so the output is self-documenting.

Run:  py demo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure

import pandas as pd
from dataflow import analysis, data_loader, charts, exporter

SAMPLE = os.path.join(os.path.dirname(__file__),
                      "sample_data", "sample_sales.csv")
OUT = os.path.join(os.path.dirname(__file__), "demo_output")
os.makedirs(OUT, exist_ok=True)

SEP = "=" * 70


def banner(title):
    print(f"\n{SEP}\n  {title}\n{SEP}")


# 1. LOAD DATA
banner("STEP 1: Loading sample data")
df = data_loader.load_file(SAMPLE)
print(f"  File:      {os.path.basename(SAMPLE)}")
print(f"  Rows:      {len(df):,}")
print(f"  Columns:   {len(df.columns)}")
print(f"  Schema:    {list(df.columns)}")
print(f"\n  First 5 rows:")
print(df.head().to_string(index=False))

# 2. FILTER
banner("STEP 2: Filtering  (region == 'North')")
north = analysis.filter_data(df, "region", "==", "North")
print(f"  Matched rows: {len(north):,}  (out of {len(df):,})")
print(f"\n  North sales by category:")
print(north.groupby("category")["revenue"].sum().to_string())

banner("STEP 2b: Filtering  (revenue > 10000)")
big = analysis.filter_data(df, "revenue", ">", "10000")
print(f"  High-value orders: {len(big):,}")
print(f"  Max revenue: ${big['revenue'].max():,.2f}")

# 3. PIVOT TABLE
banner("STEP 3: Pivot table  (rows=category, cols=region, values=revenue, sum)")
pv = analysis.pivot_table(df, "category", "region", "revenue", "sum")
print(pv.to_string(index=False))

# 4. DESCRIPTIVE STATISTICS
banner("STEP 4: Descriptive statistics")
desc = analysis.describe(df)
key_cols = ["column", "count", "mean", "std", "min", "max"]
available = [c for c in key_cols if c in desc.columns]
print(desc[available].to_string(index=False))

# 5. CORRELATION MATRIX
banner("STEP 5: Correlation matrix (numeric columns)")
corr = analysis.correlation(df)
print(corr.round(4).to_string())

# 6. LINEAR REGRESSION
banner("STEP 6: Linear regression  (units -> revenue)")
reg = analysis.linear_regression(df, "units", "revenue")
print(f"  Slope:     {reg['slope']:.4f}")
print(f"  Intercept: {reg['intercept']:.4f}")
print(f"  R-squared: {reg['r_squared']:.4f}")
print(f"  Interpretation: each additional unit adds ~${reg['slope']:.2f}"
      f" in revenue")

# 7. K-MEANS CLUSTERING
banner("STEP 7: K-means clustering  (k=3, on units & revenue)")
km = analysis.kmeans(df, ["units", "revenue"], k=3)
print(f"  Cluster sizes:")
print(km.groupby("cluster").size().to_string())
print(f"\n  Cluster centroids (mean units, mean revenue):")
print(km.groupby("cluster")[["units", "revenue"]].mean().round(2)
      .to_string())

# 8. CHARTS (all 3 types -> PNG)
banner("STEP 8: Generating charts (bar, line, scatter)")

agg = df.groupby("category")["revenue"].sum().reset_index()

# Bar chart
fig_bar = Figure(figsize=(8, 5), dpi=120)
charts.create_chart(fig_bar, "bar", "category", ["revenue"], agg,
                    title="Total Revenue by Category (Bar)")
bar_path = os.path.join(OUT, "chart_bar.png")
fig_bar.savefig(bar_path, bbox_inches="tight")
print(f"  Bar chart  -> {bar_path}  ({os.path.getsize(bar_path):,} bytes)")

# Line chart - revenue trend by order_id (first 100 orders)
trend = df.head(100)
fig_line = Figure(figsize=(8, 5), dpi=120)
charts.create_chart(fig_line, "line", "order_id", ["revenue"], trend,
                    title="Revenue Trend - First 100 Orders (Line)")
line_path = os.path.join(OUT, "chart_line.png")
fig_line.savefig(line_path, bbox_inches="tight")
print(f"  Line chart -> {line_path}  ({os.path.getsize(line_path):,} bytes)")

# Scatter chart - units vs revenue
fig_scatter = Figure(figsize=(8, 5), dpi=120)
charts.create_chart(fig_scatter, "scatter", "units", ["revenue"], df,
                    title="Units vs Revenue (Scatter)")
scatter_path = os.path.join(OUT, "chart_scatter.png")
fig_scatter.savefig(scatter_path, bbox_inches="tight")
print(f"  Scatter    -> {scatter_path}  "
      f"({os.path.getsize(scatter_path):,} bytes)")

# 9. EXPORT (Excel + PDF)
banner("STEP 9: Exporting reports")

xlsx_path = os.path.join(OUT, "report.xlsx")
exporter.export_excel(df, xlsx_path)
print(f"  Excel -> {xlsx_path}  ({os.path.getsize(xlsx_path):,} bytes)")
print(f"           (formatted header, frozen panes, auto-filter)")

pdf_path = os.path.join(OUT, "report.pdf")
exporter.export_pdf(df, pdf_path,
                    figures=[fig_bar, fig_line, fig_scatter],
                    summary=desc,
                    title="DataFlow Analyzer - Demo Report")
print(f"  PDF   -> {pdf_path}  ({os.path.getsize(pdf_path):,} bytes)")
print(f"           (title, summary stats, data preview, 3 charts)")

# DONE
banner("DEMO COMPLETE")
print(f"  All output files saved to:  {OUT}")
print(f"  Files generated:")
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    print(f"    {f:25s}  {os.path.getsize(p):>10,} bytes")
print()


