import os
from os.path import exists
from urllib.request import urlretrieve
from zipfile import ZipFile
import geopandas as gpd
from laos_gggi.const_vars import WORLD_URL, WORLD_FILENAME, LAOS_URL, LAOS_FILENAME
import logging

_log = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def download_shapefile(which, output_path="data/shapefiles"):
    if which.lower() not in ["laos", "world"]:
        raise ValueError(f'which should be one of ["world", "laos"], got {which}')
    url = LAOS_URL if which.lower() == "Laos" else WORLD_URL
    filename = LAOS_FILENAME if which.lower() == "Laos" else WORLD_FILENAME

    path_to_file = os.path.join(ROOT_DIR, output_path, filename)
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
    shapefile_path = os.path.join(ROOT_DIR, output_path, filename)

    if not exists(shapefile_path):
        _log.info(f"Extracting {shapefile_path}")
        with ZipFile(shapefile_path + ".zip", "r") as zObject:
            zObject.extractall(path=output_path)


def load_shapefile(which, output_path="data/shapefiles"):
    if which.lower() not in ["world", "laos"]:
        raise ValueError(f'which should be one of ["world", "laos"], got {which}')
    filename = (
        "wb_countries_admin0_10m"
        if which.lower() == "world"
        else "lao_adm_ngd_20191112_shp"
    )

    shapefile_path = os.path.join(ROOT_DIR, output_path, filename)
    download_shapefile(which, output_path)
    extract_shapefiles(which, output_path)

    df = gpd.read_file(shapefile_path.replace(".zip", ""))

    return df
