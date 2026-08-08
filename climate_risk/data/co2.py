from pathlib import Path

import polars as pl

from climate_risk.data.cache import cached, polars_parquet
from climate_risk.data.fetch import fetch
from climate_risk.data.source import DataSource

# Raw downloads are named for the file upstream serves; the processed cache is keyed on a logical name.
CO2 = DataSource(
    url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv",
    filename="co2_annmean_mlo.csv",
    licence="public domain (U.S. Government work, 17 U.S.C. 105)",
    citation=(
        "Lan, X., NOAA Global Monitoring Laboratory (https://gml.noaa.gov/ccgg/trends/) and "
        "Keeling, R., Scripps Institution of Oceanography. Mauna Loa annual mean CO2."
    ),
    retrieved="2026-08-05",
)

# The published file carries its licence and methodology above the header row.
CO2_HEADER_ROW = 43


def transform_co2(raw: pl.DataFrame) -> pl.DataFrame:
    """
    Reduce the NOAA annual means to a ``Date`` and a ``co2`` column.

    Parameters
    ----------
    raw : DataFrame
        The published file, carrying ``year`` and ``mean`` columns.

    Returns
    -------
    DataFrame
        One row per year, dated to its first day.
    """
    return raw.select(
        pl.date(pl.col("year"), 1, 1).alias("Date"),
        pl.col("mean").alias("co2"),
    )


def load_co2_data(cache_dir: Path, *, force_reload: bool = False) -> pl.DataFrame:
    def build() -> pl.DataFrame:
        # Fetching inside the builder keeps a warm cache from reaching the network.
        raw = fetch(CO2, cache_dir, force=force_reload)

        return transform_co2(pl.read_csv(raw, skip_rows=CO2_HEADER_ROW))

    return cached(cache_dir, "co2", build, polars_parquet(), force=force_reload)
