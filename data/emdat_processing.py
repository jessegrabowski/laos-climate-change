import pandas as pd

df = pd.read_excel("emdat.xlsx", sheet_name="EM-DAT Data")

prob_cols = [
    "Drought",
    "Earthquake",
    "Extreme temperature",
    "Flood",
    "Storm",
    "Wildfire",
    "Volcanic activity",
    "Mass Movement (Dry)",
    "Mass Movement (Wet)",
]

intensity_cols = [
    "Country",
    "Start Year",
    "Total Deaths",
    "No. Injured",
    "No. Affected",
    "No. Homeless",
    "Total Affected",
    "Reconstruction Costs ('000 US$)",
    "Reconstruction Costs, Adjusted ('000 US$)",
    "Insured Damage ('000 US$)",
    "Insured Damage, Adjusted ('000 US$)",
    "Total Damage ('000 US$)",
    "Total Damage, Adjusted ('000 US$)",
    "CPI",
]

df2 = df.copy()[intensity_cols]

df = (
    df.query("`Disaster Type` in @prob_cols")
    .groupby(["Disaster Type", "ISO", "Start Year"])
    .size()
    .unstack("Disaster Type")
    .fillna(0)
    .reset_index()
).copy()


disasters_found = [
    "Drought",
    "Earthquake",
    "Extreme temperature",
    "Flood",
    "Storm",
    "Volcanic activity",
    "Wildfire",
]

df[disasters_found] = df[disasters_found].astype(int).copy()

df.rename(columns={"ISO": "Country"}, inplace=True)
df2.rename(columns={"ISO": "Country"}, inplace=True)

df_prob = df.copy().set_index(["Country", "Start Year"]).sort_index()
df_inten = df2.copy().set_index(["Country", "Start Year"]).sort_index()
