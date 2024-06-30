import pandas as pd
import os
from os.path import exists
from laos_gggi.const_vars import OCEAN_HEAT_FILENAME, OCEAN_HEAT_URL
import logging

_log = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_ocean_heat(output_path="data", force_reload=False):
    output_path = os.path.join(ROOT_DIR, output_path)

    if not exists(output_path):
        os.makedirs(output_path)

    file_path = os.path.join(output_path, OCEAN_HEAT_FILENAME)

    if not os.path.isfile(os.path.join(file_path, OCEAN_HEAT_FILENAME)):
        df_ocean = pd.read_csv(OCEAN_HEAT_URL, header=0, names=["Date", "Temp"])
        df_ocean.Date = pd.to_datetime(df_ocean.Date, format="%Y-%m")
        df_ocean.set_index("Date", inplace=True)
        df_ocean = df_ocean.resample("YE").mean()
        df_ocean.reset_index(inplace=True)
        df_ocean["Date"] = df_ocean["Date"] - pd.offsets.YearBegin()
        df_ocean.set_index("Date", inplace=True)
        df_ocean = df_ocean.iloc[1:-1]
        df_ocean = df_ocean + 152
        df_ocean.to_csv(os.path.join(file_path, OCEAN_HEAT_FILENAME))

    else:
        df_ocean = pd.read_csv(
            os.path.join(output_path, OCEAN_HEAT_FILENAME),
            index_col=["Date"],
            parse_dates=True,
        )

    return df_ocean
