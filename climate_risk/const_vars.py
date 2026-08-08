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


# The World Bank data catalog serves downloads through a rate-limited API with no stable direct
# link, so this points at a humanitarian CKAN node mirroring the same archive.
WORLD_URL = (
    "https://ckan.rdas.live/dataset/36f4b9e3-13d4-4865-98b9-1e299a9c6458"
    "/resource/fd848e6b-bf73-470f-9c51-25ce4ff76f20/download/wb_countries_admin0_10m.zip"
)
WORLD_FILENAME = "wb_countries_admin0_10m.zip"
LAOS_URL = (
    "https://data.humdata.org/dataset/9eb6aff1-9e3f-43d3-99a6-f415fe4b4dff"
    "/resource/907a1b50-0d14-40ec-8b8a-f2d027d895aa/download/lao_admin_boundaries.shp.zip"
)
LAOS_FILENAME = "lao_admin_boundaries.shp.zip"

MODEL_DF_FILENAME = "model_df.csv"
DAMAGE_DF_FILENAME = "damage_df.csv"
RIVERS_URL = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_shp.zip"
RIVERS_SHAPEFILE_FILENAME = "HydroRIVERS_v10.shp"
RIVERS_ARCHIVE_DIRNAME = "HydroRIVERS_v10_shp"
RIVERS_ZIP_FILENAME = "rivers_zip_file.zip"
BIG_RIVERS_FILENAME = "big_rivers.shp"
MEDIUM_BIG_RIVERS_FILENAME = "medium_big_rivers.shp"
RIVERS_HYDRO_DAMAGE_FILENAME = "rivers_hydro_damage.shp"
RIVERS_FLOODS_DAMAGE_FILENAME = "rivers_floods_damage.shp"
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


COASTLINE_FILENAME = "gshhg-shp-2.3.7.zip"
COASTLINE_URL = "https://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.7.zip"
