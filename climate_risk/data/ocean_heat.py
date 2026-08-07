from pathlib import Path

import polars as pl

from climate_risk.data.cache import cached, polars_parquet
from climate_risk.data.fetch import fetch
from climate_risk.data.source import DataSource

OCEAN_HEAT = DataSource(
    url=(
        "https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA"
        "/basin/3month/ohc_levitus_climdash_seasonal.csv"
    ),
    filename="ohc_levitus_climdash_seasonal.csv",
    licence="public domain (U.S. Government work, 17 U.S.C. 105)",
    citation=(
        "NOAA National Centers for Environmental Information, global ocean heat content. "
        "https://doi.org/10.7289/V53F4MVP"
    ),
    retrieved="2026-08-05",
)

# Shifts the NCEI anomalies onto the baseline the published results were estimated against. The
# derivation is unrecorded; changing it invalidates every downstream number.
OCEAN_HEAT_BASELINE_OFFSET = 152


def transform_ocean_heat(seasonal: pl.DataFrame) -> pl.DataFrame:
    """
    Average seasonal ocean-heat anomalies to calendar years and shift them onto the project baseline.

    Parameters
    ----------
    seasonal : DataFrame
        Anomalies with a ``Date`` column formatted ``YYYY-MM`` and a ``Temp`` column.

    Returns
    -------
    DataFrame
        Annual means dated to each year's first day, offset by ``OCEAN_HEAT_BASELINE_OFFSET``.
    """
    return (
        seasonal.with_columns(pl.col("Date").str.to_date("%Y-%m"))
        .group_by(pl.col("Date").dt.year().alias("year"))
        .agg(pl.col("Temp").mean())
        .select(pl.date(pl.col("year"), 1, 1).alias("Date"), pl.col("Temp") + OCEAN_HEAT_BASELINE_OFFSET)
        .sort("Date")
    )


def load_ocean_heat_data(cache_dir: Path, *, force_reload: bool = False) -> pl.DataFrame:
    def build() -> pl.DataFrame:
        raw = fetch(OCEAN_HEAT, cache_dir, force=force_reload)

        return transform_ocean_heat(pl.read_csv(raw, has_header=True, new_columns=["Date", "Temp"]))

    return cached(cache_dir, "ocean_heat", build, polars_parquet(), force=force_reload)
