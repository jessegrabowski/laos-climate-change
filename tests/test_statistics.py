import numpy as np

from climate_risk.statistics import nan_or_sum


def test_all_missing_stays_missing():
    """A country-year with no observations must not become a zero disaster count."""
    assert np.isnan(nan_or_sum(np.array([np.nan, np.nan])))


def test_partial_missing_sums_the_observed_values():
    assert nan_or_sum(np.array([1.0, np.nan, 2.0])) == 3.0


def test_all_zero_is_a_real_zero():
    assert nan_or_sum(np.array([0.0, 0.0])) == 0.0
