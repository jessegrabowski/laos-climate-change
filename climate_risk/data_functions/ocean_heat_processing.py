from pathlib import Path

import pandas as pd

from climate_risk.const_vars import OCEAN_HEAT_FILENAME, OCEAN_HEAT_URL

# Shifts the NCEI anomalies onto the baseline the published results were estimated against. The
# derivation is unrecorded; changing it invalidates every downstream number.
OCEAN_HEAT_BASELINE_OFFSET = 152


def process_ocean_heat(monthly: pd.DataFrame) -> pd.DataFrame:
    """
    Average monthly ocean-heat anomalies to calendar years and shift them onto the project baseline.

    Parameters
    ----------
    monthly : DataFrame
        Monthly anomalies with a ``Date`` column formatted ``YYYY-MM`` and a ``Temp`` column.

    Returns
    -------
    DataFrame
        Annual means indexed by year-start timestamp, offset by ``OCEAN_HEAT_BASELINE_OFFSET``.
    """
    annual = (
        monthly.assign(Date=lambda x: pd.to_datetime(x["Date"], format="%Y-%m")).set_index("Date").resample("YE").mean()
    )
    annual.index = annual.index - pd.offsets.YearBegin()

    return annual + OCEAN_HEAT_BASELINE_OFFSET


def load_ocean_heat_data(cache_dir: Path, *, force_reload: bool = False) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)

    ocean_heat_path = cache_dir / OCEAN_HEAT_FILENAME

    if not ocean_heat_path.is_file() or force_reload:
        df_ocean = process_ocean_heat(pd.read_csv(OCEAN_HEAT_URL, header=0, names=["Date", "Temp"]))
        df_ocean.to_csv(ocean_heat_path)

    else:
        df_ocean = pd.read_csv(ocean_heat_path, index_col=["Date"], parse_dates=True)

    return df_ocean
