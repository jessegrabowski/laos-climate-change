import os
from os.path import exists
from urllib.request import urlretrieve
import const_vars

WORLD_URL = const_vars.WORLD_URL
WORLD_FILENAME = const_vars.WORLD_FILENAME
LAOS_URL = const_vars.LAOS_URL
LAOS_FILENAME = const_vars.LAOS_FILENAME


def download_shapefile(which, output_path="../data/shapefiles"):
    if which == "Laos":
        url = LAOS_URL
        filename = LAOS_FILENAME
        path_to_file = output_path + "/" + filename
    elif which == "world":
        url = WORLD_URL
        filename = WORLD_FILENAME
        path_to_file = output_path + "/" + filename
    else:
        raise NotImplementedError()

    if not exists(output_path):
        os.makedirs(output_path)
        urlretrieve(url, path_to_file)

    if not exists(path_to_file):
        urlretrieve(url, path_to_file)
