import numpy as np
import pandas as pd
import pytest

from climate_risk.statistics import ADF_test_summary, make_var_names, nan_or_sum


def test_all_missing_stays_missing():
    """A country-year with no observations must not become a zero disaster count."""
    assert np.isnan(nan_or_sum(np.array([np.nan, np.nan])))


def test_partial_missing_sums_the_observed_values():
    assert nan_or_sum(np.array([1.0, np.nan, 2.0])) == 3.0


def test_all_zero_is_a_real_zero():
    assert nan_or_sum(np.array([0.0, 0.0])) == 0.0


@pytest.mark.parametrize(
    ("n_lags", "regression", "expected"),
    [
        (0, "n", ["L1.x"]),
        (1, "n", ["L1.x", "D1L1.x"]),
        (1, "c", ["L1.x", "D1L1.x", "Constant"]),
        (1, "ct", ["L1.x", "D1L1.x", "Constant", "Trend"]),
    ],
)
def test_var_names_follow_the_regression_terms(n_lags, regression, expected):
    """The names label ADF output columns positionally, so an extra or missing one misaligns them."""
    assert make_var_names("x", n_lags, regression) == expected


def test_missing_data_is_refused_by_default():
    """statsmodels would otherwise return a silent nan for the whole test."""
    with pytest.raises(ValueError, match="missing data"):
        ADF_test_summary(pd.DataFrame({"x": [1.0, np.nan, 3.0]}))
