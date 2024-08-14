import pandas as pd
from laos_gggi import load_all_data
from statsmodels.tsa.seasonal import STL
import numpy as np


def create_replication_data():
    # Load data
    data = load_all_data()
    df_clim = data["df_time_series"][["co2", "Temp", "precip"]].iloc[1:-1]
    emdat_damage_hydro = data["emdat_damage"]["Total_Damage_Adjusted_hydro"]  # noga
    emdat_damage_clim = data["emdat_damage"]["Total_Damage_Adjusted_clim"]
    hydro_disasters = data["emdat_events"][["Flood", "Storm"]]
    climate_disasters = data["emdat_events"][
        ["Extreme temperature", "Wildfire", "Drought"]
    ]
    disasters = data["emdat_events"]
    development_indicators = data["wb_data"]
    precipitation = data["gpcc"]

    # Calculate total climatological and hydrological disasters columns

    disasters["climatological_disasters"] = (
        climate_disasters.fillna(0).astype(int).sum(axis=1)
    )
    disasters["hydrological_disasters"] = (
        hydro_disasters.fillna(0).astype(int).sum(axis=1)
    )

    # Fill NaN values for disasters and emdat_damage
    disasters = disasters.fillna(0)

    # Obtain each country's precipitation deviation from the average for its 30-year base climatology period 1961–1990
    countries = precipitation.reset_index()["ISO"].unique()

    precip_deviation = pd.DataFrame()

    precip_deviation = pd.DataFrame(columns=countries)
    for x in countries:
        precip_deviation[x] = (
            precipitation.reset_index().pivot(
                index="year", values="precip", columns="ISO"
            )[x]
            - pd.DataFrame(precipitation.unstack(-2).head(30).mean())
            .loc["precip"]
            .loc[x]
            .values
        )

    precip_deviation = (
        precip_deviation.stack()
        .reset_index()
        .rename(columns={"level_1": "ISO", 0: "precip_deviation"})
        .set_index(["ISO", "year"])
    )
    precip_deviation = precip_deviation.sort_index()

    # Obtain the sea temperature deviation from the trend
    stl_ocean_temp = STL(pd.DataFrame(df_clim["Temp"].dropna()), period=3)
    result_ocean_temp = stl_ocean_temp.fit()
    trend_ocean_temp = result_ocean_temp.trend
    dev_from_trend_ocean_temp = df_clim["Temp"].dropna() - trend_ocean_temp

    # Obtain the natural logarithms of population density and GDP per capita
    development_indicators["population"] = development_indicators["SP.POP.TOTL"]
    development_indicators["ln_population_density"] = np.log(
        development_indicators["population_density"]
    )
    development_indicators["ln_gdp_pc"] = np.log(development_indicators["gdp_per_cap"])
    development_indicators["square_ln_gdp_p"] = (
        (development_indicators["ln_gdp_pc"]) * (development_indicators["ln_gdp_pc"])
    )

    # Merging everything into one df
    df = pd.merge(
        disasters, development_indicators, right_index=True, left_index=True, how="left"
    )
    df = df.reset_index().rename(columns={"Start_Year": "year"}).set_index("year")

    df = pd.merge(
        df,
        pd.DataFrame(dev_from_trend_ocean_temp).rename(
            columns={0: "dev_from_trend_ocean_temp"}
        ),
        right_index=True,
        left_index=True,
        how="left",
    )

    df = pd.merge(df, (df_clim["co2"]), right_index=True, left_index=True, how="left")

    df = pd.merge(
        df.reset_index().set_index(["ISO", "year"]),
        precip_deviation,
        right_index=True,
        left_index=True,
        how="left",
    )

    df = pd.merge(
        df, data["surface_temp"], right_index=True, left_index=True, how="left"
    )
    df = pd.merge(
        df,
        emdat_damage_hydro.reset_index()
        .rename(columns={"Start_Year": "year"})
        .set_index(["ISO", "year"]),
        right_index=True,
        left_index=True,
        how="left",
    )

    df = pd.merge(
        df,
        emdat_damage_clim.reset_index()
        .rename(columns={"Start_Year": "year"})
        .set_index(["ISO", "year"]),
        right_index=True,
        left_index=True,
        how="left",
    )

    df = df.reset_index()
    cols_to_use = [
        "ISO",
        "year",
        "climatological_disasters",
        "hydrological_disasters",
        "population",
        "ln_population_density",
        "ln_gdp_pc",
        "square_ln_gdp_p",
        "dev_from_trend_ocean_temp",
        "co2",
        "precip_deviation",
        "Total_Damage_Adjusted_hydro",
        "Total_Damage_Adjusted_clim",
    ]
    df = df[cols_to_use]
    df = df.dropna()
    df["population"] = df["population"] / 1e6

    # Creating the time trend
    df["time_period"] = (df["year"].dt.year - 1980) / 100

    # Adjust data types
    df["ISO"] = df["ISO"]

    # SUm of all damages
    df["Total_Damage_Adjusted_all"] = (
        df["Total_Damage_Adjusted_clim"] + df["Total_Damage_Adjusted_hydro"]
    )

    return df
