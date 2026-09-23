"""Unit tests for the analysis module (filter, pivot, stats, ML).

Run with::

    py -m pytest tests/test_analysis.py -v

or without pytest::

    py -m unittest tests.test_analysis
"""

import os
import sys
import unittest

# Make the project root importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from dataflow import analysis


def _sample_df() -> pd.DataFrame:
    """A small reproducible DataFrame used across the tests."""
    return pd.DataFrame({
        "category": ["A", "A", "B", "B", "C", "C"],
        "region": ["N", "S", "N", "S", "N", "S"],
        "sales": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "qty": [1, 2, 3, 4, 5, 6],
    })


class TestFilter(unittest.TestCase):
    def test_numeric_gt(self):
        out = analysis.filter_data(_sample_df(), "sales", ">", "25")
        # sales = [10,20,30,40,50,60] -> four values above 25
        self.assertEqual(len(out), 4)
        self.assertTrue((out["sales"] > 25).all())

    def test_contains(self):
        out = analysis.filter_data(_sample_df(), "category", "contains", "a")
        # Only category "A" contains the letter 'a' (case-insensitive).
        self.assertEqual(set(out["category"]), {"A"})

    def test_equality(self):
        out = analysis.filter_data(_sample_df(), "region", "==", "N")
        self.assertEqual(len(out), 3)
        self.assertTrue((out["region"] == "N").all())


class TestPivot(unittest.TestCase):
    def test_pivot_mean(self):
        pv = analysis.pivot_table(_sample_df(), "category", "region",
                                  "sales", "mean")
        # Each category appears once per region present.
        self.assertIn("category", pv.columns)
        self.assertEqual(len(pv), 3)  # 3 categories


class TestStats(unittest.TestCase):
    def test_describe(self):
        desc = analysis.describe(_sample_df())
        self.assertIn("column", desc.columns)
        self.assertEqual(len(desc), 4)

    def test_correlation(self):
        corr = analysis.correlation(_sample_df())
        # sales and qty are perfectly correlated -> 1.0
        self.assertAlmostEqual(corr.loc["sales", "qty"], 1.0, places=6)


class TestRegression(unittest.TestCase):
    def test_perfect_fit(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]})
        res = analysis.linear_regression(df, "x", "y")
        self.assertAlmostEqual(res["slope"], 2.0, places=6)
        self.assertAlmostEqual(res["intercept"], 0.0, places=6)
        self.assertAlmostEqual(res["r_squared"], 1.0, places=6)


class TestKMeans(unittest.TestCase):
    def test_clusters_count(self):
        rng = np.random.default_rng(0)
        # Three well-separated blobs.
        a = rng.normal(0, 0.1, (20, 2))
        b = rng.normal(10, 0.1, (20, 2))
        c = rng.normal(20, 0.1, (20, 2))
        df = pd.DataFrame(np.vstack([a, b, c]), columns=["x", "y"])
        out = analysis.kmeans(df, ["x", "y"], k=3)
        self.assertEqual(out["cluster"].nunique(), 3)
        self.assertEqual(len(out), 60)


if __name__ == "__main__":
    unittest.main()
