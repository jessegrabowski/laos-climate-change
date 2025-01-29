from statsmodels.tsa.stattools import adfuller
from joblib import Parallel, delayed
import pandas as pd
from tqdm.notebook import tqdm
import numpy as np
import geopandas as gpd
import arviz as az
import pymc as pm


# Descriptive stats function
def descriptive_stats_function(df, varlist):
    # Sum stats
    sum_stats = df.describe()
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
            raise ValueError(
                "df has missing data; handle it or pass missing='drop' to automatically drop it."
            )

    if isinstance(df, pd.Series):
        df = df.to_frame()

    for series in df.columns:
        data = df[series].copy()
        if missing == "drop":
            data.dropna(inplace=True)

        print(series.center(110))
        print(("=" * 110))
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
        print(("-" * 110))
        for i, (name, reg) in enumerate(
            zip(
                ["Constant and Trend", "Constant Only", "No Constant"], ["ct", "c", "n"]
            )
        ):
            stat, p, crit, regresult = adfuller(
                data, regression=reg, regresults=True, maxlag=maxlag, autolag=autolag
            )
            n_lag = regresult.usedlag
            gamma = regresult.resols.params[0]
            names = make_var_names(series, n_lag, reg)
            reg_coefs = pd.Series(regresult.resols.params, index=names)
            reg_tstat = pd.Series(regresult.resols.tvalues, index=names)
            reg_pvals = pd.Series(regresult.resols.pvalues, index=names)

            line = f'{name:<21}{gamma:13.3f}{stat:15.3f}{p:13.3f}{n_lag:11}{crit["1%"]:10.3f}{crit["5%"]:12.3f}{crit["10%"]:11.3f}'
            print(line)

            for coef in reg_coefs.index:
                if coef in name:
                    line = f"\t{coef:<13}{reg_coefs[coef]:13.3f}{reg_tstat[coef]:15.3f}{reg_pvals[coef]:13.3f}"
                    print(line)


def get_distance_to_rivers(rivers, points, crs="EPSG:3395"):
    ret = pd.DataFrame(
        index=points.index, columns=["closest_river", "ORD_FLOW", "HYRIV_ID"]
    )
    rivers_km = rivers.copy().to_crs(crs)
    points_km = points.copy().to_crs(crs)
    for idx, row in tqdm(points_km.iterrows(), total=points.shape[0]):
        series = rivers_km.distance(row.geometry)
        ret.loc[idx, "closest_river"] = series.min()

        index = series[series == series.min()].index[0]
        ret.loc[idx, "ORD_FLOW"] = rivers_km.loc[index]["ORD_FLOW"]
        ret.loc[idx, "HYRIV_ID"] = rivers_km.loc[index]["HYRIV_ID"]

    ret["ORD_FLOW"] = ret["ORD_FLOW"].astype("int")
    ret["closest_river"] = ret["closest_river"].astype("float")
    return ret


def get_distance_to(
    gdf, points, return_columns=None, crs="EPSG:3395", n_cores=-1, name=None
):
    if return_columns is None:
        return_columns = []

    gdf_km = gdf.copy().to_crs(crs)
    points_km = points.copy().to_crs(crs)

    def get_closest(idx, row, gdf_km, return_columns):
        series = gdf_km.distance(row.geometry)
        index = series[series == series.min()].index[0]

        ret_vals = (series.min(),)
        for col in return_columns:
            ret_vals += (gdf_km.loc[index][col],)

        return ret_vals

    if name is not None:
        desc = f"Calculating distances to {name}"
    else:
        desc = None

    with Parallel(n_cores, require="sharedmem") as pool:
        results = pool(
            delayed(get_closest)(idx, row, gdf_km, return_columns)
            for idx, row in tqdm(points_km.iterrows(), total=points.shape[0], desc=desc)
        )
    return pd.DataFrame(
        results, columns=["distance_to_closest"] + return_columns, index=points.index
    )


