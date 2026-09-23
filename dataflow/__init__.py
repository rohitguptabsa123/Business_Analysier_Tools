"""DataFlow Analyzer - a standalone desktop data-analysis application.

Built with Python + Tkinter for non-technical business users.  See the
package modules for the implementation:

    data_loader  - import CSV / Excel files
    analysis     - filtering, pivot tables, statistics, ML routines
    charts       - bar / line / scatter chart rendering
    exporter     - Excel and PDF report export
    app          - the Tkinter user interface

Run the application from the project root with::

    py run.py

Developer: Rohit Gupta
"""

__version__ = "1.0.0"
__author__ = "Rohit Gupta"
__all__ = ["app", "analysis", "charts", "data_loader", "exporter"]
