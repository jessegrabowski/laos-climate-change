import os
from os.path import exists
from urllib.request import urlretrieve
from zipfile import ZipFile

from laos_gggi.const_vars import WORLD_URL, WORLD_FILENAME, LAOS_URL, LAOS_FILENAME
import logging

_log = logging.getLogger(__name__)


def download_shapefile(which, output_path="data/shapefiles"):
    if which == "Laos":
        url = LAOS_URL
        filename = LAOS_FILENAME
    elif which == "world":
        url = WORLD_URL
        filename = WORLD_FILENAME
    else:
        raise NotImplementedError()

    path_to_file = os.path.join(output_path, filename)
    if not exists(output_path):
        os.makedirs(output_path)

    if not exists(path_to_file):
        _log.info(f"Downloading {which} shapefiles to {output_path}")
        urlretrieve(url, path_to_file)


def extract_shapefiles(which: str, output_path="data/shapefiles"):
    if which.lower() not in ["world", "laos"]:
        raise ValueError(f'which should be one of ["world", "laos"], got {which}')
    filename = (
        "wb_countries_admin0_10m"
        if which.lower() == "world"
        else "lao_adm_ngd_20191112_shp"
    )
    shapefile_path = os.path.join(output_path, filename)

    if not exists(shapefile_path):
        _log.info(f"Extracting {shapefile_path}")
        with ZipFile(shapefile_path + ".zip", "r") as zObject:
            zObject.extractall(path=output_path)
