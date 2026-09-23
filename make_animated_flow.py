"""
Generate an ANIMATED flow diagram (GIF) for DataFlow Analyzer.

The animation:
  Phase 1 (0-3s): Layers appear one-by-one from top to bottom
  Phase 2 (3-6s): Data particles flow along all arrows
  Phase 3 (6-8s): Pulse glow on all boxes, then loop

Run:  py make_animated_flow.py
"""
import os, sys, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), "demo_output")
os.makedirs(OUT, exist_ok=True)

# ── Colors ──
C_INPUT = "#4CAF50"
C_PROC  = "#2196F3"
C_ANAL  = "#9C27B0"
C_CHART = "#FF9800"
C_EXP   = "#F44336"
C_UI    = "#607D8B"
C_TXT   = "white"

# ── Figure ──
fig, ax = plt.subplots(figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis("off")
ax.set_aspect("equal")

# ── Data structures ──
# Each box: (x, y, w, h, text, color, fontsize)
BOXES = [
    # Row 1: Data Input (y=12.2)
    (5, 12.2, 3, 0.8, "CSV File\n(.csv, .tsv)", C_INPUT, 9),
    (10, 12.2, 3, 0.8, "Excel File\n(.xlsx, .xls)", C_INPUT, 9),
    (15, 12.2, 3, 0.8, "User Action\n(File > Open / Ctrl+O)", C_UI, 9),
    # Row 2: GUI / Loader (y=10.5)
    (15, 10.5, 3.5, 0.8, "GUI: app.py\nDataFlowApp (Tkinter)", C_UI, 9),
    (10, 10.5, 3.5, 0.8, "data_loader.py\nload_file_async()", C_PROC, 9),
    (5, 10.5, 3.5, 0.8, "Background Thread\n(non-blocking)", C_PROC, 9),
    # Row 3: Data Processing (y=8.5)
    (5, 8.5, 3.5, 0.8, "pandas DataFrame\n(loaded in memory)", C_PROC, 9),
    (10, 8.5, 3.5, 0.8, "Paginated Table\n(1,000 rows/page)", C_UI, 9),
    (15, 8.5, 3.5, 0.8, "Filter Module\nfilter_data()", C_PROC, 9),
    # Row 4: Analysis & ML (y=6.5)
    (3, 6.5, 3, 0.8, "Pivot Table\npivot_table()", C_ANAL, 8),
    (7, 6.5, 3, 0.8, "Statistics\ndescribe()\ncorrelation()", C_ANAL, 8),
    (11, 6.5, 3, 0.8, "Regression\nlinear_regression()\n(NumPy OLS)", C_ANAL, 8),
    (15, 6.5, 3, 0.8, "Clustering\nkmeans()\n(Lloyd's algorithm)", C_ANAL, 8),
    # Row 5: Charts & Export (y=4.5)
    (4, 4.5, 3, 0.8, "charts.py\nBar / Line / Scatter\n(matplotlib)", C_CHART, 8),
    (9, 4.5, 3, 0.8, "exporter.py\nexport_excel()\n(xlsxwriter)", C_EXP, 8),
    (14, 4.5, 3, 0.8, "exporter.py\nexport_pdf()\n(reportlab)", C_EXP, 8),
    (18, 4.5, 2.5, 0.8, "GUI Display\n5 Tabs", C_UI, 8),
    # Row 6: Output Files (y=2.5)
    (4, 2.5, 3, 0.8, "Chart Images\n(.png)", C_CHART, 9),
    (9, 2.5, 3, 0.8, "Excel Report\n(.xlsx)\nformatted + autofilter", C_EXP, 8),
    (14, 2.5, 3, 0.8, "PDF Report\n(.pdf)\ntables + charts + stats", C_EXP, 8),
]

# Each arrow: (x1, y1, x2, y2, color, lw)  -- also defines a particle path
ARROWS = [
    (6.5, 12.2, 8.5, 12.2, "#333", 2),
    (11.5, 12.2, 13.5, 12.2, "#333", 2),
    (15, 11.8, 15, 10.9, "#333", 2),
    (13.25, 10.5, 11.75, 10.5, "#333", 2),
    (8.25, 10.5, 6.75, 10.5, "#333", 2),
    (5, 10.1, 5, 8.9, "#333", 2),
    (6.75, 8.5, 8.25, 8.5, "#333", 2),
    (6.75, 8.3, 13.25, 8.3, "#333", 2),
    (5, 8.1, 3, 6.9, "#333", 2),
    (5, 8.1, 7, 6.9, "#333", 2),
    (15, 8.1, 11, 6.9, "#333", 2),
    (15, 8.1, 15, 6.9, "#333", 2),
    (3, 6.1, 4, 4.9, "#333", 2),
    (7, 6.1, 4, 4.9, "#333", 2),
    (7, 6.1, 9, 4.9, "#333", 2),
    (11, 6.1, 9, 4.9, "#333", 2),
    (11, 6.1, 14, 4.9, "#333", 2),
    (15, 6.1, 14, 4.9, "#333", 2),
    (5.5, 4.5, 16.75, 4.5, "#333", 2),
    (4, 4.1, 4, 2.9, "#333", 2),
    (9, 4.1, 9, 2.9, "#333", 2),
    (14, 4.1, 14, 2.9, "#333", 2),
]

# Diamond
DIAMOND = (10, 11.3, 2.5, 0.9, "File\nselected?", C_UI, 8)

# ── Static drawing helpers ──

def draw_box(ax, x, y, w, h, text, color, fontsize=10, alpha=1.0, glow=0):
    if glow > 0:
        for r in range(3, 0, -1):
            g = FancyBboxPatch((x - w/2 - r*0.08, y - h/2 - r*0.08),
                               w + r*0.16, h + r*0.16,
                               boxstyle="round,pad=0.15",
                               facecolor=color, edgecolor="none",
                               alpha=glow * 0.15, mutation_aspect=0.5)
            ax.add_patch(g)
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor="black",
                         linewidth=1.5, mutation_aspect=0.5,
                         alpha=alpha)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=C_TXT, alpha=alpha)


