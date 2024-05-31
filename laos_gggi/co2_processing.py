import pandas as pd
import os
from os.path import exists
from const_vars import CO2_URL, CO2_FILENAME


def process_co2(data_path="../data"):
    if not exists(data_path):
        os.makedirs(data_path)

    if not os.path.isfile(data_path + "/" + CO2_FILENAME):
        url = CO2_URL
        df_co2 = pd.read_csv(url, skiprows=38)
        df_co2["Date"] = df_co2.apply(
            lambda x: pd.to_datetime(f"{x.year}-{x.month}", format="%Y-%m", axis=1)
        )
        df_co2.set_index("Date", inplace=True)
        df_co2.rename(columns={"average": "co2"}, inplace=True)
        df_co2 = df_co2[["co2"]]
        df_co2.to_csv(data_path + "/" + CO2_FILENAME)

    else:
        df_co2 = pd.read_csv(
            data_path + "/" + CO2_FILENAME, index_col=["Date"], parse_dates=True
        )

    return df_co2
