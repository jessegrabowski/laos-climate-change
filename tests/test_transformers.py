import re

import pandas as pd
import pytest

from climate_risk.transformers import Standardize


@pytest.fixture
def features():
    return pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0],
            "b": [10.0, 20.0, 30.0],
            "region_idx": [1.0, 2.0, 3.0],
            "name": ["x", "y", "z"],
        }
    )


def test_standardized_columns_are_added_not_replaced(features):
    """Callers index the original columns afterwards, so the source must survive."""
    transformed = Standardize().fit(features).transform(features)

    assert transformed["a"].tolist() == [1.0, 2.0, 3.0]
    assert "a__standardized" in transformed.columns


def test_standardizing_centres_and_scales(features):
    transformed = Standardize().fit(features).transform(features)

    assert transformed["a__standardized"].tolist() == pytest.approx([-1.0, 0.0, 1.0])


def test_index_columns_are_left_alone(features):
    """A `_idx` column is a model coordinate, not a feature; standardizing it corrupts the index."""
    transformed = Standardize().fit(features).transform(features)

    assert "region_idx__standardized" not in transformed.columns


def test_non_float_columns_are_left_alone(features):
    transformed = Standardize().fit(features).transform(features)

    assert "name__standardized" not in transformed.columns


def test_transforming_before_fitting_is_rejected(features):
    with pytest.raises(RuntimeError, match=re.escape("Must call `.fit")):
        Standardize().transform(features)


def test_statistics_applies_the_fitted_scaler_to_new_data(features):
    """Held-out data must use the training mean and scale, not its own."""
    transformer = Standardize().fit(features)

    shifted = transformer.transform(features.assign(a=features["a"] + 1.0))

    assert shifted["a__standardized"].tolist() == pytest.approx([0.0, 1.0, 2.0])
