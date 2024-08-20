from pyprojroot import here
import os
from os.path import exists
from urllib.request import urlretrieve
from laos_gggi.const_vars import GPCC_YEARS, MAKE_GPCC_URL
from laos_gggi.data_functions.shapefiles_data_loader import load_shapefile
import geopandas as geo
import pandas as pd
import gzip
import shutil
import xarray as xr

import logging

_log = logging.getLogger(__name__)


def load_gpcc_data(output_path="data", force_reload=False, repair_ISO_codes=True):
    def path_to_GPCC(years: str, extracted=False):
        fname = f"gpcc_raw_{years}.nc"
        fname += ".gz" if not extracted else ""
        return os.path.join(output_path, "gpcc", fname)

    output_path = here(output_path)
    path_to_GPCC_unzipped = os.path.join(output_path, "gpcc/gpcc_raw_1981_1990.nc")
    gpcc_processed_path = os.path.join(output_path, "gpcc/gpcc_precipitations.csv")

    # Check if "data" folder exists
    if not exists(output_path):
        os.makedirs(output_path)

    # Check if gpcc folder exists
    gpcc_path = os.path.join(output_path, "gpcc")
    if not exists(gpcc_path):
        os.makedirs(gpcc_path)

    # Check if the GPCC raw data exists
    for year_range in GPCC_YEARS:
        if not exists(path_to_GPCC(year_range)):
            _log.info(f'Downloading GPCC data for {" - ".join(year_range.split("_"))}')
            urlretrieve(
                MAKE_GPCC_URL(year_range), path_to_GPCC(year_range, extracted=False)
            )

    # Verify if the gpcc files are extracted (Note:gzip.open does not support loops)
    if not exists(path_to_GPCC_unzipped):
        for year_range in GPCC_YEARS:
            with gzip.open(path_to_GPCC(year_range, extracted=False), "rb") as f_in:
                with open(path_to_GPCC(year_range, extracted=True), "wb") as f_out:
                    _log.info(
                        f'Extracting GPCC data for {" - ".join(year_range.split("_"))}'
                    )
                    shutil.copyfileobj(f_in, f_out)

    if not exists(gpcc_processed_path) or force_reload:
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

        # Open gpcc files, transform them to geopandas shapefile geometry and merge them with the world shapefiles
        result_df = pd.DataFrame()
        for year_range in list(GPCC_YEARS):
            str_range = " - ".join(year_range.split("_"))

            data = xr.open_dataset(path_to_GPCC(year_range, extracted=True))
            df = data["precip"].to_dataframe().reset_index()
            _log.info(
                f"Merging {str_range} GPCC data with world shapefile using Lat/Lon (EPSG:4326 coordinates)"
            )
            df_geo = geo.GeoDataFrame(
                df, geometry=geo.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326"
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
        _log.info(f"Saving processed GPCC data to {gpcc_processed_path}")
        result_df.to_csv(gpcc_processed_path)
    else:
        result_df = pd.read_csv(gpcc_processed_path).set_index(["country_code", "time"])

    return result_df
