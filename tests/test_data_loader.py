"""Unit tests for the data loader and exporter.

Run with::

    py -m pytest tests/test_data_loader.py -v
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from dataflow import data_loader, exporter


class TestDataLoader(unittest.TestCase):
    def test_load_csv(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False,
                                         mode="w", newline="") as f:
            df.to_csv(f.name, index=False)
            path = f.name
        try:
            loaded = data_loader.load_file(path)
            self.assertEqual(len(loaded), 3)
            self.assertEqual(list(loaded.columns), ["a", "b"])
        finally:
            os.remove(path)

    def test_unsupported_extension(self):
        # Create a real file with an unsupported extension so the existence
        # check passes and the extension check raises ValueError.
        with tempfile.NamedTemporaryFile(suffix=".abc", delete=False) as f:
            f.write(b"hello")
            path = f.name
        try:
            with self.assertRaises(ValueError):
                data_loader.load_file(path)
        finally:
            os.remove(path)


class TestExporter(unittest.TestCase):
    def test_export_excel(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.xlsx")
            exporter.export_excel(df, path)
            self.assertTrue(os.path.isfile(path))
            # Re-read to confirm round-trip.
            back = pd.read_excel(path)
            self.assertEqual(len(back), 2)

    def test_export_pdf(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.pdf")
            exporter.export_pdf(df, path)
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 100)


if __name__ == "__main__":
    unittest.main()
