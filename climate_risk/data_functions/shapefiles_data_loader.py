import logging

from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import geopandas as gpd
import numpy as np
import pandas as pd

from climate_risk.const_vars import (
    COASTLINE_FILENAME,
    COASTLINE_URL,
    LAOS_FILENAME,
    LAOS_URL,
    WORLD_FILENAME,
    WORLD_URL,
)
from climate_risk.data_functions.rivers_data_loader import load_rivers_data
from climate_risk.exceptions import DataValidationError, ISOCodeValidationError
from climate_risk.geo.crs import GEOGRAPHIC_CRS
from climate_risk.geo.distance import MIN_DISTANCE_METRES, get_distance_to

_log = logging.getLogger(__name__)


shapefile_name_dict = {
    "world": WORLD_FILENAME.replace(".zip", ""),
    "laos": LAOS_FILENAME.replace(".zip", ""),
    "coastline": COASTLINE_FILENAME.replace(".zip", ""),
}

shapefile_url_dict = {"world": WORLD_URL, "laos": LAOS_URL, "coastline": COASTLINE_URL}

# Paths inside each archive, case included -- a case-insensitive filesystem hides a mismatch
# here that fails on Linux.
shapefile_filename_dict = {
    "world": "WB_countries_Admin0_10m",
    # The Laos archive unpacks flat, one file per admin level. Level 2 is the district layer the
    # point grid is built from.
    "laos": "lao_admin2.shp",
    "coastline": "GSHHS_shp/f",
}


VALID_CHOICES = list(shapefile_name_dict.keys())


def shapefile_dir(cache_dir: Path) -> Path:
    return cache_dir / "shapefiles"


# The boundary file lists these separately but tags them with their owner's ISO code, or with no
# code at all, so counting them would double-count the owner or introduce a country that is not one.
DROPPED_TERRITORIES = (
    # Leased or far-flung dependencies carrying no code of their own.
    "Guantanamo Bay (US)",
    "Clipperton Island (Fr.)",
    "Cocos (Keeling) Islands (Aus.)",
    "Christmas Island (Aus.)",
    # Caribbean municipalities labelled as the Netherlands.
    "Bonaire (Neth.)",
    "Sint Eustatius (Neth.)",
    "Saba (Neth.)",
    # Labelled as New Zealand.
    "Tokelau (NZ)",
)

# The US minor outlying islands share one code, so they are matched by it rather than by name.
DROPPED_ISO_CODES = ("UMI",)

# Sovereign countries the boundary file leaves at -99. XKX is the World Bank's own code for Kosovo,
# which has none under ISO 3166-1, and is what COUNTRIES_ISO and ISO_DICTIONARY use.
ISO_CODE_REPAIRS = {
    "France": "FRA",
    "Norway": "NOR",
    "Kosovo": "XKX",
}


