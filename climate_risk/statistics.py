import geopandas as gpd
import numpy as np
import pandas as pd
import pymc as pm
import xarray as xr

from sklearn.preprocessing import StandardScaler as Standardize
from statsmodels.tsa.stattools import adfuller

from climate_risk.geo.crs import GEOGRAPHIC_CRS


def nan_or_sum(x):
    if np.isnan(x).all():
        return np.nan
    return np.nansum(x)


# Descriptive stats function
def descriptive_stats_function(df, varlist):
    # Sum stats
    sum_stats = df[varlist].describe()
    # Kurtosis
    kurtosis = pd.Series()
    for x in varlist:
        kurtosis[str(x)] = df[str(x)].kurt()
    kurtosis = kurtosis.to_frame().rename(columns={0: "kurtosis"}).transpose()

    # Skewness
    skewness = pd.Series()
    for x in varlist:
        skewness[str(x)] = df[str(x)].skew()
    skewness = skewness.to_frame().rename(columns={0: "skewness"}).transpose()
    # Concat
    sum_stats = pd.concat([sum_stats, kurtosis, skewness])

    return sum_stats


# Augmented Dickey Fuller function

# First define make_var_names function to obtain the complete results of the ADF test


def make_var_names(var, n_lags, reg):
    names = [f"L1.{var}"]
    for lag in range(1, n_lags + 1):
        names.append(f"D{lag}L1.{var}")
    if reg != "n":
        names.append("Constant")
    if "t" in reg:
        names.append("Trend")

    return names


def ADF_test_summary(df, maxlag=None, autolag="BIC", missing="error"):
    if missing == "error":
        if df.isna().any().any():
            raise ValueError("df has missing data; handle it or pass missing='drop' to automatically drop it.")

    if isinstance(df, pd.Series):
        df = df.to_frame()

    for series in df.columns:
        data = df[series].copy()
        if missing == "drop":
            data.dropna(inplace=True)

        print(series.center(110))
        print("=" * 110)
        line = (
            "Specification"
            + " " * 15
            + "Coeff"
            + " " * 10
            + "Statistic"
            + " " * 5
            + "P-value"
            + " " * 6
            + "Lags"
            + " " * 6
            + "1%"
        )
        line += " " * 10 + "5%" + " " * 8 + "10%"
        print(line)
        print("-" * 110)
        for _i, (name, reg) in enumerate(
            zip(["Constant and Trend", "Constant Only", "No Constant"], ["ct", "c", "n"], strict=False)
        ):
            stat, p, crit, regresult = adfuller(data, regression=reg, regresults=True, maxlag=maxlag, autolag=autolag)
            n_lag = regresult.usedlag
            gamma = regresult.resols.params[0]
            names = make_var_names(series, n_lag, reg)
            reg_coefs = pd.Series(regresult.resols.params, index=names)
            reg_tstat = pd.Series(regresult.resols.tvalues, index=names)
            reg_pvals = pd.Series(regresult.resols.pvalues, index=names)

            line = f"{name:<21}{gamma:13.3f}{stat:15.3f}{p:13.3f}{n_lag:11}{crit['1%']:10.3f}{crit['5%']:12.3f}{crit['10%']:11.3f}"
            print(line)

            for coef in reg_coefs.index:
                if coef in name:
                    line = f"\t{coef:<13}{reg_coefs[coef]:13.3f}{reg_tstat[coef]:15.3f}{reg_pvals[coef]:13.3f}"
                    print(line)


def prediction_to_gpd_df(prediction_idata: xr.DataTree, variables: list, points: pd.DataFrame):
    predictions_dict = {}
    predictions_dict_geo = {}

    for variable in variables:
        # Tranform predictions to DF
        predictions_dict[variable] = (
            prediction_idata.posterior_predictive.mean(dim=("chain", "draw"))[variable].to_dataframe().reset_index()
        )
        # Merge predictions with Laos points
        predictions_dict[variable] = pd.merge(
            predictions_dict[variable],
            points,
            left_index=True,
            right_index=True,
            how="left",
        )

        # Transform into geo Data Frame
        predictions_dict_geo[variable] = gpd.GeoDataFrame(
            predictions_dict[variable],
            geometry=gpd.points_from_xy(predictions_dict[variable]["long"], predictions_dict[variable]["lat"]),
            crs=GEOGRAPHIC_CRS,
        )

    return predictions_dict_geo


def set_plotting_data(df, features, ISO_list):
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


def standardize(df: pd.DataFrame, columns: list[str], transformer_fitted=None):
    if transformer_fitted is None:
        transformer_fitted = Standardize().fit(df[columns])

    columns_stand = [x + "__standardized" for x in columns]
    df_stand = pd.DataFrame(transformer_fitted.transform(df[columns]), columns=columns_stand, index=df.index)
    df_stand = pd.concat([df, df_stand], axis=1)

    return transformer_fitted, df_stand
