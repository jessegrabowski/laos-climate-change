import os
from os.path import exists
from urllib.request import urlretrieve
from const_vars import GPCC_URL
import xarray as xr
import geopandas as geo
import pandas as pd


def download_gpcc_data(output_path="../data"):
    path_to_GPCC_raw = output_path + "/precip.mon.nobs.1x1.v7.nc"
    path_to_GPCC = output_path + "/gpcc_precipitation.csv"
    shapefile_unzipped_folder = output_path + "/shapefiles/wb_countries_admin0_10m"
    shapefile_path = shapefile_unzipped_folder + "/wb_countries_admin0_10m"
    if not exists(output_path):
        os.makedirs(output_path)
        urlretrieve(GPCC_URL, path_to_GPCC_raw)

    if not exists(path_to_GPCC_raw):
        urlretrieve(GPCC_URL, path_to_GPCC_raw)

    if not exists(path_to_GPCC):
        data = xr.open_dataset("../data" + "/precip.mon.nobs.1x1.v7.nc")
        df = data["precip"].to_dataframe()
        df = df.reset_index()
        df = df.query('time > "1960-01-01"')

    if not exists(shapefile_unzipped_folder):
        raise NotImplementedError("Please unzip the shapefile folder")
        # Tranform lat and long to shapely.Point objects
        df_geo = geo.GeoDataFrame(
            df, geometry=geo.points_from_xy(df["lat"], df["lon"]), crs="EPSG:4326"
        )
        # Import the world shapefile *check if they exist before
        gdf = geo.read_file(shapefile_path)
        # Merge everything
        gpcc_precipitation = df_geo.sjoin(gdf, how="left", predicate="intersects")[
            ["time", "lat", "lon", "precip", "ISO_A3", "geometry"]
        ]
        gpcc_precipitation.rename(
            columns={
                "ISO_A3": "country_code",
                "precip": "precipitation",
                "time": "date",
            },
            inplace=True,
        )
        gpcc_precipitation = gpcc_precipitation(path_to_GPCC).set_index(
            ["country_code", "date"]
        )
        gpcc_precipitation.to_csv(path_to_GPCC)

    else:
        gpcc_precipitation = pd.read_csv(path_to_GPCC).set_index(
            ["country_code", "date"]
        )

    return
