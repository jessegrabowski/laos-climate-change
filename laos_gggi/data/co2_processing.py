import pandas as pd
import os
from os.path import exists
from laos_gggi.const_vars import CO2_URL, CO2_FILENAME


def load_co2_data(data_path="../data"):
    if not exists(data_path):
        os.makedirs(data_path)

    if not os.path.isfile(os.path.join(data_path, CO2_FILENAME)):
        df_co2 = pd.read_csv(CO2_URL, skiprows=43)
        df_co2["month"] = 1
        df_co2["day"] = 1
        df_co2["Date"] = pd.to_datetime(df_co2[["year", "month", "day"]])
        df_co2.set_index("Date", inplace=True)
        df_co2.rename(columns={"mean": "co2"}, inplace=True)
        df_co2 = df_co2[["co2"]]
        df_co2.to_csv(os.path.join(data_path, CO2_FILENAME))

    else:
        df_co2 = pd.read_csv(
            os.path.join(data_path, CO2_FILENAME), index_col=["Date"], parse_dates=True
        )

    return df_co2
