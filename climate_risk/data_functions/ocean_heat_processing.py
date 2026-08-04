from pathlib import Path

import pandas as pd

from climate_risk.const_vars import OCEAN_HEAT_FILENAME, OCEAN_HEAT_URL


def load_ocean_heat_data(cache_dir: Path, *, force_reload: bool = False) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)

    ocean_heat_path = cache_dir / OCEAN_HEAT_FILENAME

    if not ocean_heat_path.is_file() or force_reload:
        df_ocean = pd.read_csv(OCEAN_HEAT_URL, header=0, names=["Date", "Temp"])
        df_ocean.Date = pd.to_datetime(df_ocean.Date, format="%Y-%m")
        df_ocean.set_index("Date", inplace=True)
        df_ocean = df_ocean.resample("YE").mean()
        df_ocean.reset_index(inplace=True)
        df_ocean["Date"] = df_ocean["Date"] - pd.offsets.YearBegin()
        df_ocean.set_index("Date", inplace=True)
        df_ocean = df_ocean + 152
        df_ocean.to_csv(ocean_heat_path)

    else:
        df_ocean = pd.read_csv(ocean_heat_path, index_col=["Date"], parse_dates=True)

    return df_ocean
