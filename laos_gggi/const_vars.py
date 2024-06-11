PROB_COLS = [  # noqa
    "Drought",
    "Earthquake",
    "Extreme temperature",
    "Flood",
    "Storm",
    "Wildfire",
    "Volcanic activity",
    "Mass Movement (Dry)",
    "Mass Movement (Wet)",
    "Region",
]

DISASTERS_FOUND = [  # noqa
    "Drought",
    "Earthquake",
    "Extreme temperature",
    "Flood",
    "Storm",
    "Volcanic activity",
    "Wildfire",
]

INTENSITY_COLS = [  # noqa
    "Country",
    "Start_Year",
    "Region",
    "Deaths",
    "Injured",
    "Numb_Affected",
    "Homeless",
    "Total_Affected",
    "Reconstruction_Costs",
    "Reconstruction_Costs_Adjusted",
    "Insured_Damage",
    "Insured_Damage_Adjusted",
    "Total_Damage",
    "Total_Damage_Adjusted",
    "CPI",
]

EM_DAT_COL_DICT = {  # noqa
    "Start Year": "Start_Year",
    "Total Deaths": "Deaths",
    "No. Injured": "Injured",
    "No. Affected": "Numb_Affected",
    "No. Homeless": "Homeless",
    "Total Affected": "Total_Affected",
    "Reconstruction Costs ('000 US$)": "Reconstruction_Costs",
    "Reconstruction Costs, Adjusted ('000 US$)": "Reconstruction_Costs_Adjusted",
    "Insured Damage ('000 US$)": "Insured_Damage",
    "Insured Damage, Adjusted ('000 US$)": "Insured_Damage_Adjusted",
    "Total Damage ('000 US$)": "Total_Damage",
    "Total Damage, Adjusted ('000 US$)": "Total_Damage_Adjusted",
}


WORLD_URL = "https://datacatalogfiles.worldbank.org/ddh-published/0038272/DR0046659/wb_countries_admin0_10m.zip?versionId=2024-05-14T14:58:01.5696428Z"  # noqa
WORLD_FILENAME = "wb_countries_admin0_10m.zip"  # noqa
LAOS_URL = "https://data.humdata.org/dataset/9eb6aff1-9e3f-43d3-99a6-f415fe4b4dff/resource/1d6edf99-5303-4b31-8909-dd70cda78443/download/lao_adm_ngd_20191112_shp.zip"  # noqa
LAOS_FILENAME = "lao_adm_ngd_20191112_shp.zip"  # noqa
