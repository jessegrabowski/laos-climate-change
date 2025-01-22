from typing import Self

import pandas as pd
from sklearn.base import BaseEstimator, OneToOneFeatureMixin, TransformerMixin


class Standardize(OneToOneFeatureMixin, BaseEstimator, TransformerMixin):
    """GLM Transformer to center and scale features.

    Creates new columns with standardized features but ignores
    columns with suffix `_idx` or non-float columns. New columns
    receive the suffix `_standardized`.

    Examples
    --------
    Basic usage:

    .. code-block:: python

        import pandas as pd

        from rx_bonds.transformer import Standardize

        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "feature_with_suffix_idx": [1, 2, 3]
        }).astype(float)
        df["string_column"] = ["a", "b", "c"]

        transformer = Standardize()
        transformer.fit_transform(df)

        #      a    b  feature_with_suffix_idx string_column  a_standardized  b_standardized
        # 0  1.0  4.0                      1.0             a            -1.0            -1.0
        # 1  2.0  5.0                      2.0             b             0.0             0.0
        # 2  3.0  6.0                      3.0             c             1.0             1.0

    """

    def __init__(self):
        """Initialize GLM transformer."""
        self._mean_std_map = {}

    def fit(self, X: pd.DataFrame, y=None) -> Self:
        """Fit method

        Returns
        -------
        Self
            Saves state from the training data.
        """
        df = X
        self._mean_std_map = {
            feature: (float(df[feature].mean()), float(df[feature].std()))
            for feature in df.columns
            if df[feature].dtype.kind == "f"
        }
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform method returns mutated dataframe using saved state.
        """
        if len(self._mean_std_map) == 0:
            raise RuntimeError(
                "Must call `.fit(df)` on training data before transforming on new data."
            )

        df = df.copy()
        # TODO: Here and elsewhere, should avoid adding columns one by one.
        # This leads to pandas warnings at some threshold.
        for feature, (mean, std) in self._mean_std_map.items():
            if feature.endswith("_idx"):
                continue
            df[f"{feature}__standardized"] = (df[feature] - mean) / std

        return df
