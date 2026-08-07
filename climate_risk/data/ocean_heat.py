from pathlib import Path

import pandas as pd

from climate_risk.data.cache import cached, pandas_csv
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


def transform_ocean_heat(seasonal: pd.DataFrame) -> pd.DataFrame:
    """
    Average seasonal ocean-heat anomalies to calendar years and shift them onto the project baseline.

    Parameters
    ----------
    seasonal : DataFrame
        Anomalies with a ``Date`` column formatted ``YYYY-MM`` and a ``Temp`` column.

    Returns
    -------
    DataFrame
        Annual means indexed by year-start timestamp, offset by ``OCEAN_HEAT_BASELINE_OFFSET``.
    """
    annual = (
        seasonal.assign(Date=lambda x: pd.to_datetime(x["Date"], format="%Y-%m"))
        .set_index("Date")
        .resample("YE")
        .mean()
    )
    # Shifting the year-end label back also clears freq, which the CSV round-trip cannot carry.
    annual.index = pd.DatetimeIndex(annual.index) - pd.offsets.YearBegin()

    return annual + OCEAN_HEAT_BASELINE_OFFSET


def load_ocean_heat_data(cache_dir: Path, *, force_reload: bool = False) -> pd.DataFrame:
    def build() -> pd.DataFrame:
        raw = fetch(OCEAN_HEAT, cache_dir, force=force_reload)

        return transform_ocean_heat(pd.read_csv(raw, header=0, names=["Date", "Temp"]))

    return cached(cache_dir, "ocean_heat", build, pandas_csv(index_col="Date", parse_dates=True), force=force_reload)
