import gzip
import logging
import os
import shutil

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr

from climate_risk.data.cache import cached, pandas_parquet
from climate_risk.data.fetch import fetch
from climate_risk.data.source import DataSource
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile
from climate_risk.geo.crs import GEOGRAPHIC_CRS

_log = logging.getLogger(__name__)

GPCC_URL = "https://opendata.dwd.de/climate_environment/GPCC"

# The name every grid carries once read, whatever the product it came from calls it.
PRECIPITATION = "precip"

# DWD writes the monitoring dates as YYYYMMDD floats under this unit string. CF does not define it,
# so xarray hands the axis back undecoded and it has to be read here.
DWD_DATE_UNITS = "day as %Y%m%d.%f"

FULL_DATA_START = 1891
FULL_DATA_END = 2020

# The near-real-time product carries on where the gauge analysis stops. Complete calendar years
# only: the annual totals downstream would read a part-year as a drought.
MONITORING_END = 2025
MONITORING_YEARS = tuple(range(FULL_DATA_END + 1, MONITORING_END + 1))

FULL_DATA_DECADES = tuple(f"{start}_{start + 9}" for start in range(FULL_DATA_START, FULL_DATA_END, 10))

FULL_DATA_CITATION = (
    "Schneider, U., Hänsel, S., Finger, P., Rustemeier, E., Ziese, M. (2022): GPCC Full Data "
    "Monthly Product Version 2022 at 1.0 degrees. "
    "https://doi.org/10.5676/DWD_GPCC/FD_M_V2022_100"
)

MONITORING_CITATION = (
    "Schneider, U., Becker, A., Finger, P., Rustemeier, E., Ziese, M. (2022): GPCC Monitoring "
    "Product: Near Real-Time Monthly Land-Surface Precipitation from Rain-Gauges based on SYNOP and "
    "CLIMAT data, at 1.0 degrees. https://doi.org/10.5676/DWD_GPCC/MP_M_V2022_100"
)


@dataclass(frozen=True, slots=True)
class GriddedProduct:
    """
    A GPCC product and the archives it is published in.

    Parameters
    ----------
    variable : str
        Name of the precipitation grid inside each archive.
    first_year, last_year : int
        The span the archives cover, both years included.
    sources : tuple of DataSource
        The archives making up the product, in time order.
    """

    variable: str
    first_year: int
    last_year: int
    sources: tuple[DataSource, ...]


def coverage_of(products: Iterable[GriddedProduct]) -> str:
    """Return the span a set of products covers, as the string their cache entry is keyed on."""
    covered = tuple(products)

    return f"{min(product.first_year for product in covered)}-{max(product.last_year for product in covered)}"


def _full_data_archive(decade: str) -> DataSource:
    name = f"full_data_monthly_v2022_{decade}_10.nc.gz"

    return DataSource(
        url=f"{GPCC_URL}/full_data_monthly_v2022/10/{name}",
        filename=name,
        licence="CC BY 4.0",
        citation=FULL_DATA_CITATION,
        retrieved="2026-08-05",
    )


def _monitoring_archive(year: int, month: int) -> DataSource:
    name = f"monitoring_v2022_10_{year}_{month:02d}.nc.gz"

    return DataSource(
        url=f"{GPCC_URL}/monitoring_v2022/{year}/{name}",
        filename=name,
        licence="CC BY 4.0",
        citation=MONITORING_CITATION,
        retrieved="2026-08-07",
    )


# The reanalysed gauge record, published a decade to an archive.
FULL_DATA = GriddedProduct(
    variable="precip",
    first_year=FULL_DATA_START,
    last_year=FULL_DATA_END,
    sources=tuple(_full_data_archive(decade) for decade in FULL_DATA_DECADES),
)

# The near-real-time continuation, published a month to an archive and built from fewer stations.
MONITORING = GriddedProduct(
    variable="p",
    first_year=MONITORING_YEARS[0],
    last_year=MONITORING_YEARS[-1],
    sources=tuple(_monitoring_archive(year, month) for year in MONITORING_YEARS for month in range(1, 13)),
)

GPCC_PRODUCTS = (FULL_DATA, MONITORING)

# The archives are large enough to keep out of the top-level cache listing.
GPCC_SUBDIRECTORY = "gpcc"

