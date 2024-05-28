import os
from os.path import exists
from pandas_datareader import wb
import pandas as pd
from const_vars import COUNTRIES_ISO, ISO_DICTIONARY


def download_wb_data(output_path="../data"):
    path_to_wb_data = output_path + "/world_bank.csv"
    if not exists(output_path):
        os.makedirs(output_path)
        # Importing data
        wb_df = wb.download(
            indicator=["EN.POP.DNST", "NY.GDP.PCAP.KD"],
            country=COUNTRIES_ISO,
            start="1900",
            end=None,
        )
        wb_df.reset_index(inplace=True)
        # Adding country code
        wb_df["country_code"] = wb_df["country"].apply(ISO_DICTIONARY.get)
        # Formatting data
        wb_df = wb_df[["country_code", "year", "NY.GDP.PCAP.KD", "EN.POP.DNST"]]
        wb_df.rename(
            columns={
                "EN.POP.DNST": "population_density",
                "NY.GDP.PCAP.KD": "gdp_per_cap",
            },
            inplace=True,
        )
        wb_df = wb_df.set_index(["country_code", "year"]).sort_index()
        wb_df.to_csv(path_to_wb_data)

    if not exists(path_to_wb_data):
        # Importing data
        wb_df = wb.download(
            indicator=["EN.POP.DNST", "NY.GDP.PCAP.KD"],
            country=COUNTRIES_ISO,
            start="1900",
            end=None,
        )
        wb_df.reset_index(inplace=True)
        # Adding country code
        wb_df["country_code"] = wb_df["country"].apply(ISO_DICTIONARY.get)
        # Formatting data
        wb_df = wb_df[["country_code", "year", "NY.GDP.PCAP.KD", "EN.POP.DNST"]]
        wb_df.rename(
            columns={
                "EN.POP.DNST": "population_density",
                "NY.GDP.PCAP.KD": "gdp_per_cap",
            },
            inplace=True,
        )
        wb_df = wb_df.set_index(["country_code", "year"]).sort_index()
        wb_df.to_csv(path_to_wb_data)

    else:
        wb_df = pd.read_csv(path_to_wb_data, index_col=["country_code", "year"])

    return wb_df
