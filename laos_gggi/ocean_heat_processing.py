import pandas as pd
import os
from os.path import exists
from const_vars import OCEAN_HEAT_FILENAME


def process_ocean_heat(data_path="../data"):
    if not exists(data_path):
        os.makedirs(data_path)

    if not os.path.isfile(data_path + "/" + OCEAN_HEAT_FILENAME):
        url = "OCEAN_HEAT_URL"
        df_ocean = pd.read_csv(url, header=None)
        df_ocean.rename(columns={0: "Date", 1: "Temp"}, inplace=True)
        df_ocean.Date = pd.to_datetime(df_ocean.Date)
        df_ocean.set_index("Date", inplace=True)
        df_ocean.to_csv(data_path + "/" + OCEAN_HEAT_FILENAME)

    else:
        df_ocean = pd.read_csv(
            data_path + "/" + OCEAN_HEAT_FILENAME, index_col=["Date"], parse_dates=True
        )

    return df_ocean