def draw_arrow(ax, x1, y1, x2, y2, color="#333", lw=2, alpha=1.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, alpha=alpha,
                                connectionstyle="arc3,rad=0"))


def draw_diamond(ax, x, y, w, h, text, color, fontsize=9, alpha=1.0):
    diamond = plt.Polygon([(x, y + h/2), (x + w/2, y),
                          (x, y - h/2), (x - w/2, y)],
                         facecolor=color, edgecolor="black",
                         linewidth=1.5, alpha=alpha)
    ax.add_patch(diamond)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=C_TXT, alpha=alpha)


# ── Static elements (title, labels, legend) ──

def draw_static():
    ax.text(10, 13.5, "DataFlow Analyzer - Application Flow Diagram",
            ha="center", va="center", fontsize=20, fontweight="bold")
    ax.text(10, 13.0, "Architecture & User Workflow",
            ha="center", va="center", fontsize=12, color="#666")

    layers = [
        (12.2, "DATA\nINPUT"), (10.5, "GUI LAYER\n(Tkinter)"),
        (8.5, "DATA\nPROCESSING"), (6.5, "ANALYSIS\n& ML"),
        (4.5, "VISUAL\n& EXPORT"), (2.5, "OUTPUT\nFILES"),
    ]
    for y, label in layers:
        ax.text(0.5, y, label, ha="center", va="center",
                fontsize=9, fontweight="bold", color="#888", style="italic")
        ax.plot([1.2, 19.5], [y - 0.8, y - 0.8], color="#eee", lw=0.5, zorder=0)

    # Legend
    legend_items = [
        (C_INPUT, "Data Input"), (C_UI, "GUI / User Action"),
        (C_PROC, "Processing (pandas)"), (C_ANAL, "Analysis & ML"),
        (C_CHART, "Charts (matplotlib)"), (C_EXP, "Export"),
    ]
    for i, (color, label) in enumerate(legend_items):
        lx = 1.5 + i * 3.1
        ly = 1.0
        ax.add_patch(plt.Rectangle((lx - 0.2, ly - 0.15), 0.4, 0.3,
                                   facecolor=color, edgecolor="black"))
        ax.text(lx + 0.3, ly, label, fontsize=8, va="center")

    ax.text(10, 0.3,
            "Workflow:  Open File  ->  Load (background thread)  ->  "
            "Filter / Pivot  ->  Statistics / Regression / K-means  ->  "
            "Charts  ->  Export Excel / PDF",
            ha="center", va="center", fontsize=10, fontweight="bold", color="#333",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f5f5f5", edgecolor="#ccc"))


# ── Animation ──
# Phase timing (in frames, 20fps => 0.05s per frame)
# Phase 1: 0-60   (3s)  -- boxes appear layer by layer
# Phase 2: 60-120 (3s)  -- particles flow along arrows
# Phase 3: 120-160(2s)  -- glow pulse + loop
TOTAL = 160

# Map boxes to layers (by y-coordinate) for staggered appearance
LAYER_ORDER = [12.2, 10.5, 8.5, 6.5, 4.5, 2.5]
# Each layer appears at frame:
LAYER_FRAME = {12.2: 0, 10.5: 10, 8.5: 20, 6.5: 30, 4.5: 40, 2.5: 50}
# Diamond appears at frame 5
DIAMOND_FRAME = 5

# Arrows appear right after their source layer
def arrow_frame(arrow):
    x1, y1, x2, y2 = arrow[:4]
    src_y = max(y1, y2)
    for ly in LAYER_ORDER:
        if abs(src_y - ly) < 0.5:
            return LAYER_FRAME[ly] + 5
    return 10


def animate(frame):
    ax.clear()
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 14)
    ax.axis("off")
    ax.set_aspect("equal")
    draw_static()

    # Phase 1: Draw boxes with staggered appearance
    for (x, y, w, h, text, color, fs) in BOXES:
        ly = None
        for candidate in LAYER_ORDER:
            if abs(y - candidate) < 0.5:
                ly = candidate
                break
        appear = LAYER_FRAME.get(ly, 0) if ly else 0
        if frame < appear:
            continue
        # Fade-in over 5 frames
        fade = min(1.0, (frame - appear) / 5.0)

        # Phase 3: glow pulse
        glow = 0
        if frame >= 120:
            t = (frame - 120) / 40.0
            glow = 0.5 + 0.5 * math.sin(t * math.pi * 2)

        draw_box(ax, x, y, w, h, text, color, fs, alpha=fade, glow=glow)

    # Diamond
    if frame >= DIAMOND_FRAME:
        fade = min(1.0, (frame - DIAMOND_FRAME) / 5.0)
        dx, dy, dw, dh, dtext, dcolor, dfs = DIAMOND
        draw_diamond(ax, dx, dy, dw, dh, dtext, dcolor, dfs, alpha=fade)
        if frame >= DIAMOND_FRAME + 3:
            ax.text(10.3, 11.0, "Yes", fontsize=8, color="green",
                    fontweight="bold", alpha=fade)
            ax.text(12, 11.5, "No (show dialog)", fontsize=8, color="#999",
                    alpha=fade)

    # Draw arrows
    for arrow in ARROWS:
        af = arrow_frame(arrow)
        if frame < af:
            continue
        fade = min(1.0, (frame - af) / 5.0)
        draw_arrow(ax, *arrow[:4], arrow[4], arrow[5], alpha=fade)

    # Phase 2: Flowing particles
    if frame >= 60:
        t = (frame - 60) / 60.0  # 0 to 1 over 60 frames
        for i, arrow in enumerate(ARROWS):
            x1, y1, x2, y2 = arrow[:4]
            # Multiple particles per arrow, staggered
            for p in range(2):
                pt = (t + i * 0.03 + p * 0.5) % 1.0
                px = x1 + (x2 - x1) * pt
                py = y1 + (y2 - y1) * pt
                # Particle color based on source box color
                pcolor = arrow[4]
                size = 8 + 3 * math.sin(pt * math.pi)
                ax.plot(px, py, 'o', color='#FFD700', markersize=size,
                        zorder=10, alpha=0.9)
                # Trail
                for tr in range(1, 4):
                    tt = max(0, pt - tr * 0.05)
                    tx = x1 + (x2 - x1) * tt
                    ty = y1 + (y2 - y1) * tt
                    ax.plot(tx, ty, 'o', color='#FFD700',
                            markersize=size * (1 - tr * 0.3),
                            zorder=9, alpha=0.4 - tr * 0.1)

    # Phase indicator
    if frame < 60:
        ax.text(19, 13.5, "Building...", fontsize=10, color="#2196F3",
                fontweight="bold", ha="right")
    elif frame < 120:
        ax.text(19, 13.5, "Data Flow", fontsize=10, color="#FF9800",
                fontweight="bold", ha="right")
    else:
        ax.text(19, 13.5, "Complete", fontsize=10, color="#4CAF50",
                fontweight="bold", ha="right")


anim = FuncAnimation(fig, animate, frames=TOTAL, interval=50, blit=False,
                     repeat=True, repeat_delay=500)

path = os.path.join(OUT, "flow_diagram_animated.gif")
writer = PillowWriter(fps=20)
anim.save(path, writer=writer, dpi=80)
print(f"Animated GIF saved to: {path}")
print(f"Size: {os.path.getsize(path):,} bytes")
plt.close()
