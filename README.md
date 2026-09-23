# DataFlow Analyzer

A standalone **desktop** data-analysis application for everyday business use.
Built with Python, Tkinter, pandas and matplotlib - no web server, no cloud,
no account required.

**Developer:** Rohit Gupta

> This project was built to the specification in the supplied Samsung Notes
> brief (`.sdocx`): a dedicated, installable desktop tool that loads structured
> data, explores it through filtering and pivot-style summaries, runs common
> statistical / machine-learning routines, and exports clean reports.

---

## Features

| Capability | Details |
|---|---|
| **Import** | CSV and Excel (`.xlsx` / `.xlsm` / `.xls`) up to 500k rows |
| **Explore** | Paginated data table, column filtering (`== != > >= < <= contains`) |
| **Summarise** | Pivot tables (rows x columns x values, 7 aggregation functions) |
| **Statistics** | Descriptive statistics, Pearson correlation matrix |
| **Machine learning** | Ordinary least-squares linear regression, k-means clustering |
| **Charts** | Bar, line and scatter (matplotlib, embedded in the app) |
| **Export** | Formatted Excel (`.xlsx`) and PDF reports (with charts + summary) |

The data table uses **pagination** (1 000 rows per page) so even a 500k-row
file never blocks the interface.  File loading runs in a **background thread**
so the UI stays responsive while large files parse.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.10+ (developed on 3.14) | Cross-platform, rich data ecosystem |
| GUI | Tkinter | Ships with CPython - zero install friction |
| Data | pandas + NumPy | Handles 500k rows comfortably |
| Charts | matplotlib | Bar / line / scatter, embeddable in Tkinter |
| Excel export | xlsxwriter | Formatted workbooks, auto-filters |
| PDF export | reportlab | Tables + embedded chart images |
| ML | NumPy (no scikit-learn) | Linear regression & k-means in ~50 lines |

---

## Installation

### Prerequisites
- **Python 3.10 or newer** (download from <https://python.org>).
  During installation on Windows, tick **"Add Python to PATH"**.
  Verify with:
  ```powershell
  py --version
  ```

### Install dependencies
```powershell
cd E:\WorkSpace\2209
py -m pip install -r requirements.txt
```

---

## Running the application

```powershell
cd E:\WorkSpace\2209
py run.py
```

The main window opens with an empty workspace.  Use **File -> Open** (or the
toolbar button, or `Ctrl+O`) to load a CSV / Excel file.

A sample dataset is included at `sample_data/sample_sales.csv`
(2 000 rows of sales data).  Generate a fresh copy with:
```powershell
py generate_sample.py
```

---

## Typical analysis workflow

1. **Open** a CSV or Excel file (`Ctrl+O`).  The Data tab shows the first
   1 000 rows; use **Prev / Next** to page through the rest.
2. **Filter** - in the left panel pick a column, an operator and a value,
   then click **Apply**.  Click **Reset** to clear the filter.
3. **Pivot** - choose Rows, (optional) Columns, Values and an aggregation
   function, then click **Build Pivot**.  Results appear in the Pivot tab.
4. **Chart** - pick a chart type (bar / line / scatter), an X column and a Y
   column, then click **Draw Chart**.  The chart appears in the Charts tab.
5. **Analyse** - click **Summary Statistics** or **Correlation Matrix**, or run
   **Regression** / **K-means** from the Analysis & ML section.
6. **Export** - use **Export Excel** or **Export PDF** to save the current
   (filtered) data and any charts you have drawn.

---

## Report generation

- **Excel** - writes the visible (filtered) data to a formatted `.xlsx` with a
  bold header row, frozen panes and an auto-filter.
- **PDF** - writes a multi-section report: title, summary statistics table,
  a 50-row data preview, and any charts drawn in the Charts tab.

---

## Project structure

```
2209/
├── dataflow/              # main application package
│   ├── __init__.py
│   ├── app.py             # Tkinter GUI (window, tabs, event handlers)
│   ├── data_loader.py     # CSV / Excel import (background thread)
│   ├── analysis.py        # filter, pivot, stats, regression, k-means
│   ├── charts.py          # bar / line / scatter rendering
│   └── exporter.py        # Excel + PDF export
├── tests/                 # unit tests (12 tests, all passing)
│   ├── test_analysis.py
│   └── test_data_loader.py
├── sample_data/
│   └── sample_sales.csv   # sample dataset for UAT
├── run.py                 # entry point
├── smoke_test.py          # headless end-to-end test (no GUI)
├── generate_sample.py     # regenerate the sample CSV
├── requirements.txt
└── README.md
```

---

## Testing

```powershell
# Unit tests (filter, pivot, stats, regression, k-means, loader, exporter)
py -m unittest discover -s tests -v

# Headless smoke test (loads sample data, runs every feature, exports files)
py smoke_test.py
```

All 12 unit tests pass.  The smoke test exercises the full pipeline end-to-end
(load -> filter -> pivot -> describe -> correlation -> regression -> k-means ->
chart -> Excel export -> PDF export).

---

## Building an installer (Windows)

To produce a standalone `.exe` that non-technical staff can install without
Python, use PyInstaller:

```powershell
py -m pip install pyinstaller
pyinstaller --onefile --windowed --name DataFlowAnalyzer run.py
```

The executable appears in `dist/DataFlowAnalyzer.exe`.  Bundle it with an
installer (e.g. Inno Setup) for a one-click Windows installer.

> macOS / Linux portability: Tkinter, pandas and matplotlib are all
> cross-platform, so the same code runs on macOS and Linux with no changes -
> only the Python dependencies need installing on each platform.

---

## Code documentation

Every module and public function has a docstring.  Key functions carry inline
comments explaining non-obvious steps (e.g. the closed-form least-squares
solution in `linear_regression`, the Lloyd's algorithm loop in `kmeans`, and
the pagination logic in `app._render_page`).

---

## Acceptance criteria status

| Criterion | Status |
|---|---|
| Import CSV and Excel up to 500k rows without crashes | OK (pandas + background thread + pagination) |
| At least 3 chart types (bar, line, scatter) | OK |
| Export to PDF and Excel matching on-screen formatting | OK |
| Code passes basic linting/tests with inline comments | OK (12 unit tests + smoke test) |
| Installable application (Windows first) | OK (PyInstaller instructions above) |
| Source code with clear build instructions | OK (this README) |
| Concise user guide | OK (this README) |

