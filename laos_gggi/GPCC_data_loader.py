import os
from os.path import exists
from urllib.request import urlretrieve
from const_vars import GPCC_URL
import xarray as xr


def download_gpcc_data(output_path="../data"):
    path_to_GPCC_raw = output_path + "/precip.mon.nobs.1x1.v7.nc"
    path_to_GPCC = output_path + "/gpcc_precipitation.csv"
    if not exists(output_path):
        os.makedirs(output_path)
        urlretrieve(GPCC_URL, path_to_GPCC_raw)

    if not exists(path_to_GPCC_raw):
        urlretrieve(GPCC_URL, path_to_GPCC_raw)

    if not exists(path_to_GPCC):
        data = xr.open_dataset("../data" + "/precip.mon.nobs.1x1.v7.nc")
        df = data["precip"].to_dataframe()
        df = df.reset_index()
        df["Country"] = "?"

    return df
