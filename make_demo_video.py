"""
Generate a 2-minute demo video for DataFlow Analyzer.

Creates an animated walkthrough of the application's features using matplotlib
and imageio-ffmpeg.  Output: demo_output/dataflow_demo.mp4

Run:  py make_demo_video.py
"""
import os, sys, math, io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import imageio.v2 as imageio

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_output")
os.makedirs(OUT, exist_ok=True)

# ── Colors ──
C_INPUT = "#4CAF50"; C_PROC = "#2196F3"; C_ANAL = "#9C27B0"
C_CHART = "#FF9800"; C_EXP = "#F44336"; C_UI = "#607D8B"
C_BG = "#1a1a2e"; C_PANEL = "#16213e"; C_ACCENT = "#0f3460"
C_TEXT = "#e0e0e0"; C_HIGHLIGHT = "#e94560"
WHITE = "#ffffff"

FPS = 15
TOTAL_SECONDS = 120
TOTAL_FRAMES = FPS * TOTAL_SECONDS  # 1800

# ── Helpers ──

def new_fig():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=80)
    fig.patch.set_facecolor(C_BG)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.set_aspect("auto")
    return fig, ax

def fig_to_array(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', facecolor=fig.get_facecolor(), dpi=80)
    plt.close(fig)
    buf.seek(0)
    import PIL.Image
    img = np.array(PIL.Image.open(buf))
    return img

def draw_box(ax, x, y, w, h, text, color, fontsize=9, text_color=WHITE, alpha=1.0):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.12",
                         facecolor=color, edgecolor="white", linewidth=1.0,
                         mutation_aspect=0.5, alpha=alpha)
    ax.add_patch(box)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color, alpha=alpha)

def draw_arrow(ax, x1, y1, x2, y2, color="#888", lw=1.5, alpha=1.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, alpha=alpha,
                                connectionstyle="arc3,rad=0"))

def ease_in_out(t):
    return 0.5 * (1 - math.cos(math.pi * t))

def lerp(a, b, t):
    return a + (b - a) * t

# ── Scene renderers ──
# Each returns a numpy image array

