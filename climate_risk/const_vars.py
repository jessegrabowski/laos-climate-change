PROB_COLS = [
    "Country",
    "ISO",
    "Start_Year",
    "Drought",
    "Extreme temperature",
    "Flood",
    "Storm",
    "Wildfire",
    "Mass movement (dry)",
    "Mass movement (wet)",
    "Region",
    "Subregion",
]

DISASTERS_FOUND = [
    "Drought",
    "Extreme temperature",
    "Flood",
    "Storm",
    "Wildfire",
]

INTENSITY_COLS = [
    "Country",
    "ISO",
    "Start_Year",
    "Region",
    "Deaths",
    "Injured",
    "Numb_Affected",
    "Homeless",
    "Total_Affected",
    "Total_Damage",
    "Total_Damage_Adjusted",
    "Disaster Type",
]

EM_DAT_COL_DICT = {
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


MODEL_DF_FILENAME = "model_df.csv"
DAMAGE_DF_FILENAME = "damage_df.csv"
LAOS_LOCATION_DICTIONARY = {
    "1971-0048-LAO": {"Latitude": 17.9757, "Longitude": 102.6331},
    "2000-0583-LAO": {"Latitude": 19.0, "Longitude": 102.0},
    "2013-0338-LAO": {"Latitude": 19.5, "Longitude": 103.5},
    "2013-0417-LAO": {"Latitude": 16.5, "Longitude": 106.0},
    "2015-0324-LAO": {"Latitude": 19.0, "Longitude": 104.0},
    "2016-0316-LAO": {"Latitude": 19.9, "Longitude": 102.1},
}


POPULATION_DENSITY_URL = "https://api.worldbank.org/v2/en/indicator/EN.POP.DNST?downloadformat=csv"
GDP_PER_CAPITA_CONSTANT_URL = "https://api.worldbank.org/v2/en/indicator/NY.GDP.PCAP.KD?downloadformat=csv"

VARIABLES_DICTIONARY = {
    "gdp_per_cap_real": "GDP per capita (constant 2015 US$)",
    "population_density": "Population density (people per sq. km of land area)",
}


REGIONS = ["Asia", "Europe", "Africa", "Oceania", "Americas"]
