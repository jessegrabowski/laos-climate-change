import logging
import shutil

from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

import geopandas as gpd

from climate_risk.const_vars import (
    BIG_RIVERS_FILENAME,
    MEDIUM_BIG_RIVERS_FILENAME,
    RIVERS_ARCHIVE_DIRNAME,
    RIVERS_SHAPEFILE_FILENAME,
    RIVERS_URL,
    RIVERS_ZIP_FILENAME,
)

# HydroSHEDS rejects urllib's default agent with a 403.
RIVERS_USER_AGENT = "climate-risk (+https://github.com/jessegrabowski/laos-climate-change)"

_log = logging.getLogger(__name__)


def load_rivers_data(cache_dir: Path, *, include_medium: bool = False) -> gpd.GeoDataFrame:
    data_path = cache_dir / "rivers"
    path_to_zip_file = data_path / RIVERS_ZIP_FILENAME
    path_to_extracted = data_path / RIVERS_ARCHIVE_DIRNAME / RIVERS_SHAPEFILE_FILENAME

    if include_medium:
        processed_path, stream_order_cutoff = data_path / MEDIUM_BIG_RIVERS_FILENAME, 6
    else:
        processed_path, stream_order_cutoff = data_path / BIG_RIVERS_FILENAME, 5

    if processed_path.is_file():
        return gpd.read_file(processed_path)

    data_path.mkdir(parents=True, exist_ok=True)

    # The archive is only needed to build the processed file.
    if not path_to_zip_file.is_file():
        _log.info("Downloading rivers")
        request = Request(RIVERS_URL, headers={"User-Agent": RIVERS_USER_AGENT})
        with urlopen(request) as response, path_to_zip_file.open("wb") as archive:
            shutil.copyfileobj(response, archive)

    if not path_to_extracted.is_file():
        with ZipFile(path_to_zip_file, "r") as zObject:
            zObject.extractall(path=data_path)

    _log.info("Loading and processing rivers data")
    gpd.read_file(path_to_extracted).query(f"ORD_FLOW < {stream_order_cutoff}").to_file(processed_path)

    return gpd.read_file(processed_path)
