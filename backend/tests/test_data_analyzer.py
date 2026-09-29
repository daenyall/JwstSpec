import pytest
import numpy as np

from DataAnalyzer import DataAnalyzer


def test_calculate_temporal_metrics():
    analyzer = DataAnalyzer()

    times = np.array([
        0.0,
        1.0,
        2.0,
        3.0,
        4.0,
        5.0
    ])

    detrended = np.array([
        1.00,
        1.00,
        0.98,
        0.98,
        1.01,
        1.01
    ])

    metrics = analyzer._calculate_temporal_metrics(
        detrended,
        times,
        transit_start=2.0,
        transit_end=3.0
    )

    assert metrics is not None

    assert metrics["oot_scatter"] == pytest.approx(
        0.007413
    )

    assert metrics["baseline_mismatch"] == pytest.approx(
        0.01
    )