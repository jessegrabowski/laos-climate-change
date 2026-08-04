from pathlib import Path

import pandas as pd

from climate_risk.const_vars import CO2_FILENAME, CO2_URL


def load_co2_data(cache_dir: Path) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)

    co2_path = cache_dir / CO2_FILENAME

    if not co2_path.is_file():
        df_co2 = pd.read_csv(CO2_URL, skiprows=43)
        df_co2["month"] = 1
        df_co2["day"] = 1
        df_co2["Date"] = pd.to_datetime(df_co2[["year", "month", "day"]])
        df_co2.set_index("Date", inplace=True)
        df_co2.rename(columns={"mean": "co2"}, inplace=True)
        df_co2 = df_co2[["co2"]]
        df_co2.to_csv(co2_path)

    else:
        df_co2 = pd.read_csv(co2_path, index_col=["Date"], parse_dates=True)

    return df_co2
