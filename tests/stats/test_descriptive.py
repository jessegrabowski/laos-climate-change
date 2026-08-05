import numpy as np
import pandas as pd
import pytest

from climate_risk.stats.descriptive import descriptive_stats_function, nan_or_sum


def test_all_missing_stays_missing():
    """A country-year with no observations must not become a zero disaster count."""
    assert np.isnan(nan_or_sum(np.array([np.nan, np.nan])))


def test_partial_missing_sums_the_observed_values():
    assert nan_or_sum(np.array([1.0, np.nan, 2.0])) == 3.0


def test_all_zero_is_a_real_zero():
    assert nan_or_sum(np.array([0.0, 0.0])) == 0.0


@pytest.fixture
def frame():
    rng = np.random.default_rng(0)
    return pd.DataFrame({"a": rng.normal(size=50), "b": rng.gamma(2.0, size=50)})


def test_the_summary_carries_kurtosis_and_skewness(frame):
    """describe() supplies neither, and both label rows the caller reads positionally."""
    summary = descriptive_stats_function(frame, ["a", "b"])

    assert {"kurtosis", "skewness"} < set(summary.index)
    assert summary.loc["kurtosis", "a"] == pytest.approx(frame["a"].kurt())
    assert summary.loc["skewness", "b"] == pytest.approx(frame["b"].skew())
