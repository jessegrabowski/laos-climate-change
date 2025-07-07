# Imports
from pyprojroot import here
import pandas as pd
from urllib.request import urlretrieve
import os
from os.path import exists
import logging
from laos_gggi.data_functions.combine_data import load_all_data
from laos_gggi.const_vars import (
    IPCC_PREDICTIONS_RAW_NAME,
    IPCC_URL,
    IPCC_COLS,
    IPCC_RENAME_DICT,
)

_log = logging.getLogger(__name__)


def process_ipcc_scenarios(data_path=None, force_reload: bool = False):
    # Define data path
    if data_path is None:
        data_path = here("data")
    if not exists(data_path) or force_reload:
        os.makedirs(data_path)  # create it if not exists

    path_to_raw_file = os.path.join(data_path, IPCC_PREDICTIONS_RAW_NAME)

    # Verify if the raw data file exists
    if not os.path.isfile(os.path.join(data_path, path_to_raw_file)):
        _log.info("Downloading IPCC predictions raw  data")
        urlretrieve(IPCC_URL, path_to_raw_file)

    # Load raw data file:
    ipcc_preds = pd.read_excel(path_to_raw_file, sheet_name="CO2 Emissions")[IPCC_COLS]
    # Rename columns
    ipcc_preds = ipcc_preds.rename(columns=IPCC_RENAME_DICT)

    # Load co2 observations data
    co2_data = load_all_data()["df_time_series"][["co2"]].reset_index()
    co2_data["year_"] = co2_data["year"].dt.year.drop(columns=["year"])
    co2_data = co2_data.drop(columns=["year"])

    ipcc_preds_proc = pd.merge(
        ipcc_preds, co2_data, left_on="year", right_on="year_", how="left"
    ).drop(columns=["year_"])

    # Adjust col names
    scenario_change_cols = (
        ["year"]
        + [x + "_change" for x in list(ipcc_preds_proc.columns)[1:-1]]
        + ["co2"]
    )
    ipcc_preds_proc.columns = scenario_change_cols

    years = ipcc_preds_proc["year"].values

    ipcc_preds_proc = ipcc_preds_proc.set_index("year")
    scenario_value_cols = [x[:-7] for x in list(ipcc_preds_proc.columns)[:-1]]

    # Compute the values
    for col in scenario_value_cols:
        for y in years:
            if y == 2015:
                ipcc_preds_proc.loc[y, col] = ipcc_preds_proc.loc[2015, "co2"]
            elif y == 2020:
                ipcc_preds_proc.loc[y, col] = ipcc_preds_proc.loc[2020, "co2"]
            elif y != 2020 and y != 2101:
                ipcc_preds_proc.loc[y, col] = (
                    ipcc_preds_proc.loc[y, col + "_change"]
                    + ipcc_preds_proc.loc[y - 5, col]
                )

    # Extend data to all the years
    years_index = pd.date_range(start="2020-01-01", end="2101-01-01", freq="YE").year
    ipcc_preds_proc_ext = ipcc_preds_proc.reindex(years_index)

    # Interpolate vaulues
    ipcc_preds_proc_ext = ipcc_preds_proc_ext.interpolate(method="linear").drop(
        columns=["co2"]
    )

    return ipcc_preds_proc_ext
