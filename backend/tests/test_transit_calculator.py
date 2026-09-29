import pytest

from TransitCalculator import TransitCalculator


def test_calculate_transit_window_selects_nearest_transit():
    calculator = TransitCalculator()

    t0 = 2459000.5
    period_days = 2.0
    duration_hours = 4.0
    observation_time = 59004.2

    midpoint, start, end, duration = calculator.calculate_transit_window(
        t0,
        period_days,
        duration_hours,
        observation_time
    )

    assert midpoint == pytest.approx(59004.0)
    assert start == pytest.approx(59003.9166666667)
    assert end == pytest.approx(59004.0833333333)
    assert duration == pytest.approx(4.0)