def create_grid_from_shape(shapefile, rivers, coastline, grid_size=100):
    long_min, lat_min, long_max, lat_max = shapefile.dissolve().bounds.values.ravel()
    long_grid = np.linspace(long_min, long_max, grid_size)
    lat_grid = np.linspace(lat_min, lat_max, grid_size)

    grid = np.column_stack([x.ravel() for x in np.meshgrid(long_grid, lat_grid)])
    grid = gpd.GeoSeries(gpd.points_from_xy(*grid.T), crs="EPSG:4326")
    grid = gpd.GeoDataFrame({"geometry": grid})

    point_overlay = grid.overlay(shapefile, how="intersection")
    points = point_overlay.geometry
    points = points.to_frame().assign(
        long=lambda x: x.geometry.x, lat=lambda x: x.geometry.y
    )

    # Obtain distance with rivers
    distances_to_rivers = get_distance_to(
        rivers, points=points, return_columns=["ORD_FLOW", "HYRIV_ID"]
    ).rename(columns={"distance_to_closest": "distance_to_river"})

    points = pd.merge(
        points, distances_to_rivers, left_index=True, right_index=True, how="left"
    )

    # Obtain Laos distance with coastlines
    distances_to_coastlines = get_distance_to(
        coastline.boundary, points=points, return_columns=None
    ).rename(columns={"distance_to_closest": "distance_to_coastline"})

    points = pd.merge(
        points, distances_to_coastlines, left_index=True, right_index=True, how="left"
    )

    # Create log of distances
    points = points.assign(
        log_distance_to_river=lambda x: np.log(x.distance_to_river),
        log_distance_to_coastline=lambda x: np.log(x.distance_to_coastline),
    )

    if "ISO_A3" in point_overlay.columns:
        points["ISO"] = point_overlay.ISO_A3
    else:
        points["ISO"] = "LAO"

    return points


def load_island_table():
    import wikipedia as wp

    html = wp.page("List_of_island_countries").html().encode("UTF-8")
    island_table = (
        pd.read_html(html, skiprows=0)[0]
        .droplevel(axis=1, level=0)
        .dropna(how="all")
        .iloc[1:]
        .reset_index(drop=True)
        .assign(
            ISO_2=lambda x: x["ISO code"].str.split().str[0],
            ISO_3=lambda x: x["ISO code"].str.split().str[1].replace({"or": "GBR"}),
        )
    )

    return island_table


def prediction_to_gpd_df(
    prediction_idata: az.InferenceData, variables: list, points: pd.DataFrame()
):
    predictions_dict = {}
    predictions_dict_geo = {}

    for variable in variables:
        # Tranform predictions to DF
        predictions_dict[variable] = (
            prediction_idata.posterior_predictive.mean(dim=("chain", "draw"))[variable]
            .to_dataframe()
            .reset_index()
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
            geometry=gpd.points_from_xy(
                predictions_dict[variable]["long"], predictions_dict[variable]["lat"]
            ),
            crs="EPSG:4326",
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


def add_data(
    features: list[str], target: str, df: pd.DataFrame, add_time: bool = False
):
    with pm.modelcontext(None):
        X = pm.Data("X", df[features], dims=["obs_idx", "feature"])
        Y = pm.Data("Y", df[target], dims=["obs_idx"])
    return X, Y


def add_country_effect():
    with pm.modelcontext(None):
        country_effect_mu = pm.Normal("country_effect_mu", mu=0, sigma=1)
        country_effect_scale = pm.Gamma("country_effect_scale", alpha=2, beta=1)
        country_effect_offset = pm.Normal("country_effect_offset", sigma=1, dims="ISO")
        country_effect = pm.Deterministic(
            "country_effect",
            country_effect_mu + country_effect_scale * country_effect_offset,
            dims="ISO",
        )

    return (
        country_effect,
        country_effect_mu,
        country_effect_scale,
        country_effect_offset,
    )
