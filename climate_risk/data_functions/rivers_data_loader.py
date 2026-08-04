import logging
import os
import urllib.request

from os.path import exists
from zipfile import ZipFile

import geopandas as gpd

from pyprojroot import here

from climate_risk.const_vars import (
    BIG_RIVERS_FILENAME,
    MEDIUM_BIG_RIVERS_FILENAME,
    RIVERS_SHAPEFILE_FILENAME,
    RIVERS_URL,
    RIVERS_ZIP_FILENAME,
)

_log = logging.getLogger(__name__)


def load_rivers_data(data_path=None, include_medium: bool = False):
    data_path = here("data/rivers") if data_path is None else data_path
    path_to_zip_file = os.path.join(data_path, RIVERS_ZIP_FILENAME)
    path_to_shapefile = os.path.join(data_path, RIVERS_SHAPEFILE_FILENAME)
    path_to_big_rivers = os.path.join(data_path, BIG_RIVERS_FILENAME)
    path_to_medium_big_rivers = os.path.join(data_path, MEDIUM_BIG_RIVERS_FILENAME)

    if not exists(data_path):
        os.makedirs(data_path)

    if not os.path.isfile(here(path_to_zip_file)):
        _log.info("Downloading rivers ")

        opener = urllib.request.URLopener()
        opener.addheader(
            "User-Agent",
            "Mozilla/5.0 (Linux i554 x86_64; en-US) AppleWebKit/534.34 (KHTML, like Gecko) "
            "Chrome/55.0.2447.185 Safari/601",
        )

        opener.retrieve(RIVERS_URL, path_to_zip_file)

    if not os.path.isfile(here(path_to_shapefile)):
        with ZipFile(here(path_to_zip_file), "r") as zObject:
            zObject.extractall(path=here(data_path))

    if include_medium:
        if not os.path.isfile(here(path_to_medium_big_rivers)):
            _log.info("Loading and processing rivers data")
            df = gpd.read_file(here(os.path.join("data", "rivers", "HydroRIVERS_v10_shp", "HydroRIVERS_v10.shp")))

            medium_and_big_rivers = df.query("ORD_FLOW < 6")
            medium_and_big_rivers.to_file(here(path_to_medium_big_rivers))
        else:
            medium_and_big_rivers = gpd.read_file(here(path_to_medium_big_rivers))
        return medium_and_big_rivers

    elif not include_medium:
        if not os.path.isfile(here(path_to_big_rivers)):
            _log.info("Loading and processing rivers data")
            df = gpd.read_file(here(os.path.join("data", "rivers", "HydroRIVERS_v10_shp", "HydroRIVERS_v10.shp")))

            big_rivers = df.query("ORD_FLOW < 5")
            big_rivers.to_file(here(path_to_big_rivers))

        if os.path.isfile(here(path_to_big_rivers)):
            big_rivers = gpd.read_file(here(path_to_big_rivers))

        return big_rivers
