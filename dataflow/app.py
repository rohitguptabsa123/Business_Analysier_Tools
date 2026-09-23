"""Main Tkinter GUI for DataFlow Analyzer.

The application is a single-window desktop app organised as:

    +----------------------------------------------------------+
    |  Menu bar  (File / Analysis / Help)                      |
    +----------------------------------------------------------+
    |  Toolbar  (Open / Export Excel / Export PDF)             |
    +------------------+---------------------------------------+
    |  Control panel   |  Notebook tabs                        |
    |  - Data source   |   Data | Summary | Charts | Pivot | ML|
    |  - Filter        |                                       |
    |  - Pivot         |                                       |
    |  - Chart         |                                       |
    |  - Analysis      |                                       |
    +------------------+---------------------------------------+
    |  Status bar  (row count / status message)               |
    +----------------------------------------------------------+

The data table uses pagination (default 1 000 rows per page) so that a
500 000-row file never blocks the UI.
"""

from __future__ import annotations

import math
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from . import analysis, charts, data_loader, exporter

# Rows shown per page in the Data tab.  Pagination keeps the Treeview fast
# even for the 500k-row acceptance-test files.
PAGE_SIZE = 1000

# Chart types offered in the UI.
CHART_TYPES = ["bar", "line", "scatter"]

# Aggregation functions available for pivot tables.
AGG_FUNCS = ["mean", "sum", "count", "min", "max", "median", "std"]


