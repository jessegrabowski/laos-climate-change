import geopandas as gpd
import pandas as pd

from joblib import Parallel, delayed
from tqdm.auto import tqdm

from climate_risk.geo.crs import PROJECTED_CRS

# Distances come back in metres, and a point sitting on a feature measures zero, which has no log.
MIN_DISTANCE_METRES = 1.0


def get_distance_to_rivers(
    rivers: gpd.GeoDataFrame, points: gpd.GeoDataFrame, crs: str = PROJECTED_CRS
) -> pd.DataFrame:
    ret = pd.DataFrame(index=points.index, columns=["closest_river", "ORD_FLOW", "HYRIV_ID"])
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
    gdf: gpd.GeoDataFrame | gpd.GeoSeries,
    points: gpd.GeoDataFrame,
    return_columns: list[str] | None = None,
    crs: str = PROJECTED_CRS,
    n_cores: int = -1,
    name: str | None = None,
) -> pd.DataFrame:
    """
    Measure the distance from every point to the nearest feature in ``gdf``.

    Parameters
    ----------
    gdf : GeoDataFrame or GeoSeries
        Features to measure to. Pass ``.boundary`` to measure to the edge of a polygon rather than
        into its interior.
    points : GeoDataFrame
        Points to measure from. The result carries this index.
    return_columns : list of str, optional
        Columns of ``gdf`` to carry across from whichever feature was nearest. Default None, which
        returns the distance alone.
    crs : str, optional
        Projected CRS to measure in, which fixes the units of the result. Default
        ``PROJECTED_CRS``, giving metres.
    n_cores : int, optional
        Cores to measure on, passed to joblib. Default -1, meaning all of them.
    name : str, optional
        Name of the features, used only in the progress description. Default None, which shows no
        description.

    Returns
    -------
    DataFrame
        ``distance_to_closest`` plus one column per entry in ``return_columns``, indexed like
        ``points``.
    """
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

    desc = f"Calculating distances to {name}" if name is not None else None

    with Parallel(n_cores, require="sharedmem") as pool:
        results = pool(
            delayed(get_closest)(idx, row, gdf_km, return_columns)
            for idx, row in tqdm(points_km.iterrows(), total=points.shape[0], desc=desc)
        )
    return pd.DataFrame(results, columns=["distance_to_closest", *return_columns], index=points.index)
