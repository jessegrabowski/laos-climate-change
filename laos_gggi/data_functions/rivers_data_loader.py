from pyprojroot import here
import os
from os.path import exists
from laos_gggi.const_vars import (
    RIVERS_URL,
    RIVERS_SHAPEFILE_FILENAME,
    RIVERS_ZIP_FILENAME,
    BIG_RIVERS_FILENAME,
)
import logging
import urllib.request
from zipfile import ZipFile

import geopandas as gpd

_log = logging.getLogger(__name__)


def load_rivers_data(data_path=here("data/rivers")):
    path_to_zip_file = os.path.join(data_path, RIVERS_ZIP_FILENAME)

    opener = urllib.request.URLopener()
    opener.addheader("User-Agent", "whatever")

    if not exists(data_path):
        os.makedirs(data_path)

    if not os.path.isfile(os.path.join(data_path, RIVERS_ZIP_FILENAME)):
        _log.info("Downloading rivers ")
        opener.retrieve(RIVERS_URL, path_to_zip_file)

    if not os.path.isfile(os.path.join(data_path, RIVERS_SHAPEFILE_FILENAME)):
        with ZipFile(
            here(os.path.join(data_path, RIVERS_ZIP_FILENAME)), "r"
        ) as zObject:
            zObject.extractall(path=here(data_path))

    if not os.path.isfile(os.path.join(data_path, BIG_RIVERS_FILENAME)):
        _log.info("Loading and processing rivers data")
        df = gpd.read_file(here(r"data\rivers\HydroRIVERS_v10_shp\HydroRIVERS_v10.shp"))
        big_rivers = df.query("ORD_CLAS == 1 and ORD_FLOW < 5")
        big_rivers.to_file(os.path.join(data_path, BIG_RIVERS_FILENAME))
    else:
        big_rivers = gpd.read_file(os.path.join(data_path, BIG_RIVERS_FILENAME))

    return big_rivers
