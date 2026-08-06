from collections.abc import Sequence
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from climate_risk.const_vars import (
    LAOS_LOCATION_DICTIONARY,
    RIVERS_FLOODS_DAMAGE_FILENAME,
    RIVERS_HYDRO_DAMAGE_FILENAME,
)
from climate_risk.data_functions.emdat_processing import load_emdat_data
from climate_risk.data_functions.rivers_data_loader import load_rivers_data
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile
from climate_risk.geo.crs import to_km
from climate_risk.geo.distance import get_distance_to_rivers

DAMAGE_COLUMNS = ("ISO", "End Year", "Latitude", "Longitude", "River Basin", "Total_Damage", "Total_Affected", "Deaths")

# ESRI Shapefile truncates field names to ten characters, so the warm path restores them.
SHAPEFILE_FIELD_LIMIT = 10

# What pd.to_datetime produces on the cold path, which the warm path has to match.
YEAR_RESOLUTION = "datetime64[us]"


def _create_rivers_damage(
    cache_dir: Path,
    filename: str,
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
        Name of the cached shapefile inside ``cache_dir``.
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
    damage_path = cache_dir / filename
    totals = {"Total_Damage": f"Total_Damage_{total_suffix}", "Total_Affected": f"Total_Affected_{total_suffix}"}
    log_columns = [f"log_damage_{log_suffix}", f"log_affected_{log_suffix}"]

    if damage_path.is_file():
        cached = gpd.read_file(damage_path)
        full_names = [*totals.values(), *log_columns, "closest_river", "River Basin"]
        restored = cached.rename(columns={name[:SHAPEFILE_FIELD_LIMIT]: name for name in full_names})

        # A shapefile Date field holds whole days, so the year comes back as text or as a
        # coarser timestamp depending on the writer. The cold path hands back YEAR_RESOLUTION.
        return restored.assign(year=lambda x: pd.to_datetime(x["year"]).astype(YEAR_RESOLUTION))

    big_rivers = load_rivers_data(cache_dir)
    emdat = load_emdat_data(cache_dir)
    world = load_shapefile("world", cache_dir, repair_ISO_codes=True)

    events = emdat["df_raw_filtered_adj"].query(query)

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

    damage_df.to_file(damage_path)

    return damage_df


def create_hydro_rivers_damage(cache_dir: Path) -> gpd.GeoDataFrame:
    return _create_rivers_damage(
        cache_dir,
        filename=RIVERS_HYDRO_DAMAGE_FILENAME,
        query='disaster_class == "Hydrometereological"',
        total_suffix="Hydro",
        log_suffix="hydro",
    )


def create_floods_rivers_damage(cache_dir: Path) -> gpd.GeoDataFrame:
    return _create_rivers_damage(
        cache_dir,
        filename=RIVERS_FLOODS_DAMAGE_FILENAME,
        query='`Disaster Type` == "Flood"',
        total_suffix="Flood",
        log_suffix="floods",
        extra_columns=["Location"],
        locations=LAOS_LOCATION_DICTIONARY,
    )