WORLD_COLUMNS = {
    "ISO_A3": "country_code",
    "FORMAL_EN": "country",
    "CONTINENT": "continent",
    "REGION_UN": "region",
}


def transform_gpcc(grids: Iterable[pd.DataFrame], world: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Average gridded precipitation to one value per country and month.

    Parameters
    ----------
    grids : iterable of DataFrame
        Gridded precipitation, one frame per archive, with ``lat``, ``lon``, ``time`` and ``precip``.
    world : GeoDataFrame
        Country boundaries, carrying the columns named in ``WORLD_COLUMNS``.

    Returns
    -------
    DataFrame
        One row per country and month, indexed by ``country_code`` and ``time``.
    """
    countries = world.rename(columns=WORLD_COLUMNS)

    # Each grid is reduced to land cells before the next is read, so the whole record is never held.
    over_land = [
        gpd.GeoDataFrame(
            gridded, geometry=gpd.points_from_xy(gridded["lon"], gridded["lat"]), crs=GEOGRAPHIC_CRS
        ).sjoin(countries, how="inner", predicate="intersects")[["time", PRECIPITATION, "country_code"]]
        for gridded in grids
    ]

    return (
        pd.concat(over_land, axis=0)
        .astype({PRECIPITATION: "float64"})
        .pivot_table(values=PRECIPITATION, index=["country_code", "time"], aggfunc="mean")
    )


def _as_timestamps(time: xr.DataArray) -> np.ndarray:
    """
    Return an archive's time axis as timestamps, whichever way the product encoded it.

    Parameters
    ----------
    time : DataArray
        The ``time`` coordinate as read from the archive.

    Returns
    -------
    ndarray
        The axis as ``datetime64``.

    Raises
    ------
    ValueError
        If the axis is neither already decoded nor written under ``DWD_DATE_UNITS``.
    """
    if np.issubdtype(time.dtype, np.datetime64):
        return time.values

    units = time.attrs.get("units")
    if units != DWD_DATE_UNITS:
        raise ValueError(
            f"The time axis is {time.dtype} under units {units!r}, which is neither a decoded datetime nor "
            f"the {DWD_DATE_UNITS!r} convention. Reading it as a number would date every row to 1970."
        )

    return pd.to_datetime(time.values.astype("int64").astype(str), format="%Y%m%d").values


def _extract(archive: Path) -> Path:
    """Decompress the archive beside itself if needed, and return the plain file."""
    extracted = archive.with_suffix("")

    if not extracted.exists():
        _log.info(f"Extracting {archive.name}")
        # Decompress beside the target and move, so an interrupted run leaves no truncated archive.
        partial = extracted.with_suffix(extracted.suffix + ".part")
        with gzip.open(archive, "rb") as compressed, partial.open("wb") as plain:
            shutil.copyfileobj(compressed, plain)
        os.replace(partial, extracted)

    return extracted


def _read_archive(archive: Path, variable: str) -> pd.DataFrame:
    """Read one archive's precipitation grid, under the canonical name and with its dates decoded."""
    with xr.open_dataset(_extract(archive)) as dataset:
        grid = dataset[variable]
        dated = grid.assign_coords(time=_as_timestamps(grid["time"]))

        return dated.rename(PRECIPITATION).to_dataframe().reset_index()


def load_gpcc_data(
    cache_dir: Path,
    *,
    products: tuple[GriddedProduct, ...] = GPCC_PRODUCTS,
    force_reload: bool = False,
    repair_ISO_codes: bool = True,
) -> pd.DataFrame:
    def build() -> pd.DataFrame:
        archives = [
            (fetch(source, cache_dir / GPCC_SUBDIRECTORY, force=force_reload), product.variable)
            for product in products
            for source in product.sources
        ]
        world = load_shapefile("world", cache_dir, repair_ISO_codes=repair_ISO_codes)

        return transform_gpcc((_read_archive(archive, variable) for archive, variable in archives), world)

    return cached(
        cache_dir,
        "gpcc",
        build,
        pandas_parquet(),
        params={"repaired_iso": repair_ISO_codes, "coverage": coverage_of(products), "precision": "float64"},
        force=force_reload,
    )
