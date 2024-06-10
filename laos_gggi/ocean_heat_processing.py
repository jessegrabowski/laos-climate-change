import pandas as pd
import os
from os.path import exists
from const_vars import OCEAN_HEAT_FILENAME, OCEAN_HEAT_URL
import logging

_log = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def process_ocean_heat(output_path="data", force_reload=False):
    output_path = os.path.join(ROOT_DIR, output_path)

    if not exists(output_path):
        os.makedirs(output_path)

    file_path = os.path.join(output_path, OCEAN_HEAT_FILENAME)

    if not os.path.isfile(file_path) or force_reload:
        df_ocean = pd.read_csv(OCEAN_HEAT_URL, header=None)
        df_ocean.rename(columns={0: "Date", 1: "Temp"}, inplace=True)
        df_ocean.Date = pd.to_datetime(df_ocean.Date)
        df_ocean.set_index("Date", inplace=True)
        df_ocean.to_csv(file_path)

    else:
        df_ocean = pd.read_csv(
            file_path,
            index_col=["Date"],
            parse_dates=True,
        )

    return df_ocean
