import os
from os.path import exists
from urllib.request import urlretrieve
from const_vars import GDP_PER_CAPITA_CONSTANT_URL, POPULATION_DENSITY_URL
import pandas as pd


def download_wb_data(output_path="../data"):
    path_to_population_density = (
        output_path + "/API_EN.POP.DNST_DS2_en_csv_v2_552619.zip"
    )
    path_to_gdp_per_capita_real = (
        output_path + "/API_NY.GDP.PCAP.KD_DS2_en_csv_v2_552878.zip"
    )
    path_to_wb_data = output_path + "/world_bank.csv"
    if not exists(output_path):
        os.makedirs(output_path)
        urlretrieve(POPULATION_DENSITY_URL, path_to_population_density)

    if not exists(path_to_population_density):
        urlretrieve(POPULATION_DENSITY_URL, path_to_population_density)

    if not exists(path_to_gdp_per_capita_real):
        urlretrieve(GDP_PER_CAPITA_CONSTANT_URL, path_to_gdp_per_capita_real)

    if not exists(output_path + "/API_EN.POP.DNST_DS2_en_csv_v2_553809.csv"):
        raise NotImplementedError("Unzip the population file")

    if not exists(output_path + "/API_NY.GDP.PCAP.KD_DS2_en_csv_v2_552878.csv"):
        raise NotImplementedError("Unzip the GDP per Capita file")

    if not exists(output_path + "/world_bank.csv"):
        population_density = pd.read_csv(
            "../data/API_EN.POP.DNST_DS2_en_csv_v2_553809.csv", skiprows=[0, 1, 2, 3]
        )
        gdp_per_cap = pd.read_csv(
            "../data/API_NY.GDP.PCAP.KD_DS2_en_csv_v2_552878.csv", skiprows=[0, 1, 2, 3]
        )

        population_density = (
            population_density.drop(
                ["Country Name", "Indicator Code", "Indicator Name"], axis=1
            )
            .melt(id_vars=["Country Code"])
            .rename(
                columns={
                    "Country Code": "Country",
                    "variable": "Year",
                    "value": "Population_density",
                }
            )
            .set_index(["Country", "Year"])
            .sort_index()
        )

        gdp_per_cap = (
            gdp_per_cap.drop(
                ["Country Name", "Indicator Code", "Indicator Name"], axis=1
            )
            .melt(id_vars=["Country Code"])
            .rename(
                columns={
                    "Country Code": "Country",
                    "variable": "Year",
                    "value": "gdp_per_cap_real",
                }
            )
            .set_index(["Country", "Year"])
            .sort_index()
        )

        world_bank_file = pd.merge(
            population_density,
            gdp_per_cap,
            left_index=True,
            right_index=True,
            how="inner",
        )

    if exists(path_to_wb_data):
        world_bank_file = pd.read_csv(path_to_wb_data)

    return (world_bank_file, world_bank_file.to_csv(path_to_wb_data))
