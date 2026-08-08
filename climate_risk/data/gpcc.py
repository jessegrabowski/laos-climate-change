import gzip
import logging
import os
import shutil

from collections.abc import Iterable
from pathlib import Path

import geopandas as gpd
import pandas as pd
import xarray as xr

from climate_risk.data.cache import cached, pandas_parquet
from climate_risk.data.fetch import fetch
from climate_risk.data.source import DataSource
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile
from climate_risk.geo.crs import GEOGRAPHIC_CRS

_log = logging.getLogger(__name__)

GPCC_DECADES = ("1981_1990", "1991_2000", "2001_2010", "2011_2020")

# The span the cache entry is keyed on, so extending the record writes a new entry rather than
# serving the shorter one already on disk.
GPCC_COVERAGE = f"{GPCC_DECADES[0].split('_')[0]}-{GPCC_DECADES[-1].split('_')[1]}"

GPCC = {
    decade: DataSource(
        url=(
            "https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022/10"
            f"/full_data_monthly_v2022_{decade}_10.nc.gz"
        ),
        filename=f"full_data_monthly_v2022_{decade}_10.nc.gz",
        licence="CC BY 4.0",
        citation=(
            "Schneider, U., H\u00e4nsel, S., Finger, P., Rustemeier, E., Ziese, M. (2022): GPCC Full Data "
            "Monthly Product Version 2022 at 1.0 degrees. "
            "https://doi.org/10.5676/DWD_GPCC/FD_M_V2022_100"
        ),
        retrieved="2026-08-05",
    )
    for decade in GPCC_DECADES
}

# The archives are large enough to keep out of the top-level cache listing.
GPCC_SUBDIRECTORY = "gpcc"

WORLD_COLUMNS = {
    "ISO_A3": "country_code",
    "FORMAL_EN": "country",
    "CONTINENT": "continent",
    "REGION_UN": "region",
}


def transform_gpcc(decades: Iterable[pd.DataFrame], world: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Average gridded precipitation to one value per country and month.

    Parameters
    ----------
    decades : iterable of DataFrame
        Gridded precipitation, one frame per archive, with ``lat``, ``lon``, ``time`` and ``precip``.
    world : GeoDataFrame
        Country boundaries, carrying the columns named in ``WORLD_COLUMNS``.

    Returns
    -------
    DataFrame
        One row per country and month, indexed by ``country_code`` and ``time``.
    """
    countries = world.rename(columns=WORLD_COLUMNS)

    # Each decade is reduced to land cells before the next is read, so the whole grid is never held.
    over_land = [
        gpd.GeoDataFrame(
            gridded, geometry=gpd.points_from_xy(gridded["lon"], gridded["lat"]), crs=GEOGRAPHIC_CRS
        ).sjoin(countries, how="inner", predicate="intersects")[["time", "precip", "country_code"]]
        for gridded in decades
    ]

    return pd.concat(over_land, axis=0).pivot_table(values="precip", index=["country_code", "time"], aggfunc="mean")


def _read_decade(archive: Path) -> pd.DataFrame:
    """Decompress the archive beside itself if needed, then read its precipitation grid."""
    extracted = archive.with_suffix("")

    if not extracted.exists():
        _log.info(f"Extracting {archive.name}")
        # Decompress beside the target and move, so an interrupted run leaves no truncated archive.
        partial = extracted.with_suffix(extracted.suffix + ".part")
        with gzip.open(archive, "rb") as compressed, partial.open("wb") as plain:
            shutil.copyfileobj(compressed, plain)
        os.replace(partial, extracted)

    return xr.open_dataset(extracted)["precip"].to_dataframe().reset_index()


def load_gpcc_data(cache_dir: Path, *, force_reload: bool = False, repair_ISO_codes: bool = True) -> pd.DataFrame:
    def build() -> pd.DataFrame:
        archives = [fetch(source, cache_dir / GPCC_SUBDIRECTORY, force=force_reload) for source in GPCC.values()]
        world = load_shapefile("world", cache_dir, repair_ISO_codes=repair_ISO_codes)

        return transform_gpcc((_read_decade(archive) for archive in archives), world)

    return cached(
        cache_dir,
        "gpcc",
        build,
        pandas_parquet(),
        params={"repaired_iso": repair_ISO_codes, "coverage": GPCC_COVERAGE},
        force=force_reload,
    )
