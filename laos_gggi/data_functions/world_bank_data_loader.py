from pyprojroot import here
import os
from os.path import exists
from pandas_datareader import wb
import pandas as pd
from laos_gggi.const_vars import (
    COUNTRIES_ISO,
    ISO_DICTIONARY,
    WB_INDICATORS,
    WB_RENAME_DICT,
)
import logging


_log = logging.getLogger(__name__)


def load_wb_data(folder_path="data"):
    path_to_wb_data = here(os.path.join(folder_path, "world_bank.csv"))
    if not exists(folder_path):
        os.makedirs(folder_path)

    if not exists(path_to_wb_data):
        # Importing data
        wb_df = wb.download(
            indicator=WB_INDICATORS,
            country=COUNTRIES_ISO,
            start="1900",
            end=None,
        )
        wb_df.reset_index(inplace=True)
        # Adding country code
        wb_df["country_code"] = wb_df["country"].apply(ISO_DICTIONARY.get)
        # Formatting data
        wb_df = wb_df[["country_code", "year"] + WB_INDICATORS]
        wb_df.rename(
            columns=WB_RENAME_DICT,
            inplace=True,
        )
        wb_df = wb_df.set_index(["country_code", "year"]).sort_index()
        wb_df.to_csv(path_to_wb_data)

    else:
        wb_df = pd.read_csv(path_to_wb_data, index_col=["country_code", "year"])

    return wb_df
