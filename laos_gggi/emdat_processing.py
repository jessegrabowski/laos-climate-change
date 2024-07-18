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

    # Define the complete combination of years and ISO codes
    years = [*range(1969, 2024)]
    ISO_codes = df["ISO"].unique()
    complete_df = pd.DataFrame(
        columns=["col_1"],
        index=pd.MultiIndex.from_product(
            [ISO_codes, years],
            names=[
                "ISO",
                "Start_Year",
            ],
        ),
    ).sort_index()

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
    df_prob_unfiltered_B = (
        pd.merge(
            complete_df,
            df_prob_unfiltered[
                ["Drought", "Extreme temperature", "Flood", "Storm", "Wildfire"]
            ],
            right_index=True,
            left_index=True,
            how="left",
        )
        .reset_index()
        .set_index(["ISO"])
    )

    df_prob_unfiltered = (
        (
            pd.merge(
                df_prob_unfiltered_B,
                df_prob_unfiltered.reset_index()
                .set_index("ISO")[["Region", "Subregion"]]
                .drop_duplicates(),
                right_index=True,
                left_index=True,
                how="left",
            )
        )
        .reset_index()
        .set_index(["ISO", "Start_Year"])
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
    df_prob_filtered_B = (
        pd.merge(
            complete_df,
            df_prob_filtered[
                ["Drought", "Extreme temperature", "Flood", "Storm", "Wildfire"]
            ],
            right_index=True,
            left_index=True,
            how="left",
        )
        .reset_index()
        .set_index(["ISO"])
    )

    df_prob_filtered = (
        (
            pd.merge(
                df_prob_filtered_B,
                df_prob_filtered.reset_index()
                .set_index("ISO")[["Region", "Subregion"]]
                .drop_duplicates(),
                right_index=True,
                left_index=True,
                how="left",
            )
        )
        .reset_index()
        .set_index(["ISO", "Start_Year"])
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
    df_prob_filtered_adjusted_B = (
        pd.merge(
            complete_df,
            df_prob_filtered_adjusted[
                ["Drought", "Extreme temperature", "Flood", "Storm", "Wildfire"]
            ],
            right_index=True,
            left_index=True,
            how="left",
        )
        .reset_index()
        .set_index(["ISO"])
    )

    df_prob_filtered_adjusted = (
        (
            pd.merge(
                df_prob_filtered_adjusted_B,
                df_prob_filtered_adjusted.reset_index()
                .set_index("ISO")[["Region", "Subregion"]]
                .drop_duplicates(),
                right_index=True,
                left_index=True,
                how="left",
            )
        )
        .reset_index()
        .set_index(["ISO", "Start_Year"])
    )

    # df_inten_unfiltered
    damage_vars = [
        "Deaths",
        "Injured",
        "Numb_Affected",
        "Homeless",
        "Total_Affected",
        "Total_Damage",
        "Total_Damage_Adjusted",
    ]

    df_inten_unfiltered = (
        df_raw.copy()
        .query("`Disaster Type` in @PROB_COLS")[INTENSITY_COLS]
        .pivot_table(index=["ISO", "Start_Year"], values=damage_vars, aggfunc="sum")
        .fillna(0)
        .astype(int)
        .sort_index()
    )

    df_inten_unfiltered = (
        pd.merge(
            complete_df,
            df_inten_unfiltered[
                [
                    "Deaths",
                    "Injured",
                    "Numb_Affected",
                    "Homeless",
                    "Total_Affected",
                    "Total_Damage",
                    "Total_Damage_Adjusted",
                ]
            ],
            right_index=True,
            left_index=True,
            how="left",
        )
        .reset_index()
        .set_index(["ISO", "Start_Year"])
    )

    # df_inten_filtered
    df_inten_filtered = (
        df_raw_filtered.copy()
        .query("`Disaster Type` in @PROB_COLS")[INTENSITY_COLS]
        .pivot_table(index=["ISO", "Start_Year"], values=damage_vars, aggfunc="sum")
        .fillna(0)
        .astype(int)
        .sort_index()
    )

    df_inten_filtered = (
        pd.merge(
            complete_df,
            df_inten_filtered[
                [
                    "Deaths",
                    "Injured",
                    "Numb_Affected",
                    "Homeless",
                    "Total_Affected",
                    "Total_Damage",
                    "Total_Damage_Adjusted",
                ]
            ],
            right_index=True,
            left_index=True,
            how="left",
        )
        .reset_index()
        .set_index(["ISO", "Start_Year"])
    )

    # df_inten_filtered_adjusted
    df_inten_filtered_adjusted = (
        df_raw_filtered_adj.copy()
        .query("`Disaster Type` in @PROB_COLS")[INTENSITY_COLS]
        .pivot_table(index=["ISO", "Start_Year"], values=damage_vars, aggfunc="sum")
        .fillna(0)
        .astype(int)
        .sort_index()
    )

    df_inten_filtered_adjusted = (
        pd.merge(
            complete_df,
            df_inten_filtered_adjusted[
                [
                    "Deaths",
                    "Injured",
                    "Numb_Affected",
                    "Homeless",
                    "Total_Affected",
                    "Total_Damage",
                    "Total_Damage_Adjusted",
                ]
            ],
            right_index=True,
            left_index=True,
            how="left",
        )
        .reset_index()
        .set_index(["ISO", "Start_Year"])
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