def repair_iso_codes(world: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Drop territories that would double-count their owner and supply the missing ISO codes.

    Parameters
    ----------
    world : GeoDataFrame
        The world boundary file, carrying ``WB_NAME`` and ``ISO_A3`` columns.

    Returns
    -------
    GeoDataFrame
        The repaired frame, reindexed from zero.

    Raises
    ------
    DataValidationError
        If a repair matches no row, which means the boundary file has changed under it.
    ISOCodeValidationError
        If any ISO code labels more than one geometry after the repairs.
    """
    missing_columns = {"WB_NAME", "ISO_A3"} - set(world.columns)
    if missing_columns:
        raise DataValidationError(f"The boundary file is missing {sorted(missing_columns)}, so it cannot be repaired.")

    unmatched = sorted({*DROPPED_TERRITORIES, *ISO_CODE_REPAIRS} - set(world["WB_NAME"]))
    unmatched += sorted(set(DROPPED_ISO_CODES) - set(world["ISO_A3"]))
    if unmatched:
        raise DataValidationError(
            f"No row matches {unmatched}. The boundary file has changed, and applying the remaining "
            f"repairs would drop or relabel the wrong countries."
        )

    repaired = world[~world["WB_NAME"].isin(DROPPED_TERRITORIES) & ~world["ISO_A3"].isin(DROPPED_ISO_CODES)].copy()
    repaired["ISO_A3"] = repaired["WB_NAME"].map(ISO_CODE_REPAIRS).fillna(repaired["ISO_A3"])
    repaired = repaired.reset_index(drop=True)

    geometries_per_code = repaired["ISO_A3"].value_counts()
    duplicated = geometries_per_code[geometries_per_code > 1]
    if not duplicated.empty:
        raise ISOCodeValidationError(f"These ISO codes label more than one geometry: {dict(duplicated)}")

    return repaired


def download_shapefile(which: str, cache_dir: Path, *, force_reload: bool = False) -> None:
    if which.lower() not in VALID_CHOICES:
        raise ValueError(f"which should be one of {VALID_CHOICES}, got {which}")
    url = shapefile_url_dict[which.lower()]
    filename = shapefile_name_dict[which.lower()] + ".zip"

    output_path = shapefile_dir(cache_dir)
    path_to_file = output_path / filename

    output_path.mkdir(parents=True, exist_ok=True)

    if not path_to_file.exists() or force_reload:
        _log.info(f"Downloading {which} shapefiles to {output_path}")
        urlretrieve(url, path_to_file)


def extract_shapefiles(which: str, cache_dir: Path, *, force_reload: bool = False) -> None:
    if which.lower() not in VALID_CHOICES:
        raise ValueError(f"which should be one of {VALID_CHOICES}, got {which}")
    zip_filename = shapefile_name_dict[which.lower()]
    filename = shapefile_filename_dict[which.lower()]

    output_path = shapefile_dir(cache_dir)
    shapefile_path = output_path / filename

    if not shapefile_path.exists() or force_reload:
        _log.info(f"Extracting {zip_filename}.zip")

        with ZipFile(output_path / (zip_filename + ".zip"), "r") as zObject:
            zObject.extractall(path=output_path)


def load_shapefile(
    which: str, cache_dir: Path, *, force_reload: bool = False, repair_ISO_codes: bool = True
) -> gpd.GeoDataFrame:
    if which.lower() not in VALID_CHOICES:
        raise ValueError(f"which should be one of {VALID_CHOICES}, got {which}")
    filename = shapefile_filename_dict[which.lower()]

    shapefile_path = shapefile_dir(cache_dir) / filename
    download_shapefile(which, cache_dir, force_reload=force_reload)
    extract_shapefiles(which, cache_dir, force_reload=force_reload)

    df = gpd.read_file(shapefile_path, layer=0)

    if which == "world" and repair_ISO_codes:
        df = repair_iso_codes(df)

    return df


def create_laos_point_grid(cache_dir: Path) -> gpd.GeoDataFrame:
    laos_points_path = cache_dir / "laos_points.shp"

    if laos_points_path.exists():
        laos_points = gpd.read_file(laos_points_path)
        laos_points = laos_points.rename(
            columns={
                "distance_t": "distance_to_river",
                "distance_1": "distance_to_coastline",
                "log_distan": "log_distance_to_river",
                "log_dist_1": "log_distance_to_coastline",
            }
        )
        return laos_points

    else:
        laos = load_shapefile("laos", cache_dir)
        coastline = load_shapefile("coastline", cache_dir)
        rivers = load_rivers_data(cache_dir)

        # Creating Laos grid
        lon_min, lat_min, lon_max, lat_max = laos.dissolve().bounds.values.ravel()
        lon_grid = np.linspace(lon_min, lon_max, 100)
        lat_grid = np.linspace(lat_min, lat_max, 100)

        laos_grid = np.column_stack([x.ravel() for x in np.meshgrid(lon_grid, lat_grid)])
        grid = gpd.GeoSeries(gpd.points_from_xy(*laos_grid.T), crs=GEOGRAPHIC_CRS)
        grid = gpd.GeoDataFrame({"geometry": grid})

        laos_points = grid.overlay(laos, how="intersection").geometry
        laos_points = laos_points.to_frame().assign(lon=lambda x: x.geometry.x, lat=lambda x: x.geometry.y)

        # Obtain distance with rivers
        Laos_distances_rivers = get_distance_to(
            rivers, points=laos_points, return_columns=["ORD_FLOW", "HYRIV_ID"]
        ).rename(columns={"distance_to_closest": "distance_to_river"})

        laos_points = pd.merge(
            laos_points,
            Laos_distances_rivers,
            left_index=True,
            right_index=True,
            how="left",
        )

        # Obtain Laos distance with coastlines
        Laos_distances_coastlines = get_distance_to(coastline.boundary, points=laos_points, return_columns=None).rename(
            columns={"distance_to_closest": "distance_to_coastline"}
        )

        laos_points = pd.merge(
            laos_points,
            Laos_distances_coastlines,
            left_index=True,
            right_index=True,
            how="left",
        )

        # Assign is_island column
        laos_points["is_island"] = False

        # Create log of distances
        laos_points = laos_points.assign(
            log_distance_to_river=lambda x: np.log(x.distance_to_river.clip(lower=MIN_DISTANCE_METRES)),
            log_distance_to_coastline=lambda x: np.log(x.distance_to_coastline.clip(lower=MIN_DISTANCE_METRES)),
        )

        laos_points.to_file(laos_points_path)

        return laos_points
