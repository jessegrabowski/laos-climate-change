import pandas as pd
import os
from os.path import exists
from laos_gggi.const_vars import INTENSITY_COLS, DISASTERS_FOUND, PROB_COLS  # noqa


def process_emdat(data_path="../data"):
    if not exists(data_path):
        os.makedirs(data_path)

    if not exists(data_path + "/emdat.xlsx"):
        raise NotImplementedError(
            "No EM-DAT data was found at `/data/emdat.xlsx`. Please make an account at https://public.emdat.be/, download the database, and place it in `/data/emdat.xlsx`"
        )

    df = pd.read_excel(data_path + "/emdat.xlsx", sheet_name="EM-DAT Data")

    df2 = df.copy()[INTENSITY_COLS]

    df = (
        df.query("`Disaster Type` in @PROB_COLS")
        .groupby(["Disaster Type", "Country", "Start Year", "Region"])
        .size()
        .unstack("Disaster Type")
        .fillna(0)
        .reset_index()
    ).copy()

    df[DISASTERS_FOUND] = df[DISASTERS_FOUND].astype(int).copy()

    df_prob = df.copy().set_index(["Country", "Start Year"]).sort_index()
    df_inten = df2.copy().set_index(["Country", "Start Year"]).sort_index()

    return (
        df_prob,
        df_inten,
        df_prob.to_csv(data_path + "/probability_data_set.csv"),
        df_inten.to_csv(data_path + "/intensity_data_set.csv"),
    )
