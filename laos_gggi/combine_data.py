import pandas as pd
from laos_gggi.emdat_processing import process_emdat
from laos_gggi.world_bank_data_loader import download_wb_data
from laos_gggi.GPCC_data_loader import download_gpcc_data
from laos_gggi.co2_processing import process_co2
from laos_gggi.ocean_heat_processing import load_ocean_heat


def final_data():
    # Create the dictionary that contains the combined files
    merged_dict = {}

    # 1. EM-DAT data representing number of events per year (index: Year, ISO3)
    emdat = process_emdat()
    merged_dict["emdat_events"] = emdat["df_prob_filtered_adjusted"].drop(
        ["Subregion"], axis=1
    )

    # 2. EM-DAT data representing the event damages (index: Year, ISO3)
    merged_dict["emdat_damage"] = emdat["df_inten_filtered_adjusted"].drop(
        ["Country", "Region"], axis=1
    )

    # 3. The WB data, index (Year, ISO3)
    merged_dict["wb_data"] = download_wb_data()
    merged_dict["wb_data"] = (
        merged_dict["wb_data"]
        .reset_index()
        .rename(columns={"country_code": "ISO", "year": "Start_Year"})
        .set_index(["ISO", "Start_Year"])
    )
    # 4 A single dataframe containing all of the timeseries-only data: GPCC + NOAA + NECI, index: Year
    # 4.1 GPCC: precipitation
    gpcc = download_gpcc_data()
    gpcc = gpcc.reset_index().rename(columns={"country_code": "ISO"})
    gpcc["year"] = pd.to_datetime(gpcc["time"]).dt.year
    merged_dict["gpcc"] = gpcc.pivot_table(
        values="precip", index=["ISO", "year"], aggfunc="sum"
    )
    merged_dict["gpcc_agg"] = gpcc.pivot_table(
        values="precip", index=["year"], aggfunc="sum"
    )

    # 4.2 NOAA: CO2
    co2 = process_co2()
    co2.reset_index(inplace=True)
    co2["year"] = co2["Date"].dt.year
    merged_dict["co2"] = co2.pivot_table(values="co2", index="year", aggfunc="sum")

    # 4.3 NECI: ocean temperature
    ocean_heat = load_ocean_heat()
    ocean_heat["year"] = ocean_heat.reset_index()["Date"].dt.year.values
    ocean_heat = ocean_heat.pivot_table(values="Temp", index="year", aggfunc="mean")
    merged_dict["ocean_temperature"] = ocean_heat
    # ISO reconciliation: emdat and world
    emdat_iso = merged_dict["emdat_damage"].index.get_level_values(0).unique()
    world_iso = merged_dict["wb_data"].index.get_level_values(0).unique()
    # Codes in EMDAT but not in world
    ", ".join(list(set(emdat_iso) - set(world_iso)))
    # Codes in shapefile but not in EMDAT
    ", ".join(list(set(world_iso) - set(emdat_iso)))
    # Drop codes not in both
    common_codes = set(world_iso).intersection(set(emdat_iso))
    merged_dict["emdat_damage"] = (
        merged_dict["emdat_damage"]
        .loc[lambda x: x.index.get_level_values(0).isin(common_codes)]
        .copy()
    )

    merged_dict["emdat_events"] = (
        merged_dict["emdat_events"]
        .loc[lambda x: x.index.get_level_values(0).isin(common_codes)]
        .copy()
        .drop(columns=["Region"])
    )

    merged_dict["wb_data"] = (
        merged_dict["wb_data"]
        .loc[merged_dict["wb_data"].index.get_level_values(0).isin(common_codes)]
        .copy()
    )

    # ISO reconciliation: gpcc
    merged_dict_iso = merged_dict["wb_data"].index.get_level_values(0).unique()
    gpcc_iso = merged_dict["gpcc"].index.get_level_values(0).unique()
    # Codes in gpcc but not in world
    ", ".join(list(set(gpcc_iso) - set(merged_dict_iso)))
    # Codes in world but not in gpcc
    ", ".join(list(set(merged_dict_iso) - set(gpcc_iso)))

    # Drop codes not in both
    common_codes2 = set(merged_dict_iso).intersection(set(gpcc_iso))
    merged_dict["emdat_damage"] = (
        merged_dict["emdat_damage"]
        .loc[lambda x: x.index.get_level_values(0).isin(common_codes)]
        .copy()
    )

    merged_dict["gpcc"] = (
        merged_dict["gpcc"]
        .loc[lambda x: x.index.get_level_values(0).isin(common_codes2)]
        .copy()
    )
    merged_dict["emdat_damage"] = (
        merged_dict["emdat_damage"]
        .loc[lambda x: x.index.get_level_values(0).isin(common_codes2)]
        .copy()
    )

    merged_dict["emdat_events"] = (
        merged_dict["emdat_events"]
        .loc[lambda x: x.index.get_level_values(0).isin(common_codes2)]
        .copy()
    )

    merged_dict["wb_data"] = (
        merged_dict["wb_data"]
        .loc[merged_dict["wb_data"].index.get_level_values(0).isin(common_codes2)]
        .copy()
    )

    # 5 Country constants
    merged_dict["country_constants"] = (
        emdat["df_prob_filtered_adjusted"]
        .reset_index()
        .drop(
            [
                "Start_Year",
                "Drought",
                "Flood",
                "Storm",
                "Wildfire",
                "Extreme temperature",
            ],
            axis=1,
        )
        .drop_duplicates()
        .set_index("ISO")
    )

    # Merging panel data sets
    emdat_df = pd.merge(
        merged_dict["emdat_events"],
        merged_dict["emdat_damage"],
        right_index=True,
        left_index=True,
        how="outer",
    )
    merged_dict["df_panel"] = pd.merge(
        emdat_df, merged_dict["wb_data"], right_index=True, left_index=True, how="left"
    )
    merged_dict["df_panel"] = pd.merge(
        merged_dict["df_panel"],
        merged_dict["gpcc"]
        .reset_index()
        .rename(columns={"year": "Start_Year"})
        .set_index(["ISO", "Start_Year"]),
        right_index=True,
        left_index=True,
        how="left",
    )

    # Merging time series
    merged_dict["df_time_series"] = pd.merge(
        merged_dict["co2"],
        merged_dict["ocean_temperature"],
        left_index=True,
        right_index=True,
        how="outer",
    )

    merged_dict["df_time_series"] = pd.merge(
        merged_dict["df_time_series"],
        merged_dict["gpcc_agg"],
        left_index=True,
        right_index=True,
        how="outer",
    )

    return merged_dict
