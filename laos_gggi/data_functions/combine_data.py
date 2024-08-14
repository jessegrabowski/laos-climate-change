import pandas as pd
from laos_gggi.data_functions.emdat_processing import load_emdat_data
from laos_gggi.data_functions.world_bank_data_loader import load_wb_data
from laos_gggi.data_functions.GPCC_data_loader import load_gpcc_data
from laos_gggi.data_functions.co2_processing import load_co2_data
from laos_gggi.data_functions.ocean_heat_processing import load_ocean_heat_data
from laos_gggi.data_functions.hadcrut_data_loader import load_hadcrut_data
from functools import partial, reduce


def load_all_data():
    # Create the dictionary that contains the combined files
    merged_dict = {}

    # 1. EM-DAT data representing number of events per year (index: Year, ISO3)
    emdat = load_emdat_data()
    merged_dict["emdat_events"] = emdat["df_prob_filtered_adjusted"].drop(
        columns=["Subregion"]
    )

    # 2. EM-DAT data representing the event damages (index: Year, ISO3)
    merged_dict["emdat_damage"] = emdat["df_inten_filtered_adjusted"]

    emdat["df_inten_filtered_adjusted_hydro"] = (
        emdat["df_inten_filtered_adjusted_hydro"]
        .drop(columns=["Region", "Subregion"])
        .rename(columns=lambda x: f"{x}_hydro")
    )

    emdat["df_inten_filtered_adjusted_clim"] = (
        emdat["df_inten_filtered_adjusted_clim"]
        .drop(columns=["Region", "Subregion"])
        .rename(columns=lambda x: f"{x}_clim")
    )

    merged_dict["emdat_damage"] = pd.merge(
        merged_dict["emdat_damage"],
        emdat["df_inten_filtered_adjusted_hydro"],
        left_index=True,
        right_index=True,
        how="left",
    )

    merged_dict["emdat_damage"] = pd.merge(
        merged_dict["emdat_damage"],
        emdat["df_inten_filtered_adjusted_clim"],
        left_index=True,
        right_index=True,
        how="left",
    )

    merged_dict["df_inten_filtered_adjusted_hydro"] = emdat[
        "df_inten_filtered_adjusted_hydro"
    ]
    merged_dict["df_inten_filtered_adjusted_clim"] = emdat[
        "df_inten_filtered_adjusted_hydro"
    ]

    # 3. The WB data, index (Year, ISO3)
    merged_dict["wb_data"] = load_wb_data()
    merged_dict["wb_data"] = (
        merged_dict["wb_data"]
        .reset_index()
        .rename(columns={"country_code": "ISO", "year": "Start_Year"})
        .assign(Start_Year=lambda x: pd.to_datetime(x.Start_Year, format="%Y"))
        .set_index(["ISO", "Start_Year"])
    )
    # 4 A single dataframe containing all of the timeseries-only data: GPCC + NOAA + NECI, index: Year
    # 4.1 GPCC: precipitation
    gpcc = load_gpcc_data()
    gpcc = gpcc.reset_index().rename(columns={"country_code": "ISO"})
    gpcc["year"] = pd.to_datetime(pd.to_datetime(gpcc["time"]).dt.year, format="%Y")
    merged_dict["gpcc"] = gpcc.pivot_table(
        values="precip", index=["ISO", "year"], aggfunc="sum"
    )
    merged_dict["gpcc_agg"] = gpcc.pivot_table(
        values="precip", index=["year"], aggfunc="sum"
    )

    # 4.2 NOAA: CO2
    co2 = load_co2_data()
    co2.reset_index(inplace=True)
    co2["year"] = pd.to_datetime(co2["Date"].dt.year, format="%Y")
    merged_dict["co2"] = co2.pivot_table(values="co2", index="year", aggfunc="sum")

    # 4.3 NECI: ocean temperature
    ocean_heat = load_ocean_heat_data()
    ocean_heat["year"] = ocean_heat.reset_index()["Date"].dt.year.values
    ocean_heat = ocean_heat.pivot_table(values="Temp", index="year", aggfunc="mean")
    ocean_heat.index = pd.to_datetime(ocean_heat.index, format="%Y")
    merged_dict["ocean_temperature"] = ocean_heat

    # 4.4 HACRUT: surface temperature
    surface_temp = load_hadcrut_data()

    merged_dict["surface_temp"] = surface_temp
    merged_dict["surface_temp_agg"] = surface_temp.reset_index().pivot_table(
        values="surface_temperature_dev", index=["year"], aggfunc="mean"
    )

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
    # ISO reconciliation: hadcrut
    merged_dict_iso = merged_dict["wb_data"].index.get_level_values(0).unique()
    hadcrut_iso = merged_dict["surface_temp"].index.get_level_values(0).unique()

    # Drop codes not in both
    common_codes2 = set(merged_dict_iso).intersection(set(hadcrut_iso))

    merged_dict["surface_temp"] = (
        merged_dict["surface_temp"]
        .loc[lambda x: x.index.get_level_values(0).isin(common_codes2)]
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
    merge_func = partial(pd.merge, left_index=True, right_index=True, how="outer")  # noqa
    merged_dict["df_panel"] = reduce(
        lambda left, right: merge_func(left, right),
        [
            merged_dict["emdat_events"],
            merged_dict["emdat_damage"],
            merged_dict["wb_data"],
            (
                merged_dict["gpcc"]
                .reset_index()
                .rename(columns={"year": "Start_Year"})
                .set_index(["ISO", "Start_Year"])
            ),
            (
                merged_dict["surface_temp"]
                .reset_index()
                .rename(columns={"year": "Start_Year"})
                .set_index(["ISO", "Start_Year"])
            ),
        ],
    )

    # Merging time series
    merged_dict["df_time_series"] = reduce(
        lambda left, right: merge_func(left, right),
        [
            merged_dict["co2"],
            merged_dict["ocean_temperature"],
            merged_dict["gpcc_agg"],
            merged_dict["surface_temp_agg"],
        ],
    )

    return merged_dict
