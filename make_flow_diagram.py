"""Generate a flow diagram for DataFlow Analyzer using matplotlib.

Run:  py make_flow_diagram.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

OUT = os.path.join(os.path.dirname(__file__), "demo_output")
os.makedirs(OUT, exist_ok=True)

C_INPUT = "#4CAF50"
C_PROC = "#2196F3"
C_ANALYSIS = "#9C27B0"
C_CHART = "#FF9800"
C_EXPORT = "#F44336"
C_UI = "#607D8B"
C_TEXT = "white"

fig, ax = plt.subplots(figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis("off")
ax.set_aspect("equal")


def draw_box(x, y, w, h, text, color, fontsize=10, text_color=C_TEXT):
    box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                         boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor="black",
                         linewidth=1.5, mutation_aspect=0.5)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color)


def draw_arrow(x1, y1, x2, y2, color="#333", lw=2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw,
                                connectionstyle="arc3,rad=0"))


def draw_diamond(x, y, w, h, text, color, fontsize=9):
    diamond = plt.Polygon([(x, y + h / 2), (x + w / 2, y),
                          (x, y - h / 2), (x - w / 2, y)],
                         facecolor=color, edgecolor="black", linewidth=1.5)
    ax.add_patch(diamond)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=C_TEXT)


# TITLE
ax.text(10, 13.5, "DataFlow Analyzer - Application Flow Diagram",
        ha="center", va="center", fontsize=20, fontweight="bold")
ax.text(10, 13.0, "Architecture & User Workflow",
        ha="center", va="center", fontsize=12, color="#666")

# LAYER LABELS
layers = [
    (12.2, "DATA\nINPUT"),
    (10.5, "GUI LAYER\n(Tkinter)"),
    (8.5, "DATA\nPROCESSING"),
    (6.5, "ANALYSIS\n& ML"),
    (4.5, "VISUAL\n& EXPORT"),
    (2.5, "OUTPUT\nFILES"),
]
for y, label in layers:
    ax.text(0.5, y, label, ha="center", va="center",
            fontsize=9, fontweight="bold", color="#888", style="italic")
    ax.plot([1.2, 19.5], [y - 0.8, y - 0.8], color="#eee", lw=0.5, zorder=0)

# ROW 1: DATA INPUT (y=12.2)
draw_box(5, 12.2, 3, 0.8, "CSV File\n(.csv, .tsv)", C_INPUT, 9)
draw_box(10, 12.2, 3, 0.8, "Excel File\n(.xlsx, .xls)", C_INPUT, 9)
draw_box(15, 12.2, 3, 0.8, "User Action\n(File > Open / Ctrl+O)", C_UI, 9)
draw_arrow(6.5, 12.2, 8.5, 12.2)
draw_arrow(11.5, 12.2, 13.5, 12.2)

# ROW 2: GUI / LOADER (y=10.5)
draw_box(15, 10.5, 3.5, 0.8, "GUI: app.py\nDataFlowApp (Tkinter)", C_UI, 9)
draw_box(10, 10.5, 3.5, 0.8, "data_loader.py\nload_file_async()", C_PROC, 9)
draw_box(5, 10.5, 3.5, 0.8, "Background Thread\n(non-blocking)", C_PROC, 9)
draw_arrow(15, 11.8, 15, 10.9)
draw_arrow(13.25, 10.5, 11.75, 10.5)
draw_arrow(8.25, 10.5, 6.75, 10.5)

# ROW 3: DATA PROCESSING (y=8.5)
draw_box(5, 8.5, 3.5, 0.8, "pandas DataFrame\n(loaded in memory)", C_PROC, 9)
draw_box(10, 8.5, 3.5, 0.8, "Paginated Table\n(1,000 rows/page)", C_UI, 9)
draw_box(15, 8.5, 3.5, 0.8, "Filter Module\nfilter_data()", C_PROC, 9)
draw_arrow(5, 10.1, 5, 8.9)
draw_arrow(6.75, 8.5, 8.25, 8.5)
draw_arrow(6.75, 8.3, 13.25, 8.3)

# ROW 4: ANALYSIS & ML (y=6.5)
draw_box(3, 6.5, 3, 0.8, "Pivot Table\npivot_table()", C_ANALYSIS, 8)
draw_box(7, 6.5, 3, 0.8, "Statistics\ndescribe()\ncorrelation()", C_ANALYSIS, 8)
draw_box(11, 6.5, 3, 0.8, "Regression\nlinear_regression()\n(NumPy OLS)", C_ANALYSIS, 8)
draw_box(15, 6.5, 3, 0.8, "Clustering\nkmeans()\n(Lloyd's algorithm)", C_ANALYSIS, 8)
draw_arrow(5, 8.1, 3, 6.9)
draw_arrow(5, 8.1, 7, 6.9)
draw_arrow(15, 8.1, 11, 6.9)
draw_arrow(15, 8.1, 15, 6.9)

# ROW 5: CHARTS & EXPORT (y=4.5)
draw_box(4, 4.5, 3, 0.8, "charts.py\nBar / Line / Scatter\n(matplotlib)", C_CHART, 8)
draw_box(9, 4.5, 3, 0.8, "exporter.py\nexport_excel()\n(xlsxwriter)", C_EXPORT, 8)
draw_box(14, 4.5, 3, 0.8, "exporter.py\nexport_pdf()\n(reportlab)", C_EXPORT, 8)
draw_box(18, 4.5, 2.5, 0.8, "GUI Display\n5 Tabs", C_UI, 8)
draw_arrow(3, 6.1, 4, 4.9)
draw_arrow(7, 6.1, 4, 4.9)
draw_arrow(7, 6.1, 9, 4.9)
draw_arrow(11, 6.1, 9, 4.9)
draw_arrow(11, 6.1, 14, 4.9)
draw_arrow(15, 6.1, 14, 4.9)
draw_arrow(5.5, 4.5, 16.75, 4.5)

# ROW 6: OUTPUT FILES (y=2.5)
draw_box(4, 2.5, 3, 0.8, "Chart Images\n(.png)", C_CHART, 9)
draw_box(9, 2.5, 3, 0.8, "Excel Report\n(.xlsx)\nformatted + autofilter", C_EXPORT, 8)
draw_box(14, 2.5, 3, 0.8, "PDF Report\n(.pdf)\ntables + charts + stats", C_EXPORT, 8)
draw_arrow(4, 4.1, 4, 2.9)
draw_arrow(9, 4.1, 9, 2.9)
draw_arrow(14, 4.1, 14, 2.9)

# DECISION DIAMOND
draw_diamond(10, 11.3, 2.5, 0.9, "File\nselected?", C_UI, 8)
draw_arrow(10, 12.2, 10, 11.75)
draw_arrow(10, 10.85, 10, 10.9)
ax.text(10.3, 11.0, "Yes", fontsize=8, color="green", fontweight="bold")
draw_arrow(8.75, 11.3, 15, 11.3, color="#999")
draw_arrow(15, 11.3, 15, 10.9, color="#999")
ax.text(12, 11.5, "No (show dialog)", fontsize=8, color="#999")

# LEGEND
legend_items = [
    (C_INPUT, "Data Input"),
    (C_UI, "GUI / User Action"),
    (C_PROC, "Processing (pandas)"),
    (C_ANALYSIS, "Analysis & ML"),
    (C_CHART, "Charts (matplotlib)"),
    (C_EXPORT, "Export"),
]
for i, (color, label) in enumerate(legend_items):
    lx = 1.5 + i * 3.1
    ly = 1.0
    ax.add_patch(plt.Rectangle((lx - 0.2, ly - 0.15), 0.4, 0.3,
                               facecolor=color, edgecolor="black"))
    ax.text(lx + 0.3, ly, label, fontsize=8, va="center")

# WORKFLOW ANNOTATION
ax.text(10, 0.3,
        "Workflow:  Open File  ->  Load (background thread)  ->  "
        "Filter / Pivot  ->  Statistics / Regression / K-means  ->  "
        "Charts  ->  Export Excel / PDF",
        ha="center", va="center", fontsize=10, fontweight="bold", color="#333",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f5f5f5", edgecolor="#ccc"))

plt.tight_layout()
path = os.path.join(OUT, "flow_diagram.png")
fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Flow diagram saved to: {path}")
print(f"Size: {os.path.getsize(path):,} bytes")
plt.close()


