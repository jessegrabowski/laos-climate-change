from pyprojroot import here
import numpy as np
import pandas as pd
import os
from os.path import exists

from laos_gggi.const_vars import (  # noqa
    INTENSITY_COLS,
    EM_DAT_COL_DICT,
    PROB_COLS,
)


def load_emdat_data(data_path="data", force_reload=False):
    output_files = ["probability_data_set", "intensity_data_set"]  # noqa
    data_path = here(data_path)

    if not exists(data_path):
        os.makedirs(data_path)

    emdat_path = os.path.join(data_path, "emdat.xlsx")
    if not exists(emdat_path):
        raise NotImplementedError(
            "No EM-DAT data was found at `/data/emdat.xlsx`. Please make an account at https://public.emdat.be/, "
            "download the database, and place it in `/data/emdat.xlsx`"
        )

    df_raw = (
        pd.read_excel(os.path.join(data_path, "emdat.xlsx"), sheet_name="EM-DAT Data")
        .rename(columns=EM_DAT_COL_DICT)
        .assign(Start_Year=lambda x: pd.to_datetime(x.Start_Year, format="%Y"))
    )

    disaster_class_dict = {
        "Storm": "Hydrometereological",
        "Flood": "Hydrometereological",
        "Wildfire": "Climatological",
        "Extreme temperature": "Climatological",
        "Drought": "Climatological",
    }

    df_raw["disaster_class"] = df_raw["Disaster Type"].map(disaster_class_dict.get)

    df_raw.loc[
        df_raw["Disaster Type"].isin(["Wildfire", "Extreme temperature", "Drought"]),
        "disaster_class",
    ] = "Climatological"

    # Useful constants
    region_dict = (
        df_raw[["ISO", "Region"]].drop_duplicates().set_index("ISO").to_dict()["Region"]
    )  #  noqa
    subregion_dict = (
        df_raw[["ISO", "Subregion"]]
        .drop_duplicates()
        .set_index("ISO")
        .to_dict()["Subregion"]
    )  #  noqa
    years = pd.date_range(start="1969-01-01", end="2024-01-01", freq="YS-JAN")
    ISO_codes = df_raw["ISO"].unique()

    # Define the complete combination of years and ISO codes
    complete_index = pd.MultiIndex.from_product(
        [ISO_codes, years], names=["ISO", "Start_Year"]
    ).sort_values()

    # Raw versions
    df_raw_filtered = df_raw.query(
        "Total_Affected >1000 &  Deaths >100 & Start_Year > 1970"
    )
    df_raw_filtered_adj = df_raw.query("Total_Affected >1000 & Start_Year > 1970")

    def process_prob_df(df):
        result = (
            df.copy()
            .query("`Disaster Type` in @PROB_COLS")
            .groupby(["Disaster Type", "ISO", "Start_Year", "Region", "Subregion"])
            .size()
            .unstack("Disaster Type")
            .reset_index()
            .set_index(["ISO", "Start_Year"])
            .sort_index()
            .reindex(complete_index)
            .assign(
                Region=lambda x: x.index.get_level_values(0).map(region_dict.get),
                Subregion=lambda x: x.index.get_level_values(0).map(subregion_dict.get),
            )
            .fillna(0)
            .sort_index()
        )

        assert result.shape[0] == len(complete_index)
        assert np.all(
            result.index.get_level_values(0) == complete_index.get_level_values(0)
        )
        assert np.all(
            result.index.get_level_values(1) == complete_index.get_level_values(1)
        )
        return result

    df_prob_unfiltered = process_prob_df(df_raw)
    df_prob_filtered = process_prob_df(df_raw_filtered)
    df_prob_filtered_adjusted = process_prob_df(df_raw_filtered_adj)

    damage_vars = [
        "Deaths",
        "Injured",
        "Numb_Affected",
        "Homeless",
        "Total_Affected",
        "Total_Damage",
        "Total_Damage_Adjusted",
    ]

    def process_damage_df(df):
        result = (
            df.copy()
            .query("`Disaster Type` in @PROB_COLS")[INTENSITY_COLS]
            .pivot_table(index=["ISO", "Start_Year"], values=damage_vars, aggfunc="sum")
            .sort_index()
            .reindex(complete_index)
            .assign(
                Region=lambda x: x.index.get_level_values(0).map(region_dict.get),
                Subregion=lambda x: x.index.get_level_values(0).map(subregion_dict.get),
            )
            .sort_index()
            .fillna(0)
        )
        assert result.shape[0] == len(complete_index)
        assert np.all(
            result.index.get_level_values(0) == complete_index.get_level_values(0)
        )
        assert np.all(
            result.index.get_level_values(1) == complete_index.get_level_values(1)
        )

        return result

    df_inten_unfiltered = process_damage_df(df_raw)
    df_inten_filtered = process_damage_df(df_raw_filtered)
    df_inten_filtered_adjusted = process_damage_df(df_raw_filtered_adj)
    df_inten_filtered_adjusted_hydro = process_damage_df(
        df_raw_filtered_adj.query('disaster_class == "Hydrometereological"')
    )
    df_inten_filtered_adjusted_clim = process_damage_df(
        df_raw_filtered_adj.query('disaster_class == "Climatological"')
    )

    result = {
        "df_raw": df_raw,
        "df_raw_filtered": df_raw_filtered,
        "df_raw_filtered_adj": df_raw_filtered_adj,
        "df_prob_unfiltered": df_prob_unfiltered,
        "df_prob_filtered": df_prob_filtered,
        "df_prob_filtered_adjusted": df_prob_filtered_adjusted,
        "df_inten_unfiltered": df_inten_unfiltered,
        "df_inten_filtered": df_inten_filtered,
        "df_inten_filtered_adjusted": df_inten_filtered_adjusted,
        "df_inten_filtered_adjusted_hydro": df_inten_filtered_adjusted_hydro,
        "df_inten_filtered_adjusted_clim": df_inten_filtered_adjusted_clim,
    }

    return result
