# Verify world shapefile
from os.path import exists
from urllib.request import urlretrieve

path_to_file = "C:/Users/camil/Dropbox/Servicios/OECD-GGGI/laos-climate-change/laos_climate_change/wb_countries_admin0_10m.zip"
url = "https://datacatalogfiles.worldbank.org/ddh-published/0038272/DR0046659/wb_countries_admin0_10m.zip?versionId=2024-05-14T14:58:01.5696428Z"
filename = "wb_countries_admin0_10m.zip"


def download_shape_files():
    if not exists(path_to_file):
        urlretrieve(url, filename)
    else:
        filename


# Verify Laos shapefile
path_to_file2 = "lao_adm_ngd_20191112_shp.zip"
url2 = "https://data.humdata.org/dataset/9eb6aff1-9e3f-43d3-99a6-f415fe4b4dff/resource/1d6edf99-5303-4b31-8909-dd70cda78443/download/lao_adm_ngd_20191112_shp.zip"
filename2 = "lao_adm_ngd_20191112_shp.zip"


def download_shape_files2():
    if not exists(path_to_file2):
        urlretrieve(url2, filename2)
    else:
        filename2
