import pandas as pd
import os
from os.path import exists
from laos_gggi.const_vars import INTENSITY_COLS, DISASTERS_FOUND, PROB_COLS  # noqa


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def process_emdat(data_path="data", force_reload=False):
    output_files = ["probability_data_set", "intensity_data_set"]
    data_path = os.path.join(ROOT_DIR, data_path)

    if not exists(data_path):
        os.makedirs(data_path)

    emdat_path = os.path.join(data_path, "emdat.xlsx")
    if not exists(emdat_path):
        raise NotImplementedError(
            "No EM-DAT data was found at `/data/emdat.xlsx`. Please make an account at <url>, download the database, "
            "and place it in `/data/emdat.xlsx`"
        )

    if (
        all(
            [
                exists(os.path.join(data_path, f"{out_name}.csv"))
                for out_name in output_files
            ]
        )
        and not force_reload
    ):
        return (
            pd.read_csv(os.path.join(data_path, f"{output_files[0]}.csv")).set_index(
                ["ISO", "Start Year"]
            ),
            pd.read_csv(os.path.join(data_path, f"{output_files[1]}.csv")).set_index(
                ["ISO", "Start Year"]
            ),
        )

    df = pd.read_excel(emdat_path, sheet_name="EM-DAT Data")
    df2 = df.copy()[INTENSITY_COLS]

    df = (
        df.query("`Disaster Type` in @PROB_COLS")
        .groupby(["Disaster Type", "ISO", "Start Year"])
        .size()
        .unstack("Disaster Type")
        .fillna(0)
        .reset_index()
    ).copy()

    df[DISASTERS_FOUND] = df[DISASTERS_FOUND].astype(int).copy()

    df_prob = df.copy().set_index(["ISO", "Start Year"]).sort_index()
    df_inten = df2.copy().set_index(["ISO", "Start Year"]).sort_index()

    for df, out_name in zip([df_prob, df_inten], output_files):
        out_path = os.path.join(data_path, f"{out_name}.csv")
        if not exists(out_path):
            df.to_csv(out_path)

    return df_prob, df_inten
