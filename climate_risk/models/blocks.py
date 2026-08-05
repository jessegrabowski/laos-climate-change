from collections.abc import Sequence

import numpy as np
import numpy.typing as npt
import pandas as pd
import pymc as pm
import pytensor
import pytensor.tensor as pt

from pytensor.tensor import TensorVariable


def add_hierarchical_effect(
    name: str = "country",
    loc_mu: float = 0.0,
    loc_sigma: float = 1.0,
    scale_alpha: float = 2.0,
    scale_beta: float = 1.0,
    use_zerosum_offset: bool = False,
    group_dim: str | None = None,
) -> tuple[TensorVariable, TensorVariable, TensorVariable, TensorVariable]:
    """Adds a hierarchical effect to the active PyMC model.

    Parameters
    ----------
    name: str
        The name of the effect
    loc_mu: float
        The mean of the (Normal) location parameter
    loc_sigma: float
        The standard deviation of the (Normal) location parameter
    scale_alpha: float
        The alpha (rate) parameter of the (Gamma) scale parameter
    scale_beta: float
        The beta (shape) parameter of the (Gamma) scale parameter
    use_zerosum_offset: bool, default False
        If True, the offset is modeled as a ZeroSumNormal. Otherwise a Normal is used.
    group_dim: str
        Dimension of the group (e.g. 'ISO' for countries). Must be provided.

    Returns
    -------
    country_effect: TensorVariable
        The country effect
    country_effect_loc: TensorVariable
        The location parameter of the distribution over effects
    country_effect_scale: TensorVariable
        The scale parameter of the distribution over effects
    country_effect_offset: TensorVariable
        The offsets for each country from the overall group mean
    """
    if group_dim is None:
        raise ValueError("group_dim must be provided")

    with pm.modelcontext(None):
        country_effect_loc = pm.Normal(f"{name}_effect_loc", mu=loc_mu, sigma=loc_sigma)
        country_effect_scale = pm.Gamma(f"{name}_effect_scale", alpha=scale_alpha, beta=scale_beta)

        if use_zerosum_offset:
            country_effect_offset = pm.ZeroSumNormal(f"{name}_effect_offset", sigma=1, dims=group_dim)
        else:
            country_effect_offset = pm.Normal(f"{name}_effect_offset", sigma=1, dims=group_dim)
        country_effect = pm.Deterministic(
            f"{name}_effect",
            country_effect_loc + country_effect_scale * country_effect_offset,
            dims=group_dim,
        )

    return (
        country_effect,
        country_effect_loc,
        country_effect_scale,
        country_effect_offset,
    )


def add_data(
    features: list[str],
    df: pd.DataFrame,
    target: str | None = None,
    name: str | None = None,
    dims: Sequence[str] | str | None = None,
    dtype: npt.DTypeLike | None = None,
) -> TensorVariable | tuple[TensorVariable, TensorVariable]:
    """Add data to the active PyMC model.

    Parameters
    ----------
    features: list of str
        The features to include in the model. Each entry must be a column in the provided dataframe.
    df: pd.DataFrame
        The dataframe containing the data
    target: str, optional
        Column name to use for the targets. If not provided, no target data will be returned.
    name: str, optional
        If provided, the name will be appended to the name (e.g. X_name, Y_name)
    dims: Sequence of str, or str; optional
        Named dimensions to include on the data. If targets are requested, only the first dimension will be used for the
        targets (it is assumed to be the batch dimension)
    dtype: str, optional
        Data type to cast the data to. If not provided, the default data type defined by pytensor will be used.

    Returns
    -------
    X: TensorVariable
        The data tensor
    Y: TensorVariable
        The target tensor. Only returned if target is provided.
    """
    X_name = "X" if name is None else f"X_{name}"
    Y_name = "Y" if name is None else f"Y_{name}"

    if dtype is None:
        dtype = pytensor.config.floatX
    dtype = np.dtype(dtype)

    with pm.modelcontext(None):
        X = pm.Data(X_name, df[features].astype(dtype), dims=dims)

        if target is not None:
            Y = pm.Data(
                Y_name,
                df[target].astype(dtype),
                dims=dims[0] if dims is not None else dims,
            )
            return X, Y

    return X


def compute_center(X: TensorVariable | np.ndarray) -> np.ndarray:
    return (pt.max(X, axis=0) + pt.min(X, axis=0)).eval() / 2


def set_plotting_data(df: pd.DataFrame, features: list[str], ISO_list: list[str]) -> None:
    iso_idx = df["ISO"].apply(lambda x: ISO_list.index(x))

    pm.set_data(
        {
            "X_gp": df[["lat", "long"]],
            "Y": np.full(df.shape[0], 0),
            "ISO_idx": iso_idx,
            "X": df[features],
            "is_island": df["is_island"],
        },
        coords={"obs_idx": df.index.values},
    )
