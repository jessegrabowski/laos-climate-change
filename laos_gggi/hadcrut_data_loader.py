import os
from os.path import exists
from urllib.request import urlretrieve
from laos_gggi.const_vars import HADCRUT_URL
from laos_gggi.shapefiles_data_loader import load_shapefile
import geopandas as geo
import pandas as pd
import xarray as xr

import logging

_log = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def process_hadcrut_data(output_path="data", force_reload=False, repair_ISO_codes=True):
    output_path = os.path.join(ROOT_DIR, output_path)
    hadcrut_raw_path = os.path.join(output_path, "hadcrut_temperature_raw.nc")
    hadcrut_processed_path = os.path.join(
        output_path, "hadcrut_temperature_processed.csv"
    )

    # Check if "data" folder exists
    if not exists(output_path):
        os.makedirs(output_path)

    # Check if the hadcrut raw data exists
    if not exists(hadcrut_raw_path):
        _log.info("Downloading HADCRUT data")
        urlretrieve(HADCRUT_URL, hadcrut_raw_path)

    # Verify if the hadcrut processed file exists
    if not exists(hadcrut_processed_path) or force_reload:
        # Import hadcrut processed file
        _log.info("Loading  HADCRUT raw data")
        data = xr.open_dataset(hadcrut_raw_path)
        df = data["tas_mean"].to_dataframe().reset_index()

        # Import the world shapefile
        _log.info("Loading world shapefile as GeoDataFrame")
        world_shapefile = load_shapefile(
            "world", force_reload=force_reload, repair_ISO_codes=repair_ISO_codes
        ).rename(
            columns={
                "ISO_A3": "country_code",
                "FORMAL_EN": "country",
                "CONTINENT": "continent",
                "REGION_UN": "region",
            }
        )
        _log.info(
            "Merging HADCRUT data with world shapefile using Lat/Lon (EPSG:4326 coordinates)"
        )

        df_geo = geo.GeoDataFrame(
            df,
            geometry=geo.points_from_xy(df["longitude"], df["latitude"]),
            crs="EPSG:4326",
        )
        result_df = df_geo.sjoin(world_shapefile, how="inner", predicate="intersects")[
            [
                "time",
                "latitude",
                "longitude",
                "realization",
                "tas_mean",
                "country_code",
                "geometry",
                "country",
                "continent",
                "region",
            ]
        ]
        result_df = result_df.rename(columns={"tas_mean": "surface_temperature_dev"})

        result_df = result_df.pivot_table(
            values="surface_temperature_dev",
            index=["country_code", "time"],
            aggfunc="mean",
        )
        result_df = result_df.reset_index()
        result_df["year"] = result_df["time"].dt.year
        result_df = result_df.rename(columns={"country_code": "ISO"})

        result_df = result_df.pivot_table(
            values="surface_temperature_dev", index=["ISO", "year"], aggfunc="mean"
        )

        result_df = result_df.pivot_table(
            values="surface_temperature_dev", index=["ISO", "year"]
        )
        result_df = (
            result_df.reset_index().query("year >1959").set_index(["ISO", "year"])
        )

        _log.info(f"Saving processed GPCC data to {hadcrut_processed_path}")
        result_df.to_csv(hadcrut_processed_path)
    else:
        result_df = pd.read_csv(hadcrut_processed_path).set_index(["ISO", "year"])

    return result_df
