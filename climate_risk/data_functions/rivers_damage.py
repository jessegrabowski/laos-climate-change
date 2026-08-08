from collections.abc import Sequence
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from climate_risk.data.cache import cached, geo_parquet
from climate_risk.data_functions.emdat_processing import load_emdat_data
from climate_risk.data_functions.rivers_data_loader import load_rivers_data
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile
from climate_risk.geo.crs import to_km
from climate_risk.geo.distance import get_distance_to_rivers

DAMAGE_COLUMNS = ("ISO", "End Year", "Latitude", "Longitude", "River Basin", "Total_Damage", "Total_Affected", "Deaths")

LAOS_LOCATION_DICTIONARY = {
    "1971-0048-LAO": {"Latitude": 17.9757, "Longitude": 102.6331},
    "2000-0583-LAO": {"Latitude": 19.0, "Longitude": 102.0},
    "2013-0338-LAO": {"Latitude": 19.5, "Longitude": 103.5},
    "2013-0417-LAO": {"Latitude": 16.5, "Longitude": 106.0},
    "2015-0324-LAO": {"Latitude": 19.0, "Longitude": 104.0},
    "2016-0316-LAO": {"Latitude": 19.9, "Longitude": 102.1},
}


def _create_rivers_damage(
    cache_dir: Path,
    name: str,
    query: str,
    total_suffix: str,
    log_suffix: str,
    extra_columns: Sequence[str] = (),
    locations: dict[str, dict[str, float]] | None = None,
) -> gpd.GeoDataFrame:
    """
    Join EM-DAT damages to the nearest major river, caching the result as a shapefile.

    Parameters
    ----------
    cache_dir : Path
        Directory holding the EM-DAT workbook, the shapefiles and the cached output.
    filename : str
        Logical name the result is cached under.
    query : str
        Pandas query selecting the events, applied to the adjusted EM-DAT frame.
    total_suffix : str
        Suffix for the damage and affected totals, giving ``Total_Damage_{total_suffix}``.
    log_suffix : str
        Suffix for their logarithms, giving ``log_damage_{log_suffix}``.
    extra_columns : sequence of str, optional
        Columns to carry through beyond ``DAMAGE_COLUMNS``. Default empty.
    locations : dict mapping str to dict, optional
        Latitude and longitude to force onto specific ``DisNo.`` events. Default None, which forces
        nothing.

    Returns
    -------
    GeoDataFrame
        One row per event, with its distance in kilometres to the nearest major river.
    """
    totals = {"Total_Damage": f"Total_Damage_{total_suffix}", "Total_Affected": f"Total_Affected_{total_suffix}"}

    def build() -> gpd.GeoDataFrame:
        big_rivers = load_rivers_data(cache_dir)
        emdat = load_emdat_data(cache_dir)["df_raw_filtered_adj"].to_pandas()
        world = load_shapefile("world", cache_dir, repair_ISO_codes=True)

        events = emdat.query(query)

        if locations is not None:
            for disaster_number, coordinates in locations.items():
                matching = events[events["DisNo."] == disaster_number].index
                events.loc[matching, "Latitude"] = coordinates["Latitude"]
                events.loc[matching, "Longitude"] = coordinates["Longitude"]

        damage_df = gpd.GeoDataFrame(
            (
                events[[*DAMAGE_COLUMNS, *extra_columns]]
                .dropna(how="any", subset=["Latitude", "Longitude"])
                .assign(
                    geometry=lambda x: gpd.points_from_xy(x.Longitude, x.Latitude),
                    year=lambda x: pd.to_datetime(x["End Year"], format="%Y"),
                )
                .drop(columns=["End Year"])
                .replace({0.0: np.nan})
            ),
            crs=world.crs,
        )

        closest_river = get_distance_to_rivers(big_rivers, damage_df)
        closest_river["closest_river"] = to_km(closest_river["closest_river"])

        damage_df = damage_df.join(closest_river).rename(columns=totals)
        damage_df = damage_df.assign(
            **{
                f"log_damage_{log_suffix}": np.log(damage_df[totals["Total_Damage"]]),
                f"log_affected_{log_suffix}": np.log(damage_df[totals["Total_Affected"]]),
            }
        )

        return damage_df

    return cached(cache_dir, name, build, geo_parquet())


def create_hydro_rivers_damage(cache_dir: Path) -> gpd.GeoDataFrame:
    return _create_rivers_damage(
        cache_dir,
        name="rivers_hydro_damage",
        query='disaster_class == "Hydrometereological"',
        total_suffix="Hydro",
        log_suffix="hydro",
    )


def create_floods_rivers_damage(cache_dir: Path) -> gpd.GeoDataFrame:
    return _create_rivers_damage(
        cache_dir,
        name="rivers_floods_damage",
        query='`Disaster Type` == "Flood"',
        total_suffix="Flood",
        log_suffix="floods",
        extra_columns=["Location"],
        locations=LAOS_LOCATION_DICTIONARY,
    )
