from pathlib import Path

import numpy as np
import pandas as pd

from climate_risk.const_vars import (
    EM_DAT_COL_DICT,
    INTENSITY_COLS,
    PROB_COLS,  # noqa: F401  -- referenced as @PROB_COLS inside pandas query strings
)

# The study window opens in 1969 and closes on the newest event in the workbook.
EMDAT_WINDOW_START = "1969-01-01"


def load_emdat_data(
    cache_dir: Path,
    *,
    force_reload: bool = False,
    window_start: str | pd.Timestamp = EMDAT_WINDOW_START,
) -> dict[str, pd.DataFrame]:
    cache_dir.mkdir(parents=True, exist_ok=True)

    emdat_path = cache_dir / "emdat.xlsx"
    if not emdat_path.exists():
        raise NotImplementedError(
            f"No EM-DAT data was found at `{emdat_path}`. Please make an account at https://public.emdat.be/, "
            f"download the database, and place it at `{emdat_path}`"
        )

    df_raw = (
        pd.read_excel(emdat_path, sheet_name="EM-DAT Data")
        .rename(columns=EM_DAT_COL_DICT)
        .assign(Start_Year=lambda x: pd.to_datetime(x.Start_Year, format="%Y"))
    )

    disaster_class_dict = {
        "Storm": "Hydrometereological",
        "Flood": "Hydrometereological",
        "Mass movement (wet)": "Hydrometereological",
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
    region_dict = df_raw[["ISO", "Region"]].drop_duplicates().set_index("ISO").to_dict()["Region"]
    subregion_dict = df_raw[["ISO", "Subregion"]].drop_duplicates().set_index("ISO").to_dict()["Subregion"]
    ISO_codes = df_raw["ISO"].unique()

    newest_event = df_raw["Start_Year"].max()
    years = pd.date_range(start=window_start, end=newest_event, freq="YS-JAN")
    if years.empty:
        raise ValueError(
            f"window_start={pd.Timestamp(window_start).date()} is after the newest event in the workbook "
            f"({newest_event.date()}), so every output frame would be empty."
        )

    # Define the complete combination of years and ISO codes
    complete_index = pd.MultiIndex.from_product([ISO_codes, years], names=["ISO", "Start_Year"]).sort_values()

    # Raw versions
    df_raw_filtered = df_raw.query("Total_Affected >1000 &  Deaths >100 & Start_Year > 1970")
    df_raw_filtered_adj = df_raw.query("Total_Affected >1000 & Start_Year > 1980")

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
            .sort_index()
        )

        assert result.shape[0] == len(complete_index)
        assert np.all(result.index.get_level_values(0) == complete_index.get_level_values(0))
        assert np.all(result.index.get_level_values(1) == complete_index.get_level_values(1))
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
        )

        assert result.shape[0] == len(complete_index)
        assert np.all(result.index.get_level_values(0) == complete_index.get_level_values(0))
        assert np.all(result.index.get_level_values(1) == complete_index.get_level_values(1))

        return result

    df_inten_unfiltered = process_damage_df(df_raw)
    df_inten_filtered = process_damage_df(df_raw_filtered)
    df_inten_filtered_adjusted = process_damage_df(df_raw_filtered_adj)
    df_inten_filtered_adjusted_hydro = process_damage_df(
        df_raw_filtered_adj.query('disaster_class == "Hydrometereological"')
    )
    df_inten_filtered_adjusted_clim = process_damage_df(df_raw_filtered_adj.query('disaster_class == "Climatological"'))

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
