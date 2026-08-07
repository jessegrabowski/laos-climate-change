import logging

from pathlib import Path

import geopandas as gpd
import pandas as pd
import xarray as xr

from climate_risk.data.cache import cached, pandas_csv
from climate_risk.data.fetch import fetch
from climate_risk.data.source import DataSource
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile
from climate_risk.geo.crs import GEOGRAPHIC_CRS

_log = logging.getLogger(__name__)

HADCRUT = DataSource(
    url="https://crudata.uea.ac.uk/cru/data/temperature/HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc",
    filename="HadCRUT.5.0.2.0.analysis.anomalies.ensemble_mean.nc",
    licence="Open Government Licence v3",
    citation=(
        "HadCRUT.5.0.2.0 analysis anomalies, ensemble mean, obtained from "
        "https://www.metoffice.gov.uk/hadobs/hadcrut5 and \u00a9 British Crown Copyright, Met Office, "
        "provided under an Open Government Licence."
    ),
    retrieved="2026-08-05",
    sha256=None,
)

# The gridded record starts long before the panel does, and the early years are sparse.
FIRST_PANEL_YEAR = 1959

WORLD_COLUMNS = {
    "ISO_A3": "country_code",
    "FORMAL_EN": "country",
    "CONTINENT": "continent",
    "REGION_UN": "region",
}


def transform_hadcrut(temperatures: pd.DataFrame, world: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Average gridded temperature anomalies to one value per country and year.

    Parameters
    ----------
    temperatures : DataFrame
        Gridded anomalies with ``latitude``, ``longitude``, ``time`` and ``tas_mean`` columns.
    world : GeoDataFrame
        Country boundaries, carrying the columns named in ``WORLD_COLUMNS``.

    Returns
    -------
    DataFrame
        One row per country and year, indexed by ``ISO`` and ``year``.
    """
    located = gpd.GeoDataFrame(
        temperatures,
        geometry=gpd.points_from_xy(temperatures["longitude"], temperatures["latitude"]),
        crs=GEOGRAPHIC_CRS,
    )
    within_a_country = located.sjoin(world.rename(columns=WORLD_COLUMNS), how="inner", predicate="intersects")

    annual = within_a_country.assign(year=lambda x: pd.to_datetime(x["time"].dt.year, format="%Y"))

    return (
        annual.pivot_table(values="tas_mean", index=["country_code", "year"], aggfunc="mean")
        .rename(columns={"tas_mean": "surface_temperature_dev"})
        .reset_index()
        .rename(columns={"country_code": "ISO"})
        .query(f"year > {FIRST_PANEL_YEAR}")
        .set_index(["ISO", "year"])
    )


def load_hadcrut_data(cache_dir: Path, *, force_reload: bool = False, repair_ISO_codes: bool = True) -> pd.DataFrame:
    def build() -> pd.DataFrame:
        raw = fetch(HADCRUT, cache_dir, force=force_reload)

        _log.info("Reading gridded HadCRUT anomalies")
        gridded = xr.open_dataset(raw)["tas_mean"].to_dataframe().reset_index()
        world = load_shapefile("world", cache_dir, force_reload=force_reload, repair_ISO_codes=repair_ISO_codes)

        return transform_hadcrut(gridded, world)

    return cached(
        cache_dir,
        "hadcrut",
        build,
        # Caches exist with the year written bare and as an ISO date, so no format is given.
        pandas_csv(index_col=["ISO", "year"], parse_dates=["year"]),
        params={"repaired_iso": repair_ISO_codes},
        force=force_reload,
    )
