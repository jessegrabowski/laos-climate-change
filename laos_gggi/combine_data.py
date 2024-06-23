import pandas as pd
import sys

sys.path.append("..")
from emdat_processing import process_emdat
from world_bank_data_loader import download_wb_data
from GPCC_data_loader import download_gpcc_data
from co2_processing import process_co2
from ocean_heat_processing import load_ocean_heat


def final_data():
    # Create the dictionary that contains the combined files
    merged_dict = {}

    # 1. EM-DAT data representing number of events per year (index: Year, ISO3)
    emdat = process_emdat()
    merged_dict["emdat_events"] = emdat["df_prob_filtered_adjusted"].drop(
        columns=["Region", "Subregion"]
    )

    # 2. EM-DAT data representing the event damages (index: Year, ISO3)
    merged_dict["emdat_damage"] = emdat["df_inten_filtered_adjusted"].drop(
        columns=["Country", "Region"]
    )

    # 3. The WB data, index (Year, ISO3)
    merged_dict["wb_data"] = download_wb_data()

    # 4 A single dataframe containing all of the timeseries-only data: GPCC + NOAA + NECI, index: Year
    # 4.1 GPCC: precipitation
    gpcc = download_gpcc_data()
    gpcc = gpcc.reset_index().rename(columns={"country_code": "ISO"})
    gpcc["year"] = pd.to_datetime(gpcc["time"]).dt.year
    merged_dict["gpcc"] = gpcc.pivot_table(values="precip", index="year", aggfunc="sum")

    # 4.2 NOAA: CO2
    co2 = process_co2()
    co2.reset_index(inplace=True)
    co2["year"] = co2["Date"].dt.year
    merged_dict["co2"] = co2.pivot_table(values="co2", index="year", aggfunc="sum")

    # 4.3 NECI: ocean temperature
    ocean_heat = load_ocean_heat()
    ocean_heat.reset_index(inplace=True)
    ocean_heat["year"] = ocean_heat["Date"].dt.year
    merged_dict["ocean_temperature"] = ocean_heat.pivot_table(
        values="Temp", index="year", aggfunc="mean"
    )

    return merged_dict
