from pyprojroot import here
import os
from os.path import exists
from urllib.request import urlretrieve
from zipfile import ZipFile
import geopandas as gpd
from laos_gggi.const_vars import WORLD_URL, WORLD_FILENAME, LAOS_URL, LAOS_FILENAME
import logging

_log = logging.getLogger(__name__)


shapefile_name_dict = {
    "world": WORLD_FILENAME.replace(".zip", ""),
    "laos": LAOS_FILENAME.replace(".zip", ""),
}


def download_shapefile(which, output_path="data/shapefiles", force_reload=False):
    if which.lower() not in ["laos", "world"]:
        raise ValueError(f'which should be one of ["world", "laos"], got {which}')
    url = LAOS_URL if which.lower() == "laos" else WORLD_URL
    filename = LAOS_FILENAME if which.lower() == "laos" else WORLD_FILENAME

    output_path = here(output_path)
    path_to_file = os.path.join(output_path, filename)

    if not exists(output_path):
        os.makedirs(output_path)

    if not exists(path_to_file) or force_reload:
        _log.info(f"Downloading {which} shapefiles to {output_path}")
        urlretrieve(url, path_to_file)


def extract_shapefiles(which: str, output_path="data/shapefiles", force_reload=False):
    if which.lower() not in ["world", "laos"]:
        raise ValueError(f'which should be one of ["world", "laos"], got {which}')
    filename = shapefile_name_dict[which.lower()]
    shapefile_path = str(here(os.path.join(output_path, filename)))

    if not os.path.isdir(shapefile_path) or force_reload:
        _log.info(f"Extracting {shapefile_path}")
        fname = filename + ".zip"

        with ZipFile(here(os.path.join(output_path, fname)), "r") as zObject:
            zObject.extractall(path=here(output_path))


def load_shapefile(
    which, output_path="data/shapefiles", force_reload=False, repair_ISO_codes=True
):
    if which.lower() not in ["world", "laos"]:
        raise ValueError(f'which should be one of ["world", "laos"], got {which}')
    filename = (
        "wb_countries_admin0_10m"
        if which.lower() == "world"
        else "lao_adm_ngd_20191112_shp"
    )

    shapefile_path = str(here(os.path.join(output_path, filename)))
    download_shapefile(which, output_path, force_reload=force_reload)
    extract_shapefiles(which, output_path, force_reload=force_reload)

    df = gpd.read_file(shapefile_path.replace(".zip", ""), layer=0)

    if which == "world" and repair_ISO_codes:
        # The ISO codes are not 1:1 with geometries. This code cleans things up, mostly
        # by dropping small island colonies.

        # Drop UMI (United State Maritime Islands)
        df = df.loc[lambda x: x.ISO_A3 != "UMI"].copy()

        # Drop Gitmo, Clipperton Island, and Australian Indian Ocean territories
        # These are associated with their owner's ISO code, but are far-flung
        df.drop(labels=[129, 232, 238, 239], inplace=True)

        # Drop the Netherland's overseas holdings (Bonaire, Saint Eustatius, Saba)
        # Ditto -- they are labeled as the Netherlands
        df.drop(labels=[234, 235, 236], inplace=True)

        # Drop Tokelau (NZ)
        df.drop(labels=[249], inplace=True)

        # Give France, Norway, and Kosovo the correct ISO3 codes
        # These are the biggest problems. France doesn't have the correct ISO code at all, nor does Norway
        # (both are given -99)
        df.loc[20, "ISO_A3"] = "FRA"
        df.loc[50, "ISO_A3"] = "NOR"
        df.loc[62, "ISO_A3"] = "UNK"  # Kosovo doesn't have a code :(

        df.reset_index(drop=True, inplace=True)

        # Check that ISO codes are unique for each geometry
        assert (df["ISO_A3"].value_counts() == 1).all()

    return df
