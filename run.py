#!/usr/bin/env python3
"""Entry point for DataFlow Analyzer.

Run from the project root with::

    py run.py

This wrapper simply imports and launches the Tkinter application defined in
:mod:`dataflow.app`.
"""

from dataflow.app import main

if __name__ == "__main__":
    main()