class DataFlowApp(tk.Tk):
    """The application window - a :class:`tkinter.Tk` subclass."""

    def __init__(self) -> None:
        super().__init__()
        self.title("DataFlow Analyzer")
        self.geometry("1280x800")
        self.minsize(960, 600)

        # ---- application state ------------------------------------------------
        self.df: pd.DataFrame | None = None        # full loaded dataset
        self.view_df: pd.DataFrame | None = None   # currently visible (filtered) data
        self.page = 0                               # zero-based page index
        self.chart_figures: list[Figure] = []       # charts for PDF export
        self.current_chart_figure: Figure | None = None

        # ---- animation state ---------------------------------------------------
        self._tw_queue: str = ""                     # typewriter buffer
        self._tw_pos: int = 0                       # typewriter cursor
        self._tw_after_id: str | None = None        # pending after() id
        self._pulse_after_id: str | None = None     # pulse loop after() id
        self._row_after_ids: list[str] = []          # staggered row animation ids
        self._chart_after_id: str | None = None     # chart animation after() id
        self._loading_after_id: str | None = None   # loading spinner after() id
        self._loading_angle: float = 0.0             # spinner rotation angle
        self._is_loading: bool = False

        # ---- UI construction ---------------------------------------------------
        self._build_menu()
        self._build_toolbar()
        self._build_main()
        self._build_statusbar()

        self._set_status("Ready. Open a CSV or Excel file to begin.")

    # ------------------------------------------------------------------ menu
    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open...", command=self.on_open,
                              accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Export to Excel...",
                              command=self.on_export_excel)
        file_menu.add_command(label="Export to PDF...",
                              command=self.on_export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self.on_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)
        self.bind("<Control-o>", lambda e: self.on_open())

    # --------------------------------------------------------------- toolbar
    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(6, 4))
        bar.pack(side="top", fill="x")
        ttk.Button(bar, text="Open File", command=self.on_open).pack(side="left")
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y",
                                                   padx=8)
        ttk.Button(bar, text="Export Excel", command=self.on_export_excel
                  ).pack(side="left")
        ttk.Button(bar, text="Export PDF", command=self.on_export_pdf
                  ).pack(side="left", padx=4)
        # Animated progress bar (hidden until needed)
        self.progress = ttk.Progressbar(bar, mode="indeterminate",
                                         length=120)
        self.progress.pack(side="left", padx=(12, 0))

    # ----------------------------------------------------------------- main
    def _build_main(self) -> None:
        """Build the horizontal split: control panel (left) + notebook (right)."""
        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=6, pady=4)

        self._build_left_panel(body)
        self._build_notebook(body)

    # --------------------------------------------------------- left panel
    def _build_left_panel(self, parent) -> None:
        panel = ttk.Labelframe(parent, text="Controls", padding=8)
        parent.add(panel, weight=0)
        panel.columnconfigure(0, weight=1)

        row = 0

        # --- Data source info ---
        ttk.Label(panel, text="Data Source", font=("Segoe UI", 10, "bold")
                 ).grid(row=row, column=0, sticky="w", pady=(0, 4))
        row += 1
        self.source_label = ttk.Label(panel, text="No file loaded",
                                      foreground="#666")
        self.source_label.grid(row=row, column=0, sticky="w")
        row += 1

        ttk.Separator(panel, orient="horizontal").grid(row=row, column=0,
                                                       sticky="ew", pady=8)
        row += 1

        # --- Filter section ---
        ttk.Label(panel, text="Filter", font=("Segoe UI", 10, "bold")
                 ).grid(row=row, column=0, sticky="w")
        row += 1
        self.filter_col = ttk.Combobox(panel, state="readonly")
        self.filter_col.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        self.filter_op = ttk.Combobox(
            panel, state="readonly",
            values=["==", "!=", ">", ">=", "<", "<=", "contains"])
        self.filter_op.current(0)
        self.filter_op.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        self.filter_val = ttk.Entry(panel)
        self.filter_val.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        btns = ttk.Frame(panel)
        btns.grid(row=row, column=0, sticky="ew", pady=4)
        ttk.Button(btns, text="Apply", command=self.apply_filter).pack(
            side="left", expand=True, fill="x")
        ttk.Button(btns, text="Reset", command=self.reset_filter).pack(
            side="left", expand=True, fill="x", padx=(4, 0))
        row += 1

        ttk.Separator(panel, orient="horizontal").grid(row=row, column=0,
                                                       sticky="ew", pady=8)
        row += 1

        # --- Pivot section ---
        row = self._build_pivot_section(panel, row)

        ttk.Separator(panel, orient="horizontal").grid(row=row, column=0,
                                                       sticky="ew", pady=8)
        row += 1

        # --- Chart section ---
        row = self._build_chart_section(panel, row)

        ttk.Separator(panel, orient="horizontal").grid(row=row, column=0,
                                                       sticky="ew", pady=8)
        row += 1

        # --- Analysis / ML section ---
        self._build_analysis_section(panel, row)

    def _build_pivot_section(self, panel, row) -> int:
        """Build the pivot-table controls.  Returns the next free grid row."""
        ttk.Label(panel, text="Pivot Table", font=("Segoe UI", 10, "bold")
                 ).grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Label(panel, text="Rows:").grid(row=row, column=0, sticky="w")
        row += 1
        self.pivot_index = ttk.Combobox(panel, state="readonly")
        self.pivot_index.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="Columns (optional):").grid(
            row=row, column=0, sticky="w")
        row += 1
        self.pivot_cols = ttk.Combobox(panel, state="readonly")
        self.pivot_cols.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="Values:").grid(row=row, column=0, sticky="w")
        row += 1
        self.pivot_values = ttk.Combobox(panel, state="readonly")
        self.pivot_values.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="Aggregation:").grid(row=row, column=0, sticky="w")
        row += 1
        self.pivot_agg = ttk.Combobox(panel, state="readonly", values=AGG_FUNCS)
        self.pivot_agg.current(0)
        self.pivot_agg.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Button(panel, text="Build Pivot", command=self.run_pivot).grid(
            row=row, column=0, sticky="ew", pady=4)
        return row + 1

    def _build_chart_section(self, panel, row) -> int:
        """Build the chart controls.  Returns the next free grid row."""
        ttk.Label(panel, text="Chart", font=("Segoe UI", 10, "bold")
                 ).grid(row=row, column=0, sticky="w")
        row += 1
        self.chart_type = ttk.Combobox(
            panel, state="readonly", values=CHART_TYPES)
        self.chart_type.current(0)
        self.chart_type.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="X axis:").grid(row=row, column=0, sticky="w")
        row += 1
        self.chart_x = ttk.Combobox(panel, state="readonly")
        self.chart_x.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="Y axis:").grid(row=row, column=0, sticky="w")
        row += 1
        self.chart_y = ttk.Combobox(panel, state="readonly")
        self.chart_y.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Button(panel, text="Draw Chart", command=self.make_chart).grid(
            row=row, column=0, sticky="ew", pady=4)
        return row + 1

    def _build_analysis_section(self, panel, row) -> None:
        """Build the statistics / ML controls at the bottom of the panel."""
        ttk.Label(panel, text="Analysis & ML", font=("Segoe UI", 10, "bold")
                 ).grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Button(panel, text="Summary Statistics",
                   command=self.run_describe).grid(row=row, column=0,
                                                   sticky="ew", pady=2)
        row += 1
        ttk.Button(panel, text="Correlation Matrix",
                   command=self.run_correlation).grid(row=row, column=0,
                                                       sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="Regression  X:").grid(row=row, column=0,
                                                     sticky="w")
        row += 1
        self.reg_x = ttk.Combobox(panel, state="readonly")
        self.reg_x.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="Regression  Y:").grid(row=row, column=0,
                                                     sticky="w")
        row += 1
        self.reg_y = ttk.Combobox(panel, state="readonly")
        self.reg_y.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Button(panel, text="Run Regression",
                   command=self.run_regression).grid(row=row, column=0,
                                                     sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="K-means columns:").grid(row=row, column=0,
                                                        sticky="w")
        row += 1
        self.km_cols = ttk.Combobox(panel, state="readonly")
        self.km_cols.grid(row=row, column=0, sticky="ew", pady=2)
        row += 1
        ttk.Label(panel, text="K (clusters):").grid(row=row, column=0,
                                                    sticky="w")
        row += 1
        self.km_k = tk.IntVar(value=3)
        ttk.Spinbox(panel, from_=2, to=10, textvariable=self.km_k,
                    width=8).grid(row=row, column=0, sticky="w", pady=2)
        row += 1
        ttk.Button(panel, text="Run K-means",
                   command=self.run_kmeans).grid(row=row, column=0,
                                                 sticky="ew", pady=2)

    # ------------------------------------------------------------- notebook
    def _build_notebook(self, parent) -> None:
        self.notebook = ttk.Notebook(parent)
        parent.add(self.notebook, weight=3)

        # --- Data tab: paginated Treeview ---
        self.data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.data_tab, text="Data")
        self._build_data_tab(self.data_tab)

        # --- Summary tab: Treeview for describe() / correlation ---
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text="Summary")
        self._build_result_tab(self.summary_tab, "summary_tree")

        # --- Charts tab: matplotlib canvas ---
        self.chart_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_tab, text="Charts")
        self._build_chart_tab(self.chart_tab)

        # --- Pivot tab ---
        self.pivot_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pivot_tab, text="Pivot")
        self._build_result_tab(self.pivot_tab, "pivot_tree")

        # --- ML tab ---
        self.ml_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.ml_tab, text="ML")
        self._build_result_tab(self.ml_tab, "ml_tree")

    def _build_data_tab(self, parent) -> None:
        """Paginated table: a Treeview plus prev/next page controls."""
        top = ttk.Frame(parent)
        top.pack(side="top", fill="x", padx=4, pady=4)
        ttk.Button(top, text="< Prev", command=self.prev_page).pack(
            side="left")
        self.page_label = ttk.Label(top, text="Page 0 / 0")
        self.page_label.pack(side="left", padx=10)
        ttk.Button(top, text="Next >", command=self.next_page).pack(side="left")

        # Treeview inside a scrollable frame.
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.data_tree = ttk.Treeview(tree_frame, show="headings")
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal",
                                command=self.data_tree.xview)
        yscroll = ttk.Scrollbar(tree_frame, orient="vertical",
                                command=self.data_tree.yview)
        self.data_tree.configure(xscrollcommand=xscroll.set,
                                 yscrollcommand=yscroll.set)
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

    def _build_result_tab(self, parent, attr_name: str) -> None:
        """A generic read-only Treeview used by Summary / Pivot / ML tabs."""
        tree = ttk.Treeview(parent, show="headings")
        xs = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        ys = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        tree.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        setattr(self, attr_name, tree)

    def _build_chart_tab(self, parent) -> None:
        """Embed a matplotlib Figure in the Charts tab."""
        self.chart_figure = Figure(figsize=(7, 4.5), dpi=100)
        self.chart_canvas = FigureCanvasTkAgg(self.chart_figure, parent)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.current_chart_figure = self.chart_figure

    # ------------------------------------------------------------ status bar
    def _build_statusbar(self) -> None:
        bar = ttk.Frame(self, relief="sunken", padding=(6, 2))
        bar.pack(side="bottom", fill="x")
        # Pulsing status indicator dot
        self.status_dot = tk.Canvas(bar, width=14, height=14,
                                    highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 6))
        self._dot_state = 0
        # Typewriter status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(bar, textvariable=self.status_var,
                                      font=("Consolas", 10))
        self.status_label.pack(side="left")
        self.rowcount_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.rowcount_var).pack(side="right")
        # Loading spinner canvas (hidden by default)
        self.spinner_canvas = tk.Canvas(bar, width=20, height=20,
                                        highlightthickness=0)
        # Not packed until loading starts
        self._start_pulse()

    # --------------------------------------------------------------- helpers
    def _set_status(self, msg: str) -> None:
        """Update the bottom status bar with a typewriter animation."""
        # Cancel any pending typewriter frame
        if self._tw_after_id is not None:
            self.after_cancel(self._tw_after_id)
            self._tw_after_id = None
        self._tw_queue = msg
        self._tw_pos = 0
        self.status_var.set("")
        self._typewriter_step()

    def _typewriter_step(self) -> None:
        """Reveal one more character of the queued status message."""
        if self._tw_pos < len(self._tw_queue):
            self._tw_pos += 1
            self.status_var.set(self._tw_queue[:self._tw_pos])
            # Vary speed: faster for long messages
            delay = 12 if len(self._tw_queue) > 40 else 25
            self._tw_after_id = self.after(delay, self._typewriter_step)
        else:
            self._tw_after_id = None

    # --------------------------------------------------- pulsing indicator
    def _start_pulse(self) -> None:
        """Begin the pulsing status-dot animation loop."""
        self._pulse_step()

    def _pulse_step(self) -> None:
        """Draw one frame of the pulsing indicator."""
        self.status_dot.delete("all")
        t = self._dot_state
        # Three-phase colour: green=ready, blue=working, red=error
        if self._is_loading:
            base = (33, 150, 243)       # blue
        elif "error" in self.status_var.get().lower() or \
             "fail" in self.status_var.get().lower():
            base = (244, 67, 54)       # red
        else:
            base = (76, 175, 80)       # green
        # Pulsing alpha via sine wave
        pulse = 0.5 + 0.5 * math.sin(t * 0.15)
        r = 3 + 3 * pulse
        # Outer glow ring
        for ring in range(3, 0, -1):
            alpha = int(60 * pulse / ring)
            color = self._rgba(base[0], base[1], base[2], alpha)
            self.status_dot.create_oval(7 - r - ring*2, 7 - r - ring*2,
                                        7 + r + ring*2, 7 + r + ring*2,
                                        fill=color, outline="")
        # Core dot
        core = self._rgba(base[0], base[1], base[2], 255)
        self.status_dot.create_oval(7 - r, 7 - r, 7 + r, 7 + r,
                                    fill=core, outline="")
        self._dot_state += 1
        self._pulse_after_id = self.after(60, self._pulse_step)

    @staticmethod
    def _rgba(r: int, g: int, b: int, a: int) -> str:
        """Convert RGB + alpha to a Tk color string."""
        # Tk Canvas doesn't support alpha; blend with the background (#f0f0f0)
        bg_r, bg_g, bg_b = 240, 240, 240
        ratio = a / 255.0
        mr = int(r * ratio + bg_r * (1 - ratio))
        mg = int(g * ratio + bg_g * (1 - ratio))
        mb = int(b * ratio + bg_b * (1 - ratio))
        return f"#{mr:02x}{mg:02x}{mb:02x}"

    # --------------------------------------------------- loading spinner
    def _show_loading(self) -> None:
        """Show the animated loading spinner in the status bar."""
        self._is_loading = True
        self.spinner_canvas.pack(side="left", padx=(8, 0))
        self.progress.start(10)
        self._animate_spinner()

    def _hide_loading(self) -> None:
        """Hide the loading spinner."""
        self._is_loading = False
        self.spinner_canvas.pack_forget()
        self.progress.stop()
        if self._loading_after_id is not None:
            self.after_cancel(self._loading_after_id)
            self._loading_after_id = None

    def _animate_spinner(self) -> None:
        """Draw one frame of the rotating arc spinner."""
        if not self._is_loading:
            return
        self.spinner_canvas.delete("all")
        cx, cy = 10, 10
        self._loading_angle = (self._loading_angle + 15) % 360
        # Draw 8 arc segments with fading opacity
        for i in range(8):
            angle = self._loading_angle + i * 45
            alpha_ratio = 1.0 - (i / 8.0)
            # Blend from blue to background
            r = int(33 * alpha_ratio + 240 * (1 - alpha_ratio))
            g = int(150 * alpha_ratio + 240 * (1 - alpha_ratio))
            b = int(243 * alpha_ratio + 240 * (1 - alpha_ratio))
            color = f"#{r:02x}{g:02x}{b:02x}"
            rad = math.radians(angle)
            x1 = cx + 3 * math.cos(rad)
            y1 = cy + 3 * math.sin(rad)
            x2 = cx + 8 * math.cos(rad)
            y2 = cy + 8 * math.sin(rad)
            self.spinner_canvas.create_line(x1, y1, x2, y2,
                                            fill=color, width=2,
                                            capstyle="round")
        self._loading_after_id = self.after(50, self._animate_spinner)

    # --------------------------------------------------- progress helpers
    def _show_progress(self) -> None:
        """Start the indeterminate progress bar animation."""
        self.progress.start(10)

    def _hide_progress(self) -> None:
        """Stop the progress bar animation."""
        self.progress.stop()

    def _require_data(self) -> bool:
        """Return True if data is loaded, else warn the user."""
        if self.view_df is None:
            messagebox.showwarning("No data", "Open a CSV or Excel file first.")
            return False
        return True

    def _populate_column_dropdowns(self) -> None:
        """Fill every column combobox with the current DataFrame's columns."""
        if self.df is None:
            return
        cols = list(self.df.columns)
        for combo in (self.filter_col, self.pivot_index, self.pivot_cols,
                      self.pivot_values, self.chart_x, self.chart_y,
                      self.reg_x, self.reg_y, self.km_cols):
            combo["values"] = cols
            if combo["values"]:
                combo.current(0)

    # --------------------------------------------------------- file handling
    def on_open(self) -> None:
        """Show a file dialog and start loading the chosen file in a thread."""
        path = filedialog.askopenfilename(
            title="Open data file",
            filetypes=[("Data files", "*.csv *.xlsx *.xlsm *.xls *.tsv *.txt"),
                       ("All files", "*.*")])
        if not path:
            return
        self._set_status(f"Loading {os.path.basename(path)} ...")
        self._show_loading()
        data_loader.load_file_async(
            path, on_done=self._load_done, on_error=self._load_error,
            on_progress=lambda m: self.after(0, lambda: self._set_status(m)))
        self._current_path = path

    def _load_done(self, df: pd.DataFrame) -> None:
        """Called (from the worker thread) when loading succeeds."""
        # Schedule UI updates on the main thread.
        self.after(0, lambda: self._apply_loaded_data(df))

    def _load_error(self, exc: BaseException) -> None:
        """Called (from the worker thread) when loading fails."""
        self.after(0, lambda: self._hide_loading())
        self.after(0, lambda: messagebox.showerror(
            "Load error", str(exc)))
        self.after(0, lambda: self._set_status("Load failed"))

    def _apply_loaded_data(self, df: pd.DataFrame) -> None:
        """Store the loaded DataFrame and refresh the UI on the main thread."""
        self._hide_loading()
        self.df = df
        self.view_df = df
        self.page = 0
        self.chart_figures.clear()
        self._populate_column_dropdowns()
        self.source_label.config(
            text=f"{os.path.basename(self._current_path)}\n"
                 f"{len(df):,} rows x {len(df.columns)} cols")
        self.refresh_table()
        self._set_status(f"Loaded {len(df):,} rows")
        self.rowcount_var.set(f"{len(df):,} rows")

    # ------------------------------------------------------- data table view
    def refresh_table(self) -> None:
        """Rebuild the Data tab Treeview for the current page."""
        if self.view_df is None:
            return
        self._render_page()

    def _render_page(self) -> None:
        """Draw one page of rows into the Data tab Treeview with stagger."""
        # Cancel any pending row animations
        for aid in self._row_after_ids:
            try:
                self.after_cancel(aid)
            except Exception:
                pass
        self._row_after_ids.clear()

        tree = self.data_tree
        # Clear existing columns and rows.
        tree.delete(*tree.get_children())
        tree["columns"] = []

        df = self.view_df
        cols = list(df.columns)
        tree["columns"] = cols
        for c in cols:
            tree.heading(c, text=str(c))
            tree.column(c, width=120, stretch=False)

        # Slice the DataFrame to the current page.
        start = self.page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_df = df.iloc[start:end]

        # Stagger row insertion for a smooth reveal effect
        row_data = []
        for _, row in page_df.iterrows():
            values = ["" if pd.isna(v) else v for v in row.tolist()]
            row_data.append(values)

        # Insert rows in small batches with a delay for animation
        batch_size = 50
        total = len(row_data)

        def insert_batch(batch_idx: int) -> None:
            offset = batch_idx * batch_size
            if offset >= total:
                return
            batch = row_data[offset:offset + batch_size]
            for values in batch:
                tree.insert("", "end", values=values)
            if offset + batch_size < total:
                aid = self.after(15, lambda: insert_batch(batch_idx + 1))
                self._row_after_ids.append(aid)

        insert_batch(0)

        total_pages = max(1, (len(df) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.config(
            text=f"Page {self.page + 1} / {total_pages}  "
                 f"(rows {start + 1}-{min(end, len(df))} of {len(df):,})")

    def next_page(self) -> None:
        if self.view_df is None:
            return
        max_page = max(0, (len(self.view_df) - 1) // PAGE_SIZE)
        if self.page < max_page:
            self.page += 1
            self._render_page()

    def prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self._render_page()

    def _show_df_in_tree(self, tree: ttk.Treeview, df: pd.DataFrame) -> None:
        """Render an arbitrary DataFrame into a result-tab Treeview."""
        tree.delete(*tree.get_children())
        tree["columns"] = []
        if df is None or df.empty:
            return
        cols = [str(c) for c in df.columns]
        tree["columns"] = cols
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110, stretch=False)
        for _, row in df.head(5000).iterrows():
            values = ["" if pd.isna(v) else v for v in row.tolist()]
            tree.insert("", "end", values=values)

    # --------------------------------------------------------------- filter
    def apply_filter(self) -> None:
        """Apply the user's filter to the loaded data and refresh the table."""
        if not self._require_data():
            return
        col = self.filter_col.get()
        op = self.filter_op.get()
        val = self.filter_val.get()
        if not col:
            messagebox.showwarning("Filter", "Choose a column to filter on.")
            return
        self._show_progress()
        self._set_status("Filtering data ...")
        try:
            self.view_df = analysis.filter_data(self.df, col, op, val)
        except Exception as exc:  # noqa: BLE001
            self._hide_progress()
            messagebox.showerror("Filter error", str(exc))
            return
        self._hide_progress()
        self.page = 0
        self.refresh_table()
        self._set_status(f"Filter applied: {len(self.view_df):,} rows")
        self.rowcount_var.set(f"{len(self.view_df):,} rows (filtered)")

    def reset_filter(self) -> None:
        """Clear any active filter and show the full dataset again."""
        if self.df is None:
            return
        self.view_df = self.df
        self.page = 0
        self.refresh_table()
        self._set_status("Filter reset")
        self.rowcount_var.set(f"{len(self.df):,} rows")

    # ---------------------------------------------------------------- pivot
    def run_pivot(self) -> None:
        """Build a pivot table and show it in the Pivot tab."""
        if not self._require_data():
            return
        index = self.pivot_index.get()
        cols = self.pivot_cols.get() or None
        values = self.pivot_values.get()
        agg = self.pivot_agg.get()
        if not index or not values:
            messagebox.showwarning("Pivot", "Select Rows and Values columns.")
            return
        self._show_progress()
        self._set_status("Building pivot table ...")
        try:
            result = analysis.pivot_table(
                self.view_df, index, cols, values, agg)
        except Exception as exc:  # noqa: BLE001
            self._hide_progress()
            messagebox.showerror("Pivot error", str(exc))
            return
        self._hide_progress()
        self._show_df_in_tree(self.pivot_tree, result)
        self.notebook.select(self.pivot_tab)
        self._set_status(f"Pivot built: {len(result)} rows")

    # ---------------------------------------------------------------- chart
    def make_chart(self) -> None:
        """Render the selected chart type in the Charts tab with animation."""
        if not self._require_data():
            return
        x_col = self.chart_x.get()
        y_col = self.chart_y.get()
        chart_type = self.chart_type.get()
        if not x_col or not y_col:
            messagebox.showwarning("Chart", "Select X and Y columns.")
            return
        try:
            charts.create_chart(
                self.chart_figure, chart_type, x_col, [y_col],
                self.view_df, title=f"{chart_type.capitalize()}: "
                                    f"{y_col} vs {x_col}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Chart error", str(exc))
            return
        # Animated chart reveal: progressive alpha fade-in
        self._animate_chart_reveal()
        self.chart_figures = [self.chart_figure]
        self.notebook.select(self.chart_tab)
        self._set_status(f"{chart_type} chart drawn")

    def _animate_chart_reveal(self) -> None:
        """Progressively fade in the chart canvas for a smooth reveal."""
        if self._chart_after_id is not None:
            self.after_cancel(self._chart_after_id)
        self._chart_alpha = 0.0

        def fade_step() -> None:
            self._chart_alpha = min(1.0, self._chart_alpha + 0.15)
            # Set figure alpha via patch
            self.chart_figure.patch.set_alpha(self._chart_alpha)
            for ax in self.chart_figure.get_axes():
                for artist in ax.get_children():
                    try:
                        old_alpha = artist.get_alpha()
                        if old_alpha is None:
                            artist.set_alpha(self._chart_alpha)
                        else:
                            artist.set_alpha(min(old_alpha, self._chart_alpha))
                    except Exception:
                        pass
            self.chart_canvas.draw()
            if self._chart_alpha < 1.0:
                self._chart_after_id = self.after(30, fade_step)
            else:
                self._chart_after_id = None

        fade_step()

    # ------------------------------------------------------------- analysis
    def run_describe(self) -> None:
        """Show descriptive statistics in the Summary tab."""
        if not self._require_data():
            return
        self._show_progress()
        self._set_status("Computing summary statistics ...")
        result = analysis.describe(self.view_df)
        self._hide_progress()
        self._show_df_in_tree(self.summary_tree, result)
        self.notebook.select(self.summary_tab)
        self._set_status("Summary statistics generated")

    def run_correlation(self) -> None:
        """Show the correlation matrix in the Summary tab."""
        if not self._require_data():
            return
        self._show_progress()
        self._set_status("Computing correlation matrix ...")
        corr = analysis.correlation(self.view_df)
        self._hide_progress()
        if corr.empty:
            messagebox.showinfo("Correlation",
                                "No numeric columns found.")
            return
        self._show_df_in_tree(self.summary_tree, corr.reset_index())
        self.notebook.select(self.summary_tab)
        self._set_status("Correlation matrix generated")

    def run_regression(self) -> None:
        """Run linear regression and show results in the ML tab."""
        if not self._require_data():
            return
        x_col = self.reg_x.get()
        y_col = self.reg_y.get()
        if not x_col or not y_col:
            messagebox.showwarning("Regression", "Select X and Y columns.")
            return
        self._show_progress()
        self._set_status("Running linear regression ...")
        try:
            res = analysis.linear_regression(self.view_df, x_col, y_col)
        except Exception as exc:  # noqa: BLE001
            self._hide_progress()
            messagebox.showerror("Regression error", str(exc))
            return
        self._hide_progress()
        # Present the coefficients as a small table.
        result_df = pd.DataFrame([{
            "X": x_col, "Y": y_col,
            "slope": round(res["slope"], 6),
            "intercept": round(res["intercept"], 6),
            "r_squared": round(res["r_squared"], 6),
        }])
        self._show_df_in_tree(self.ml_tree, result_df)
        self.notebook.select(self.ml_tab)
        self._set_status(
            f"Regression: R^2={res['r_squared']:.4f}")

    def run_kmeans(self) -> None:
        """Run k-means clustering and show labelled rows in the ML tab."""
        if not self._require_data():
            return
        cols_str = self.km_cols.get()
        if not cols_str:
            messagebox.showwarning("K-means", "Select a numeric column.")
            return
        k = int(self.km_k.get())
        self._show_progress()
        self._set_status(f"Running K-means (k={k}) ...")
        try:
            result = analysis.kmeans(self.view_df, [cols_str], k=k)
        except Exception as exc:  # noqa: BLE001
            self._hide_progress()
            messagebox.showerror("K-means error", str(exc))
            return
        self._hide_progress()
        self._show_df_in_tree(self.ml_tree, result)
        self.notebook.select(self.ml_tab)
        self._set_status(f"K-means done: {k} clusters, {len(result)} rows")

    # --------------------------------------------------------------- export
    def on_export_excel(self) -> None:
        """Export the currently visible (filtered) data to a formatted .xlsx."""
        if not self._require_data():
            return
        path = filedialog.asksaveasfilename(
            title="Export to Excel", defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        self._show_progress()
        self._set_status("Exporting to Excel ...")
        try:
            exporter.export_excel(self.view_df, path)
        except Exception as exc:  # noqa: BLE001
            self._hide_progress()
            messagebox.showerror("Export error", str(exc))
            return
        self._hide_progress()
        self._set_status(f"Exported Excel: {path}")

    def on_export_pdf(self) -> None:
        """Export a PDF report with summary, data preview and charts."""
        if not self._require_data():
            return
        path = filedialog.asksaveasfilename(
            title="Export to PDF", defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        self._show_progress()
        self._set_status("Exporting to PDF ...")
        try:
            summary = analysis.describe(self.view_df)
            exporter.export_pdf(
                self.view_df, path,
                figures=self.chart_figures or None,
                summary=summary)
        except Exception as exc:  # noqa: BLE001
            self._hide_progress()
            messagebox.showerror("Export error", str(exc))
            return
        self._hide_progress()
        self._set_status(f"Exported PDF: {path}")

    # ----------------------------------------------------------------- help
    def on_about(self) -> None:
        """Show a small About dialog."""
        messagebox.showinfo(
            "About DataFlow Analyzer",
            "DataFlow Analyzer v1.0.0\n\n"
            "A standalone desktop tool for everyday data analysis:\n"
            "  - Import CSV / Excel (up to 500k rows)\n"
            "  - Filter, pivot and summarise\n"
            "  - Bar / line / scatter charts\n"
            "  - Linear regression & k-means clustering\n"
            "  - Export to Excel and PDF\n\n"
            "Built with Python, Tkinter, pandas and matplotlib.\n\n"
            "Developer: Rohit Gupta")


def main() -> None:
    """Application entry point - create the window and start the Tk loop."""
    app = DataFlowApp()
    app.mainloop()


if __name__ == "__main__":
    main()









