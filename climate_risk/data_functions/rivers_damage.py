from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from climate_risk.const_vars import (
    LAOS_LOCATION_DICTIONARY,
    RIVERS_FLOODS_DAMAGE_FILENAME,
    RIVERS_HYDRO_DAMAGE_FILENAME,
)
from climate_risk.data_functions.emdat_processing import load_emdat_data
from climate_risk.data_functions.rivers_data_loader import load_rivers_data
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile
from climate_risk.geo.crs import to_km
from climate_risk.geo.distance import get_distance_to_rivers


def create_hydro_rivers_damage(cache_dir: Path) -> gpd.GeoDataFrame:
    hydro_damage_path = cache_dir / RIVERS_HYDRO_DAMAGE_FILENAME

    if not hydro_damage_path.is_file():
        big_rivers = load_rivers_data(cache_dir)
        emdat = load_emdat_data(cache_dir)

        world = load_shapefile("world", cache_dir, repair_ISO_codes=True)

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
                        "Total_Affected",
                        "Deaths",
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
        closest_river["closest_river"] = to_km(closest_river["closest_river"])

        damage_df = damage_df.join(closest_river)

        damage_df.rename(
            columns={
                "Total_Damage": "Total_Damage_Hydro",
                "Total_Affected": "Total_Affected_Hydro",
            },
            inplace=True,
        )

        damage_df = damage_df.assign(log_damage_hydro=lambda x: np.log(x.Total_Damage_Hydro))

        damage_df = damage_df.assign(log_affected_hydro=lambda x: np.log(x.Total_Affected_Hydro))

        damage_df.to_file(hydro_damage_path)

    else:
        damage_df = gpd.read_file(hydro_damage_path)
        damage_df = damage_df.rename(
            columns={
                "River Basi": "River Basin",
                "Total_Dama": "Total_Damage_Hydro",
                "Total_Affe": "Total_Affected",
                "closest_ri": "closest_river",
                "log_damage": "log_damage_hydro",
            }
        )

    return damage_df


def create_floods_rivers_damage(cache_dir: Path) -> gpd.GeoDataFrame:
    floods_damage_path = cache_dir / RIVERS_FLOODS_DAMAGE_FILENAME

    if not floods_damage_path.is_file():
        big_rivers = load_rivers_data(cache_dir)
        emdat = load_emdat_data(cache_dir)
        world = load_shapefile("world", cache_dir, repair_ISO_codes=True)

        floods_damages = (
            emdat["df_raw_filtered_adj"]
            .rename(columns={"Disaster Type": "disaster_type"})
            .query('disaster_type == "Flood"')
        )

        for x in LAOS_LOCATION_DICTIONARY.keys():
            index = floods_damages[floods_damages["DisNo."] == x].index
            floods_damages.loc[index, "Latitude"] = LAOS_LOCATION_DICTIONARY[x]["Latitude"]
            floods_damages.loc[index, "Longitude"] = LAOS_LOCATION_DICTIONARY[x]["Longitude"]

        damage_df_f = gpd.GeoDataFrame(
            (
                floods_damages[
                    [
                        "ISO",
                        "End Year",
                        "Latitude",
                        "Longitude",
                        "River Basin",
                        "Total_Damage",
                        "Total_Affected",
                        "Deaths",
                        "Location",
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

        closest_river_f = get_distance_to_rivers(big_rivers, damage_df_f)
        closest_river_f["closest_river"] = to_km(closest_river_f["closest_river"])

        damage_df_f = damage_df_f.join(closest_river_f)

        damage_df_f.rename(
            columns={
                "Total_Damage": "Total_Damage_Flood",
                "Total_Affected": "Total_Affected_Flood",
            },
            inplace=True,
        )

        damage_df_f = damage_df_f.assign(log_damage_floods=lambda x: np.log(x.Total_Damage_Flood))

        damage_df_f = damage_df_f.assign(log_affected_floods=lambda x: np.log(x.Total_Affected_Flood))

        damage_df_f.to_file(floods_damage_path)

    else:
        damage_df_f = gpd.read_file(floods_damage_path)
        damage_df_f = damage_df_f.rename(
            columns={
                "River Basi": "River Basin",
                "Total_Dama": "Total_Damage_floods",
                "Total_Affe": "Total_Affected_floods",
                "closest_ri": "closest_river",
                "log_damage": "log_damage_floods",
                "log_affect": "log_affected_floods",
            }
        )

    return damage_df_f
