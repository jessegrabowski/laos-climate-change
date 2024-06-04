import os
from os.path import exists
from urllib.request import urlretrieve
from const_vars import GPCC_YEARS, MAKE_GPCC_URL
import geopandas as geo
import pandas as pd
from zipfile import ZipFile
import gzip
import shutil
import xarray as xr


def download_gpcc_data(output_path="../data"):
    def path_to_GPCC_raw(years: str):
        return f"../data/gpcc/gpcc_raw_{years}.nc.gz"

    def path_to_GPCC_extracted(years: str):
        return f"../data/gpcc/gpcc_raw_{years}.nc"

    path_to_GPCC_unzipped = output_path + "/gpcc/gpcc_raw_1981_1990.nc"
    shapefile_unzipped_folder_world = (
        output_path + "/shapefiles/wb_countries_admin0_10m"
    )
    shapefile_unzipped_folder_laos = output_path + "lao_adm_ngd_20191112_shp"
    world_shapefile_path = output_path + "/shapefiles/wb_countries_admin0_10m"  # noqa
    gpcc_processed_path = output_path + "/gpcc/gpcc_precipitations.csv"

    # Check if "data" folder exists
    if not exists(output_path):
        os.makedirs(output_path)

    # Check if gpcc folder exists
    if not exists(output_path + "/gpcc"):
        os.makedirs(output_path + "/gpcc")

    # Check if the GPCC raw data exists
    if not exists(path_to_GPCC_raw("1981_1990")):
        for x in GPCC_YEARS:
            urlretrieve(MAKE_GPCC_URL(x), path_to_GPCC_raw(x))

    # Verify if shapefiles are unzipped
    if not exists(shapefile_unzipped_folder_world):
        with ZipFile(
            output_path + "/shapefiles/wb_countries_admin0_10m.zip", "r"
        ) as zObject:
            zObject.extractall(path=output_path + "/shapefiles")
    if not exists(shapefile_unzipped_folder_laos):
        with ZipFile(
            output_path + "/shapefiles/lao_adm_ngd_20191112_shp.zip", "r"
        ) as zObject:
            zObject.extractall(path=output_path + "/shapefiles")

    # Verify if the gpcc files are extracted (Note:gzip.open does not support loops)
    if not exists(path_to_GPCC_unzipped):
        for x in GPCC_YEARS:
            with gzip.open(path_to_GPCC_raw(x), "rb") as f_in:
                with open(path_to_GPCC_extracted(x), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
    if not exists(gpcc_processed_path):
        # Import the world shapefile
        world_shapefile = geo.read_file(world_shapefile_path).rename(  # noqa
            columns={
                "ISO_A3": "country_code",
                "FORMAL_EN": "country",
                "CONTINENT": "continent",
                "REGION_UN": "region",
            }
        )
        # Open gpcc files, transform them to geopandas shapefile geometry and merge them with the world shapefiles
        result_df = pd.DataFrame()
        for x in list(GPCC_YEARS):
            data = xr.open_dataset(path_to_GPCC_extracted(x))
            df = data["precip"].to_dataframe().reset_index()
            df_geo = geo.GeoDataFrame(
                df, geometry=geo.points_from_xy(df["lat"], df["lon"]), crs="EPSG:4326"
            )
            df_geo_wshape = df_geo.sjoin(
                world_shapefile, how="inner", predicate="intersects"
            )[
                [
                    "time",
                    "lat",
                    "lon",
                    "precip",
                    "country_code",
                    "geometry",
                    "country",
                    "continent",
                    "region",
                ]
            ]
            result_df = pd.concat([result_df, df_geo_wshape], axis=0)

        result_df = result_df.pivot_table(
            values="precip", index=["country_code", "time"], aggfunc="mean"
        )
        result_df.to_csv(gpcc_processed_path)
    else:
        result_df = pd.read_csv(gpcc_processed_path).set_index(["country_code", "time"])
    return result_df
