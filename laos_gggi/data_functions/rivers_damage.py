import pandas as pd
from pyprojroot import here
import os
import numpy as np
import geopandas as gpd

from laos_gggi.data_functions.rivers_data_loader import load_rivers_data
from laos_gggi import load_emdat_data, load_shapefile
from laos_gggi.const_vars import RIVERS_HYDRO_DAMAGE_FILENAME
from laos_gggi.statistics import get_distance_to_rivers


def create_hydro_rivers_damage():
    data_path = here("data")
    if not os.path.isfile(os.path.join(data_path, RIVERS_HYDRO_DAMAGE_FILENAME)):
        big_rivers = load_rivers_data()
        emdat = load_emdat_data()

        # Load shapefiles
        world = load_shapefile("world", repair_ISO_codes=True)
        # laos = load_shapefile("laos")

        damage_df = gpd.GeoDataFrame(
            (
                emdat["df_raw_filtered_adj"]
                .query('disaster_class == "Hydrometereological"')[
                    [
                        "ISO",
                        "End Year",
                        "Latitude",
                        "Longitude",
                        "River Basin",
                        "Total_Damage",
                    ]
                ]
                .dropna(how="all", subset=["Latitude", "Longitude"])
                .assign(
                    geometry=lambda x: gpd.points_from_xy(x.Longitude, x.Latitude),
                    year=lambda x: pd.to_datetime(x["End Year"], format="%Y"),
                )
                .drop(columns=["End Year"])
                .replace({0.0: np.nan})
            ),
            crs=world.crs,
        )

        closest_river = get_distance_to_rivers(big_rivers, damage_df)

        damage_df = damage_df.join(
            closest_river / 1000
        )  # Note: we are dividing by 1000 to convert meters to km (because EPSG:3395 is in meters)

        damage_df.rename(columns={"Total_Damage": "Total_Damage_Hydro"}, inplace=True)

        damage_df = damage_df.assign(
            log_damage_hydro=lambda x: np.log(x.Total_Damage_Hydro)
        )

        damage_df.to_file(os.path.join(data_path, RIVERS_HYDRO_DAMAGE_FILENAME))
    else:
        damage_df = gpd.read_file(os.path.join(data_path, RIVERS_HYDRO_DAMAGE_FILENAME))

    return damage_df
