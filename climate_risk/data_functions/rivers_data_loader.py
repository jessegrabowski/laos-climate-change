import logging

from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd

from climate_risk.data.cache import cached, geo_parquet
from climate_risk.data.fetch import fetch
from climate_risk.data.source import DataSource

_log = logging.getLogger(__name__)

RIVERS = DataSource(
    url="https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_shp.zip",
    filename="HydroRIVERS_v10_shp.zip",
    licence="HydroSHEDS License Agreement: free for scientific, educational and commercial use",
    citation=(
        "Lehner, B., Grill, G. (2013): Global river hydrography and network routing: baseline data "
        "and new approaches to study the world's large river systems. Hydrological Processes, "
        "27(15), 2171-2186. https://doi.org/10.1002/hyp.9740"
    ),
    retrieved="2026-08-08",
)

# The archive unpacks into a directory named for itself.
RIVERS_MEMBER = "HydroRIVERS_v10_shp/HydroRIVERS_v10.shp"

RIVERS_SUBDIRECTORY = "rivers"

# Stream order runs low-to-high from the largest rivers down, so a lower cutoff keeps fewer, bigger
# ones. The panel uses the major rivers alone; the wider set exists for sensitivity checks.
BIG_RIVER_ORDER = 5
MEDIUM_RIVER_ORDER = 6


def transform_rivers(rivers: gpd.GeoDataFrame, stream_order_cutoff: int) -> gpd.GeoDataFrame:
    """
    Keep the rivers whose stream order is below the cutoff.

    Parameters
    ----------
    rivers : GeoDataFrame
        The HydroRIVERS network, carrying an ``ORD_FLOW`` stream order.
    stream_order_cutoff : int
        The exclusive upper bound on stream order. Order runs low-to-high from the largest
        rivers down, so a lower cutoff keeps fewer and bigger ones.

    Returns
    -------
    kept : GeoDataFrame
        The rivers that clear the cutoff.
    """
    return rivers.query(f"ORD_FLOW < {stream_order_cutoff}")


def _extract_rivers(cache_dir: Path) -> Path:
    """Unpack the archive unless the network is already on disk, and return the shapefile."""
    directory = cache_dir / RIVERS_SUBDIRECTORY
    extracted = directory / RIVERS_MEMBER

    if not extracted.exists():
        _log.info(f"Extracting {RIVERS.filename}")
        with ZipFile(fetch(RIVERS, directory)) as archive:
            archive.extractall(path=directory)

    return extracted


def load_rivers_data(cache_dir: Path, *, include_medium: bool = False) -> gpd.GeoDataFrame:
    cutoff = MEDIUM_RIVER_ORDER if include_medium else BIG_RIVER_ORDER

    def build() -> gpd.GeoDataFrame:
        return transform_rivers(gpd.read_file(_extract_rivers(cache_dir)), cutoff)

    return cached(
        cache_dir / RIVERS_SUBDIRECTORY,
        "rivers",
        build,
        geo_parquet(),
        params={"stream_order_below": cutoff},
    )
