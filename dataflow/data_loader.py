"""Data loading module for DataFlow Analyzer.

Responsibilities
----------------
* Detect file type from the extension (CSV or Excel).
* Read the file into a :class:`pandas.DataFrame` using the appropriate parser.
* Run the read in a background thread so the Tkinter UI stays responsive,
  reporting progress back via a callback.

The module deliberately keeps the public surface tiny: :func:`load_file` is the
single entry point used by the GUI.
"""

from __future__ import annotations

import os
import threading
from typing import Callable, Optional

import pandas as pd

# File extensions we understand.  Excel covers the legacy .xls and the modern
# .xlsx / .xlsm formats (the latter via openpyxl).
EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}
CSV_EXTENSIONS = {".csv", ".tsv", ".txt"}


def load_file(path: str,
              progress: Optional[Callable[[str], None]] = None) -> pd.DataFrame:
    """Synchronously load *path* into a DataFrame.

    Parameters
    ----------
    path:
        Path to a CSV or Excel file.
    progress:
        Optional callback that receives human-readable status strings.  This
        is called before and after the read so callers can update a label.

    Returns
    -------
    pandas.DataFrame

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if progress:
        progress(f"Reading {os.path.basename(path)} ...")

    if ext in CSV_EXTENSIONS:
        # ``low_memory=False`` keeps type inference consistent for large files.
        # ``encoding`` falls back to latin-1 on decode errors so odd files do
        # not crash the import.
        try:
            df = pd.read_csv(path, low_memory=False, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, low_memory=False, encoding="latin-1")
    elif ext in EXCEL_EXTENSIONS:
        # openpyxl handles .xlsx/.xlsm; .xls needs xlrd (rare today).
        df = pd.read_excel(path, engine="openpyxl" if ext != ".xls" else None)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Use CSV or Excel (.xlsx/.xls).")

    if progress:
        progress(f"Loaded {len(df):,} rows x {len(df.columns)} columns")

    return df


def load_file_async(path: str,
                    on_done: Callable[[pd.DataFrame], None],
                    on_error: Callable[[BaseException], None],
                    on_progress: Optional[Callable[[str], None]] = None
                    ) -> threading.Thread:
    """Load *path* in a background thread.

    This is the variant the GUI uses so the event loop never blocks while a
    500k-row file is being parsed.  Exactly one of *on_done* / *on_error* is
    invoked when the read finishes.

    Parameters
    ----------
    path:
        File to load.
    on_done:
        Called with the resulting DataFrame on success.
    on_error:
        Called with the exception on failure.
    on_progress:
        Optional status callback (called from the worker thread).

    Returns
    -------
    threading.Thread
        The started worker thread (already running).
    """

    def _worker() -> None:
        try:
            df = load_file(path, progress=on_progress)
            on_done(df)
        except BaseException as exc:  # noqa: BLE001 - surface every error
            on_error(exc)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
