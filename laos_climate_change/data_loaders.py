import os
from os.path import exists
from urllib.request import urlretrieve

WORLD_URL = "https://datacatalogfiles.worldbank.org/ddh-published/0038272/DR0046659/wb_countries_admin0_10m.zip?versionId=2024-05-14T14:58:01.5696428Z"
world_filename = "wb_countries_admin0_10m.zip"
LAOS_URL = "https://data.humdata.org/dataset/9eb6aff1-9e3f-43d3-99a6-f415fe4b4dff/resource/1d6edf99-5303-4b31-8909-dd70cda78443/download/lao_adm_ngd_20191112_shp.zip"
laos_filename = "lao_adm_ngd_20191112_shp.zip"


def download_shapefile(which, output_path="../laos-climate-change/laos_climate_change"):
    if which == "Laos":
        url = LAOS_URL
        filename = laos_filename
        path_to_file = output_path + "/" + filename
    elif which == "world":
        url = WORLD_URL
        filename = world_filename
        path_to_file = output_path + "/" + filename
    else:
        raise NotImplementedError()

    if not exists(output_path):
        os.makedirs(output_path)

    if not exists(path_to_file):
        urlretrieve(url, filename)
