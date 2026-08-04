import logging
import urllib.request

from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd

from climate_risk.const_vars import (
    BIG_RIVERS_FILENAME,
    MEDIUM_BIG_RIVERS_FILENAME,
    RIVERS_SHAPEFILE_FILENAME,
    RIVERS_URL,
    RIVERS_ZIP_FILENAME,
)

_log = logging.getLogger(__name__)


def load_rivers_data(cache_dir: Path, *, include_medium: bool = False) -> gpd.GeoDataFrame:
    data_path = cache_dir / "rivers"
    path_to_zip_file = data_path / RIVERS_ZIP_FILENAME
    path_to_shapefile = data_path / RIVERS_SHAPEFILE_FILENAME
    path_to_big_rivers = data_path / BIG_RIVERS_FILENAME
    path_to_medium_big_rivers = data_path / MEDIUM_BIG_RIVERS_FILENAME
    path_to_extracted = data_path / "HydroRIVERS_v10_shp" / RIVERS_SHAPEFILE_FILENAME

    data_path.mkdir(parents=True, exist_ok=True)

    if not path_to_zip_file.is_file():
        _log.info("Downloading rivers ")

        opener = urllib.request.URLopener()
        opener.addheader(
            "User-Agent",
            "Mozilla/5.0 (Linux i554 x86_64; en-US) AppleWebKit/534.34 (KHTML, like Gecko) "
            "Chrome/55.0.2447.185 Safari/601",
        )

        opener.retrieve(RIVERS_URL, path_to_zip_file)

    if not path_to_shapefile.is_file():
        with ZipFile(path_to_zip_file, "r") as zObject:
            zObject.extractall(path=data_path)

    if include_medium:
        if not path_to_medium_big_rivers.is_file():
            _log.info("Loading and processing rivers data")
            df = gpd.read_file(path_to_extracted)

            medium_and_big_rivers = df.query("ORD_FLOW < 6")
            medium_and_big_rivers.to_file(path_to_medium_big_rivers)
        else:
            medium_and_big_rivers = gpd.read_file(path_to_medium_big_rivers)
        return medium_and_big_rivers

    elif not include_medium:
        if not path_to_big_rivers.is_file():
            _log.info("Loading and processing rivers data")
            df = gpd.read_file(path_to_extracted)

            big_rivers = df.query("ORD_FLOW < 5")
            big_rivers.to_file(path_to_big_rivers)

        if path_to_big_rivers.is_file():
            big_rivers = gpd.read_file(path_to_big_rivers)

        return big_rivers
