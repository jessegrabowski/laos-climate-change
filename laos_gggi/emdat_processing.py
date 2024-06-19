import pandas as pd
import os
from os.path import exists

from laos_gggi.const_vars import (
    INTENSITY_COLS,
    EM_DAT_COL_DICT,
    PROB_COLS,  # noqa
)  # noqa


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def process_emdat(data_path="data", force_reload=False):
    output_files = ["probability_data_set", "intensity_data_set"]  # noqa
    data_path = os.path.join(ROOT_DIR, data_path)

    if not exists(data_path):
        os.makedirs(data_path)

    emdat_path = os.path.join(data_path, "emdat.xlsx")
    if not exists(emdat_path):
        raise NotImplementedError(
            "No EM-DAT data was found at `/data/emdat.xlsx`. Please make an account at https://public.emdat.be/, download the database, and place it in `/data/emdat.xlsx`"
        )

    df = pd.read_excel(data_path + "/emdat.xlsx", sheet_name="EM-DAT Data").rename(
        columns=EM_DAT_COL_DICT
    )
    # Raw versions
    df_raw = df

    df_raw_filtered = df.query(
        "Total_Affected >1000 &  Deaths >100 & Start_Year > 1970"
    )

    df_raw_filtered_adj = df.query("Total_Affected >1000 & Start_Year > 1970")

    # df_prob_unfiltered
    df_prob_unfiltered = (
        df_raw.copy()
        .query("`Disaster Type` in @PROB_COLS")
        .groupby(["Disaster Type", "ISO", "Start_Year", "Region", "Subregion"])
        .size()
        .unstack("Disaster Type")
        .fillna(0)
        .astype(int)
        .reset_index()
        .set_index(["ISO", "Start_Year"])
        .sort_index()
    )

    # df_prob_filtered
    df_prob_filtered = (
        df_raw_filtered.copy()
        .query("`Disaster Type` in @PROB_COLS")
        .groupby(["Disaster Type", "ISO", "Start_Year", "Region", "Subregion"])
        .size()
        .unstack("Disaster Type")
        .fillna(0)
        .astype(int)
        .reset_index()
        .set_index(["ISO", "Start_Year"])
        .sort_index()
    )

    # df_prob_filtered_adjusted
    df_prob_filtered_adjusted = (
        df_raw_filtered_adj.copy()
        .query("`Disaster Type` in @PROB_COLS")
        .groupby(["Disaster Type", "ISO", "Start_Year", "Region", "Subregion"])
        .size()
        .unstack("Disaster Type")
        .fillna(0)
        .astype(int)
        .reset_index()
        .set_index(["ISO", "Start_Year"])
        .sort_index()
    )

    # df_inten_unfiltered
    df_inten_unfiltered = (
        df_raw.copy()
        .query("`Disaster Type` in @PROB_COLS")[INTENSITY_COLS]
        .set_index(["ISO", "Start_Year"])
        .sort_index()
    )

    # df_inten_filtered
    df_inten_filtered = (
        df_raw_filtered.copy()
        .query("`Disaster Type` in @PROB_COLS")[INTENSITY_COLS]
        .set_index(["ISO", "Start_Year"])
        .sort_index()
    )

    # df_inten_filtered_adjusted
    df_inten_filtered_adjusted = (
        df_raw_filtered_adj.copy()
        .query("`Disaster Type` in @PROB_COLS")[INTENSITY_COLS]
        .set_index(["ISO", "Start_Year"])
        .sort_index()
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
    }
    return result
