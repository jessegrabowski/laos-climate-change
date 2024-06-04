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
WORLD_URL = "https://datacatalogfiles.worldbank.org/ddh-published/0038272/DR0046659/wb_countries_admin0_10m.zip?versionId=2024-05-14T14:58:01.5696428Z"  # noqa
WORLD_FILENAME = "wb_countries_admin0_10m.zip"  # noqa
LAOS_URL = "https://data.humdata.org/dataset/9eb6aff1-9e3f-43d3-99a6-f415fe4b4dff/resource/1d6edf99-5303-4b31-8909-dd70cda78443/download/lao_adm_ngd_20191112_shp.zip"  # noqa
LAOS_FILENAME = "lao_adm_ngd_20191112_shp.zip"  # noqa
POPULATION_DENSITY_URL = (
    "https://api.worldbank.org/v2/en/indicator/EN.POP.DNST?downloadformat=csv"
)
GDP_PER_CAPITA_CONSTANT_URL = (
    "https://api.worldbank.org/v2/en/indicator/NY.GDP.PCAP.KD?downloadformat=csv"
)

VARIABLES_DICTIONARY = {
    "gdp_per_cap_real": "GDP per capita (constant 2015 US$)",
    "population_density": "Population density (people per sq. km of land area)",
}

GPCC_URL = {"1981_1990": "https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022/10/full_data_monthly_v2022_1981_1990_10.nc.gz",
    "1991_2000": "https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022/10/full_data_monthly_v2022_1991_2000_10.nc.gz" ,
    "2001_2010": "https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022/10/full_data_monthly_v2022_2001_2010_10.nc.gz" ,
    "2011_2020": "https://opendata.dwd.de/climate_environment/GPCC/full_data_monthly_v2022/10/full_data_monthly_v2022_2011_2020_10.nc.gz"}