def scene_title(frame, start, end):
    """Scene 1: Title screen (0-12s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    # Animated gradient background lines
    for i in range(20):
        y = 0.5 + i * 0.45
        offset = math.sin(t * math.pi * 2 + i * 0.3) * 0.3
        ax.plot([0, 16], [y + offset, y + offset], color=C_ACCENT,
                alpha=0.15, lw=0.5)

    # Title fade-in
    title_alpha = min(1.0, t * 3)
    ax.text(8, 5.5, "DataFlow Analyzer", ha="center", va="center",
            fontsize=42, fontweight="bold", color=WHITE, alpha=title_alpha)
    ax.text(8, 4.5, "Desktop Data Analysis Tool", ha="center", va="center",
            fontsize=18, color=C_CHART, alpha=title_alpha)

    # Animated underline
    if t > 0.2:
        ul_t = min(1.0, (t - 0.2) * 2.5)
        ul_w = 6 * ease_in_out(ul_t)
        ax.plot([8 - ul_w/2, 8 + ul_w/2], [3.8, 3.8], color=C_HIGHLIGHT,
                lw=3, alpha=title_alpha)

    # Feature badges appear
    features = ["CSV / Excel", "Filter & Pivot", "Charts", "Regression", "K-means", "Export"]
    for i, feat in enumerate(features):
        ft = max(0, (t - 0.3 - i * 0.08))
        fa = min(1.0, ft * 4)
        fx = 2.5 + i * 2.2
        fy = 2.5
        if fa > 0:
            draw_box(ax, fx, fy, 1.8, 0.5, feat, C_ACCENT, fontsize=8, alpha=fa)

    # Pulsing dot
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 4)
    r = 0.1 + 0.05 * pulse
    ax.add_patch(plt.Circle((8, 1.2), r, color=C_HIGHLIGHT, alpha=0.8))
    ax.text(8, 0.7, "Loading demo...", ha="center", fontsize=10, color=C_TEXT,
            alpha=0.6)

    return fig_to_array(fig)

def scene_file_open(frame, start, end):
    """Scene 2: File open + loading (12-28s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    # Window frame
    ax.add_patch(FancyBboxPatch((1, 1), 14, 7, boxstyle="round,pad=0.2",
                 facecolor=C_PANEL, edgecolor=C_ACCENT, linewidth=2))
    # Title bar
    ax.add_patch(FancyBboxPatch((1, 7.2), 14, 0.8, boxstyle="round,pad=0.1",
                 facecolor=C_ACCENT, edgecolor="none"))
    ax.text(2, 7.6, "DataFlow Analyzer", fontsize=11, color=WHITE, fontweight="bold")
    # Window buttons
    for i, c in enumerate(["#ff5f57", "#ffbd2e", "#28c941"]):
        ax.add_patch(plt.Circle((14.2 - i*0.35, 7.6), 0.1, color=c))

    # Toolbar
    ax.add_patch(FancyBboxPatch((1.2, 6.4), 13.6, 0.6, boxstyle="round,pad=0.05",
                 facecolor="#0a1628", edgecolor="none"))
    draw_box(ax, 2.5, 6.7, 1.5, 0.4, "Open File", C_PROC, 8)
    draw_box(ax, 4.5, 6.7, 1.5, 0.4, "Export Excel", C_EXP, 8)
    draw_box(ax, 6.5, 6.7, 1.5, 0.4, "Export PDF", C_EXP, 8)

    # File dialog appears
    if t < 0.3:
        dialog_alpha = ease_in_out(t / 0.3)
    else:
        dialog_alpha = 1.0
    ax.add_patch(FancyBboxPatch((3, 3), 10, 3, boxstyle="round,pad=0.2",
                 facecolor="#1e2a4a", edgecolor=C_ACCENT, linewidth=1.5,
                 alpha=dialog_alpha))
    ax.text(8, 5.5, "Open Data File", ha="center", fontsize=14,
            color=WHITE, fontweight="bold", alpha=dialog_alpha)

    # File list
    files = ["sales_data.csv", "customers.xlsx", "orders.tsv", "products.csv"]
    for i, f in enumerate(files):
        fy = 4.8 - i * 0.5
        highlight = (i == 0 and t > 0.4)
        bg = C_ACCENT if highlight else "none"
        if highlight:
            ax.add_patch(FancyBboxPatch((3.5, fy - 0.15), 6, 0.35,
                         boxstyle="round,pad=0.05", facecolor=C_ACCENT,
                         edgecolor="none", alpha=dialog_alpha))
        ax.text(4, fy, f"  {f}", fontsize=10, color=C_TEXT, alpha=dialog_alpha)

    # Click animation on first file
    if 0.35 < t < 0.5:
        click_t = (t - 0.35) / 0.15
        click_r = 0.3 * (1 - click_t)
        ax.add_patch(plt.Circle((5, 4.8), click_r, color=C_HIGHLIGHT,
                     alpha=0.5 * (1 - click_t)))

    # Loading spinner after file selected
    if t > 0.5:
        lt = (t - 0.5) / 0.5
        # Spinner
        cx, cy = 8, 2.5
        angle = lt * 360 * 3
        for i in range(8):
            a = math.radians(angle + i * 45)
            ar = 1.0 - (i / 8.0)
            r = int(33 * ar + 26 * (1 - ar))
            g = int(150 * ar + 26 * (1 - ar))
            b = int(243 * ar + 46 * (1 - ar))
            color = f"#{r:02x}{g:02x}{b:02x}"
            x1 = cx + 0.15 * math.cos(a)
            y1 = cy + 0.15 * math.cos(a)
            x2 = cx + 0.4 * math.cos(a)
            y2 = cy + 0.4 * math.cos(a)
            ax.plot([x1, x2], [y1, y2], color=color, lw=2.5, solid_capstyle="round")

        # Progress bar
        bar_w = 6 * min(1.0, lt * 1.5)
        ax.add_patch(FancyBboxPatch((5, 1.8), 6, 0.3, boxstyle="round,pad=0.05",
                     facecolor="#0a1628", edgecolor="none"))
        ax.add_patch(FancyBboxPatch((5, 1.8), bar_w, 0.3, boxstyle="round,pad=0.05",
                     facecolor=C_PROC, edgecolor="none"))

        # Typewriter status
        status = "Loading sales_data.csv ... 2,000 rows detected"
        nchars = int(lt * len(status))
        ax.text(8, 1.3, status[:nchars], ha="center", fontsize=9,
                color=C_CHART, family="monospace")

    return fig_to_array(fig)

def scene_data_table(frame, start, end):
    """Scene 3: Data table with staggered row reveal (28-48s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    # Window frame
    ax.add_patch(FancyBboxPatch((0.5, 0.5), 15, 8, boxstyle="round,pad=0.2",
                 facecolor=C_PANEL, edgecolor=C_ACCENT, linewidth=2))
    ax.add_patch(FancyBboxPatch((0.5, 7.2), 15, 1.3, boxstyle="round,pad=0.1",
                 facecolor=C_ACCENT, edgecolor="none"))
    ax.text(1.5, 7.85, "DataFlow Analyzer", fontsize=11, color=WHITE, fontweight="bold")
    for i, c in enumerate(["#ff5f57", "#ffbd2e", "#28c941"]):
        ax.add_patch(plt.Circle((14.2 - i*0.35, 7.85), 0.1, color=c))

    # Left panel
    ax.add_patch(FancyBboxPatch((0.8, 0.8), 3.5, 6, boxstyle="round,pad=0.1",
                 facecolor="#0d1b2e", edgecolor=C_ACCENT, linewidth=1))
    ax.text(2.55, 6.4, "Controls", ha="center", fontsize=9, color=C_CHART, fontweight="bold")
    # Control items
    for i, label in enumerate(["Data Source", "Filter", "Pivot Table", "Chart", "Analysis & ML"]):
        draw_box(ax, 2.55, 5.7 - i * 0.9, 3, 0.6, label, C_ACCENT, 8)

    # Data tab area
    ax.text(5, 6.7, "Data Tab - Paginated Table (1,000 rows/page)", fontsize=9,
            color=C_CHART, fontweight="bold")

    # Table header
    headers = ["order_id", "date", "region", "category", "units", "unit_price", "revenue"]
    col_x = [5.2, 6.5, 7.8, 9.0, 10.0, 11.2, 12.5]
    for i, (h, cx) in enumerate(zip(headers, col_x)):
        ax.add_patch(FancyBboxPatch((cx - 0.55, 6.0), 1.1, 0.35,
                     boxstyle="round,pad=0.03", facecolor=C_PROC, edgecolor="none"))
        ax.text(cx, 6.17, h, ha="center", va="center", fontsize=6.5,
                color=WHITE, fontweight="bold")

    # Staggered row reveal
    sample_data = [
        ["1001", "2024-01-15", "North", "Electronics", "5", "299.99", "1499.95"],
        ["1002", "2024-01-16", "South", "Clothing", "12", "49.99", "599.88"],
        ["1003", "2024-01-17", "East", "Food", "50", "9.99", "499.50"],
        ["1004", "2024-01-18", "West", "Electronics", "3", "599.99", "1799.97"],
        ["1005", "2024-01-19", "North", "Books", "20", "14.99", "299.80"],
        ["1006", "2024-01-20", "South", "Clothing", "8", "79.99", "639.92"],
        ["1007", "2024-01-21", "East", "Food", "35", "12.50", "437.50"],
        ["1008", "2024-01-22", "West", "Electronics", "7", "449.99", "3149.93"],
        ["1009", "2024-01-23", "North", "Books", "15", "19.99", "299.85"],
        ["1010", "2024-01-24", "South", "Food", "60", "7.99", "479.40"],
    ]

    rows_to_show = int(t * 20)  # Reveal rows progressively
    for r in range(min(rows_to_show, len(sample_data))):
        row_t = min(1.0, (t * 20 - r))
        row_alpha = ease_in_out(row_t)
        row_y = 5.6 - r * 0.45
        bg = "#0a1628" if r % 2 == 0 else "#0d1b2e"
        ax.add_patch(FancyBboxPatch((4.7, row_y - 0.15), 8.5, 0.35,
                     boxstyle="round,pad=0.02", facecolor=bg, edgecolor="none",
                     alpha=row_alpha))
        for i, (val, cx) in enumerate(zip(sample_data[r], col_x)):
            ax.text(cx, row_y, val, ha="center", va="center", fontsize=6.5,
                    color=C_TEXT, alpha=row_alpha)

    # Pulsing status dot
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 4)
    ax.add_patch(plt.Circle((1.2, 1.0), 0.08 + 0.04 * pulse, color=C_INPUT, alpha=0.8))

    # Typewriter status
    if t > 0.1:
        status = "Loaded 2,000 rows x 7 cols"
        nchars = int(min(1.0, (t - 0.1) * 3) * len(status))
        ax.text(1.5, 1.0, status[:nchars], fontsize=8, color=C_TEXT, family="monospace")

    # Page info
    ax.text(13, 1.0, "Page 1/2  (rows 1-1000 of 2,000)", fontsize=7, color=C_TEXT)

    return fig_to_array(fig)

def scene_filter(frame, start, end):
    """Scene 4: Filtering (48-62s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    ax.add_patch(FancyBboxPatch((0.5, 0.5), 15, 8, boxstyle="round,pad=0.2",
                 facecolor=C_PANEL, edgecolor=C_ACCENT, linewidth=2))
    ax.add_patch(FancyBboxPatch((0.5, 7.2), 15, 1.3, boxstyle="round,pad=0.1",
                 facecolor=C_ACCENT, edgecolor="none"))
    ax.text(1.5, 7.85, "DataFlow Analyzer", fontsize=11, color=WHITE, fontweight="bold")

    # Left panel - filter section highlighted
    ax.add_patch(FancyBboxPatch((0.8, 0.8), 3.5, 6, boxstyle="round,pad=0.1",
                 facecolor="#0d1b2e", edgecolor=C_ACCENT, linewidth=1))
    ax.text(2.55, 6.4, "Controls", ha="center", fontsize=9, color=C_CHART, fontweight="bold")

    # Filter section with highlight
    if t > 0.1:
        hl_alpha = 0.3 + 0.2 * math.sin(t * math.pi * 3)
        ax.add_patch(FancyBboxPatch((0.9, 4.8), 3.3, 1.5,
                     boxstyle="round,pad=0.1", facecolor=C_PROC, edgecolor="none",
                     alpha=hl_alpha))
    ax.text(2.55, 5.9, "Filter", ha="center", fontsize=8, color=WHITE, fontweight="bold")

    # Filter controls
    draw_box(ax, 2.55, 5.5, 2.8, 0.35, "region", C_ACCENT, 7)
    draw_box(ax, 2.55, 5.0, 2.8, 0.35, "==", C_ACCENT, 7)
    # Typewriter in filter value
    filter_val = "North"
    nchars = int(min(1.0, t * 2) * len(filter_val)) if t > 0.2 else 0
    draw_box(ax, 2.55, 4.5, 2.8, 0.35, filter_val[:nchars] or " ", C_ACCENT, 7)

    # Apply button with click animation
    if 0.4 < t < 0.55:
        click_t = (t - 0.4) / 0.15
        click_r = 0.4 * (1 - click_t)
        ax.add_patch(plt.Circle((2.55, 4.0), click_r, color=C_HIGHLIGHT, alpha=0.5))
    draw_box(ax, 2.55, 4.0, 1.3, 0.35, "Apply", C_INPUT, 7)

    # Progress bar
    if 0.5 < t < 0.7:
        pt = (t - 0.5) / 0.2
        bar_w = 2.5 * pt
        ax.add_patch(FancyBboxPatch((1.2, 3.3), 2.5, 0.2, boxstyle="round,pad=0.03",
                     facecolor="#0a1628", edgecolor="none"))
        ax.add_patch(FancyBboxPatch((1.2, 3.3), bar_w, 0.2, boxstyle="round,pad=0.03",
                     facecolor=C_PROC, edgecolor="none"))

    # Results table
    ax.text(8, 6.7, "Filtered Results", fontsize=9, color=C_CHART, fontweight="bold")
    headers = ["order_id", "region", "category", "units", "revenue"]
    col_x = [5.5, 7.0, 8.5, 10.0, 11.5]
    for h, cx in zip(headers, col_x):
        ax.add_patch(FancyBboxPatch((cx - 0.6, 6.0), 1.2, 0.35,
                     boxstyle="round,pad=0.03", facecolor=C_PROC, edgecolor="none"))
        ax.text(cx, 6.17, h, ha="center", fontsize=7, color=WHITE, fontweight="bold")

    # Filtered rows (only North region)
    filtered = [
        ["1001", "North", "Electronics", "5", "1499.95"],
        ["1005", "North", "Books", "20", "299.80"],
        ["1009", "North", "Books", "15", "299.85"],
        ["1012", "North", "Food", "40", "319.60"],
        ["1018", "North", "Electronics", "10", "2999.90"],
    ]
    show_rows = int(max(0, (t - 0.6)) * 15) if t > 0.6 else 0
    for r in range(min(show_rows, len(filtered))):
        ra = min(1.0, (t - 0.6) * 15 - r)
        row_y = 5.6 - r * 0.45
        ax.add_patch(FancyBboxPatch((4.9, row_y - 0.15), 7.5, 0.35,
                     boxstyle="round,pad=0.02", facecolor="#0a1628", edgecolor="none",
                     alpha=ra))
        for val, cx in zip(filtered[r], col_x):
            ax.text(cx, row_y, val, ha="center", fontsize=7, color=C_TEXT, alpha=ra)

    # Status
    if t > 0.7:
        status = "Filter applied: 516 rows"
        nchars = int(min(1.0, (t - 0.7) * 3) * len(status))
        ax.text(1.5, 1.0, status[:nchars], fontsize=8, color=C_INPUT, family="monospace")

    return fig_to_array(fig)

def scene_charts(frame, start, end):
    """Scene 5: Charts with fade-in (62-82s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    ax.add_patch(FancyBboxPatch((0.5, 0.5), 15, 8, boxstyle="round,pad=0.2",
                 facecolor=C_PANEL, edgecolor=C_ACCENT, linewidth=2))
    ax.add_patch(FancyBboxPatch((0.5, 7.2), 15, 1.3, boxstyle="round,pad=0.1",
                 facecolor=C_ACCENT, edgecolor="none"))
    ax.text(1.5, 7.85, "DataFlow Analyzer - Charts Tab", fontsize=11,
            color=WHITE, fontweight="bold")

    # Chart type tabs
    chart_types = ["Bar", "Line", "Scatter"]
    for i, ct in enumerate(chart_types):
        active = (i == int(t * 3) % 3) if t > 0.3 else (i == 0)
        color = C_CHART if active else C_ACCENT
        draw_box(ax, 3 + i * 2, 6.5, 1.5, 0.4, ct, color, 8)

    # Chart area
    chart_alpha = min(1.0, t * 2) if t < 0.5 else 1.0
    ax.add_patch(FancyBboxPatch((1.5, 1.0), 13, 5, boxstyle="round,pad=0.1",
                 facecolor="#0a1628", edgecolor=C_ACCENT, linewidth=1, alpha=chart_alpha))

    # Draw animated chart based on which type
    chart_idx = int(t * 3) % 3 if t > 0.3 else 0
    local_t = (t * 3) % 1.0 if t > 0.3 else t

    # Generate sample data
    categories = ['North', 'South', 'East', 'West', 'Central']
    values = [4500, 3200, 5100, 2800, 3900]

    # Chart axes
    ax.plot([2.5, 13.5], [1.5, 1.5], color="#333", lw=1, alpha=chart_alpha)
    ax.plot([2.5, 2.5], [1.5, 5.5], color="#333", lw=1, alpha=chart_alpha)

    if chart_idx == 0:  # Bar chart
        ax.text(7.5, 5.7, "Bar Chart: Revenue by Region", ha="center",
                fontsize=10, color=C_CHART, fontweight="bold", alpha=chart_alpha)
        bar_w = 1.2
        for i, (cat, val) in enumerate(zip(categories, values)):
            bx = 3.5 + i * 2
            bh = (val / 5500) * 3.5 * min(1.0, local_t * 2 + i * 0.1)
            colors = [C_PROC, C_INPUT, C_CHART, C_EXP, C_ANAL]
            ax.add_patch(FancyBboxPatch((bx - bar_w/2, 1.5), bar_w, bh,
                         boxstyle="round,pad=0.05", facecolor=colors[i],
                         edgecolor="none", alpha=chart_alpha * 0.85))
            ax.text(bx, 1.3, cat, ha="center", fontsize=7, color=C_TEXT, alpha=chart_alpha)
            if bh > 1:
                ax.text(bx, 1.5 + bh + 0.15, f"{val:,}", ha="center",
                        fontsize=7, color=WHITE, alpha=chart_alpha)

    elif chart_idx == 1:  # Line chart
        ax.text(7.5, 5.7, "Line Chart: Monthly Revenue Trend", ha="center",
                fontsize=10, color=C_CHART, fontweight="bold", alpha=chart_alpha)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        rev_data = [12000, 15000, 13500, 18000, 16500, 21000]
        xs = np.linspace(3.5, 13, len(months))
        ys = 1.5 + (np.array(rev_data) / 22000) * 3.5

        # Animated line draw
        n_show = max(2, int(local_t * len(months)))
        ax.plot(xs[:n_show], ys[:n_show], color=C_CHART, lw=2.5,
                marker="o", markersize=6, alpha=chart_alpha)
        for i, (m, x, y) in enumerate(zip(months, xs, ys)):
            if i < n_show:
                ax.text(x, 1.2, m, ha="center", fontsize=7, color=C_TEXT, alpha=chart_alpha)

    else:  # Scatter
        ax.text(7.5, 5.7, "Scatter Plot: Units vs Revenue", ha="center",
                fontsize=10, color=C_CHART, fontweight="bold", alpha=chart_alpha)
        np.random.seed(42)
        sx = np.random.uniform(3.5, 13, 30)
        sy = 1.5 + (sx - 3.5) / 10 * 3.5 + np.random.uniform(-0.5, 0.5, 30)
        n_show = int(local_t * 30)
        ax.scatter(sx[:n_show], sy[:n_show], c=C_ANAL, s=30, alpha=chart_alpha * 0.7)

    # Fade-in effect indicator
    if t < 0.5:
        ax.text(14, 6.5, "Fade-in...", fontsize=8, color=C_CHART, alpha=1 - t * 2)

    return fig_to_array(fig)

def scene_analysis(frame, start, end):
    """Scene 6: Analysis & ML (82-102s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    ax.add_patch(FancyBboxPatch((0.5, 0.5), 15, 8, boxstyle="round,pad=0.2",
                 facecolor=C_PANEL, edgecolor=C_ACCENT, linewidth=2))
    ax.add_patch(FancyBboxPatch((0.5, 7.2), 15, 1.3, boxstyle="round,pad=0.1",
                 facecolor=C_ACCENT, edgecolor="none"))
    ax.text(1.5, 7.85, "DataFlow Analyzer - Analysis & ML", fontsize=11,
            color=WHITE, fontweight="bold")

    # Three sub-sections: Statistics, Regression, K-means
    section_t = t * 3
    section_idx = int(section_t)
    local_t = section_t % 1.0

    # Section 1: Summary Statistics
    if section_idx == 0:
        ax.text(8, 6.5, "Summary Statistics (describe())", ha="center",
                fontsize=12, color=C_ANAL, fontweight="bold")
        headers = ["Column", "mean", "std", "min", "25%", "50%", "75%", "max"]
        col_x = [2.5, 4.5, 6.0, 7.5, 9.0, 10.5, 12.0, 13.5]
        for h, cx in zip(headers, col_x):
            ax.add_patch(FancyBboxPatch((cx - 0.6, 5.8), 1.2, 0.35,
                         boxstyle="round,pad=0.03", facecolor=C_ANAL, edgecolor="none"))
            ax.text(cx, 5.97, h, ha="center", fontsize=7, color=WHITE, fontweight="bold")

        stats = [
            ["units", "12.5", "8.3", "1", "5", "10", "18", "50"],
            ["unit_price", "156.32", "189.45", "7.99", "29.99", "79.99", "199.99", "599.99"],
            ["revenue", "1875.6", "1240.8", "7.99", "299.8", "899.9", "2200", "5999.9"],
        ]
        for r, row in enumerate(stats):
            ra = min(1.0, local_t * 4 - r * 0.3)
            if ra <= 0:
                continue
            row_y = 5.3 - r * 0.5
            ax.add_patch(FancyBboxPatch((1.9, row_y - 0.15), 12.2, 0.35,
                         boxstyle="round,pad=0.02", facecolor="#0a1628",
                         edgecolor="none", alpha=ra))
            for val, cx in zip(row, col_x):
                ax.text(cx, row_y, val, ha="center", fontsize=7, color=C_TEXT, alpha=ra)

    # Section 2: Regression
    elif section_idx == 1:
        ax.text(8, 6.5, "Linear Regression (NumPy OLS)", ha="center",
                fontsize=12, color=C_PROC, fontweight="bold")

        # Scatter + regression line
        np.random.seed(42)
        sx = np.linspace(3, 13, 25)
        sy = 1.5 + (sx - 3) / 10 * 3.5 + np.random.uniform(-0.6, 0.6, 25)
        n_show = int(local_t * 25)
        ax.scatter(sx[:n_show], sy[:n_show], c=C_CHART, s=25, alpha=0.7)

        # Regression line
        if local_t > 0.5:
            line_t = (local_t - 0.5) * 2
            slope = 0.35
            intercept = 0.5
            x_end = 3 + 10 * line_t
            y_end = 1.5 + (slope * 10 * line_t) + intercept
            ax.plot([3, x_end], [1.5 + intercept, y_end], color=C_HIGHLIGHT,
                    lw=2.5, alpha=0.9)

        # Results
        if local_t > 0.7:
            res_t = (local_t - 0.7) / 0.3
            ax.text(10, 5.5, f"slope: 0.346", fontsize=9, color=C_TEXT, alpha=res_t)
            ax.text(10, 5.0, f"intercept: 0.482", fontsize=9, color=C_TEXT, alpha=res_t)
            ax.text(10, 4.5, f"R\u00b2 = 0.847", fontsize=9, color=C_INPUT,
                    fontweight="bold", alpha=res_t)

    # Section 3: K-means
    else:
        ax.text(8, 6.5, "K-Means Clustering (k=3)", ha="center",
                fontsize=12, color=C_INPUT, fontweight="bold")

        # Cluster centers
        centers = [(5, 3), (9, 4.5), (11, 2.5)]
        colors = [C_INPUT, C_PROC, C_CHART]
        np.random.seed(42)

        for ci, (cx, cy) in enumerate(centers):
            pts = np.random.randn(10, 2) * 0.6
            pts[:, 0] += cx
            pts[:, 1] += cy
            n_show = int(local_t * 10)
            ax.scatter(pts[:n_show, 0], pts[:n_show, 1], c=colors[ci], s=25, alpha=0.7)
            # Cluster center
            if local_t > 0.5:
                ax.scatter([cx], [cy], c=colors[ci], s=100, marker='X',
                           edgecolors=WHITE, linewidths=1.5, zorder=5)

        # Cluster labels
        if local_t > 0.7:
            for ci, (cx, cy) in enumerate(centers):
                ax.text(cx, cy + 0.8, f"Cluster {ci}", ha="center",
                        fontsize=8, color=colors[ci], fontweight="bold")

    # Progress bar
    if local_t < 0.3:
        pt = local_t / 0.3
        ax.add_patch(FancyBboxPatch((5, 0.8), 6, 0.2, boxstyle="round,pad=0.03",
                     facecolor="#0a1628", edgecolor="none"))
        ax.add_patch(FancyBboxPatch((5, 0.8), 6 * pt, 0.2, boxstyle="round,pad=0.03",
                     facecolor=C_ANAL, edgecolor="none"))

    return fig_to_array(fig)

def scene_export(frame, start, end):
    """Scene 7: Export (102-115s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    ax.add_patch(FancyBboxPatch((0.5, 0.5), 15, 8, boxstyle="round,pad=0.2",
                 facecolor=C_PANEL, edgecolor=C_ACCENT, linewidth=2))
    ax.add_patch(FancyBboxPatch((0.5, 7.2), 15, 1.3, boxstyle="round,pad=0.1",
                 facecolor=C_ACCENT, edgecolor="none"))
    ax.text(1.5, 7.85, "DataFlow Analyzer - Export", fontsize=11,
            color=WHITE, fontweight="bold")

    # Two export options
    # Excel
    excel_alpha = 1.0 if t < 0.5 else max(0.3, 1.0 - (t - 0.5) * 1.4)
    draw_box(ax, 5, 4.5, 4, 2.5, "Export to\nExcel (.xlsx)\n\nFormatted + Autofilter",
             C_EXP, 10, alpha=excel_alpha)

    # PDF
    pdf_alpha = 1.0 if t > 0.4 else max(0.3, t * 2.5)
    draw_box(ax, 11, 4.5, 4, 2.5, "Export to\nPDF (.pdf)\n\nTables + Charts + Stats",
             C_EXP, 10, alpha=pdf_alpha)

    # Click animation
    if 0.2 < t < 0.35:
        click_t = (t - 0.2) / 0.15
        ax.add_patch(plt.Circle((5, 4.5), 0.5 * (1 - click_t), color=C_HIGHLIGHT, alpha=0.5))

    # Progress bar for Excel
    if 0.3 < t < 0.5:
        pt = (t - 0.3) / 0.2
        ax.add_patch(FancyBboxPatch((3, 2.5), 4, 0.3, boxstyle="round,pad=0.05",
                     facecolor="#0a1628", edgecolor="none"))
        ax.add_patch(FancyBboxPatch((3, 2.5), 4 * pt, 0.3, boxstyle="round,pad=0.05",
                     facecolor=C_INPUT, edgecolor="none"))
        ax.text(5, 2.0, "Exporting Excel...", ha="center", fontsize=8, color=C_TEXT)

    # Excel file icon
    if t > 0.5:
        ft = min(1.0, (t - 0.5) * 3)
        ax.add_patch(FancyBboxPatch((4.2, 1.0), 1.6, 1.2, boxstyle="round,pad=0.1",
                     facecolor=C_INPUT, edgecolor=WHITE, linewidth=1, alpha=ft))
        ax.text(5, 1.6, "XLSX", ha="center", fontsize=8, color=WHITE, fontweight="bold", alpha=ft)
        ax.text(5, 0.7, "sales_report.xlsx", ha="center", fontsize=7, color=C_TEXT, alpha=ft)

    # Click on PDF
    if 0.65 < t < 0.8:
        click_t = (t - 0.65) / 0.15
        ax.add_patch(plt.Circle((11, 4.5), 0.5 * (1 - click_t), color=C_HIGHLIGHT, alpha=0.5))

    # Progress bar for PDF
    if 0.75 < t < 0.95:
        pt = (t - 0.75) / 0.2
        ax.add_patch(FancyBboxPatch((9, 2.5), 4, 0.3, boxstyle="round,pad=0.05",
                     facecolor="#0a1628", edgecolor="none"))
        ax.add_patch(FancyBboxPatch((9, 2.5), 4 * pt, 0.3, boxstyle="round,pad=0.05",
                     facecolor=C_EXP, edgecolor="none"))
        ax.text(11, 2.0, "Exporting PDF...", ha="center", fontsize=8, color=C_TEXT)

    # PDF file icon
    if t > 0.95:
        ft = min(1.0, (t - 0.95) * 5)
        ax.add_patch(FancyBboxPatch((10.2, 1.0), 1.6, 1.2, boxstyle="round,pad=0.1",
                     facecolor=C_EXP, edgecolor=WHITE, linewidth=1, alpha=ft))
        ax.text(11, 1.6, "PDF", ha="center", fontsize=8, color=WHITE, fontweight="bold", alpha=ft)
        ax.text(11, 0.7, "sales_report.pdf", ha="center", fontsize=7, color=C_TEXT, alpha=ft)

    return fig_to_array(fig)

def scene_closing(frame, start, end):
    """Scene 8: Closing screen (115-120s)"""
    fig, ax = new_fig()
    t = (frame - start) / (end - start)

    # Fade from previous to closing
    for i in range(20):
        y = 0.5 + i * 0.45
        offset = math.sin(t * math.pi * 2 + i * 0.3) * 0.3
        ax.plot([0, 16], [y + offset, y + offset], color=C_ACCENT, alpha=0.15, lw=0.5)

    alpha = min(1.0, t * 3)
    ax.text(8, 5.5, "DataFlow Analyzer", ha="center", fontsize=36,
            color=WHITE, fontweight="bold", alpha=alpha)
    ax.text(8, 4.5, "Thank You", ha="center", fontsize=20, color=C_CHART, alpha=alpha)

    features = ["CSV / Excel Import", "Filter & Pivot", "Charts", "Regression", "K-means", "Export"]
    for i, feat in enumerate(features):
        ft = max(0, (t - 0.2 - i * 0.06))
        fa = min(1.0, ft * 5)
        fx = 2.5 + i * 2.2
        if fa > 0:
            draw_box(ax, fx, 3.0, 1.8, 0.5, feat, C_ACCENT, 8, alpha=fa)

    ax.text(8, 1.5, "Built with Python, Tkinter, pandas, matplotlib", ha="center",
            fontsize=10, color=C_TEXT, alpha=alpha * 0.7)

    return fig_to_array(fig)

# ── Main ──
def main():
    scenes = [
        (0, 180, scene_title),          # 0-12s
        (180, 420, scene_file_open),    # 12-28s
        (420, 720, scene_data_table),    # 28-48s
        (720, 930, scene_filter),        # 48-62s
        (930, 1230, scene_charts),       # 62-82s
        (1230, 1530, scene_analysis),    # 82-102s
        (1530, 1725, scene_export),      # 102-115s
        (1725, 1800, scene_closing),     # 115-120s
    ]

    output_path = os.path.join(OUT, "dataflow_demo.mp4")
    writer = imageio.get_writer(output_path, fps=FPS, codec='libx264',
                                 quality=8, macro_block_size=1)

    total = TOTAL_FRAMES
    for frame in range(total):
        for (s, e, renderer) in scenes:
            if s <= frame < e:
                img = renderer(frame, s, e)
                writer.append_data(img)
                break
        if frame % 50 == 0:
            pct = frame / total * 100
            print(f"  Frame {frame}/{total} ({pct:.0f}%)")

    writer.close()
    size = os.path.getsize(output_path)
    print(f"\nVideo saved: {output_path}")
    print(f"Size: {size:,} bytes ({size/1024/1024:.1f} MB)")

if __name__ == "__main__":
    main()
