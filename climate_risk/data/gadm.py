from pathlib import Path

from climate_risk.data.source import ManualSource

# GADM's terms exclude redistribution and automated download, so it is declared as a manual source
# and never appears in the fetchable registry.
GADM = ManualSource(
    filename="gadm_410.gpkg",
    homepage="https://gadm.org/download_world.html",
    licence=(
        "Academic use and other non-commercial use only. Redistribution, and use as part of a "
        "commercial product or service, require prior written permission."
    ),
    citation="GADM, Database of Global Administrative Areas, version 4.1. https://gadm.org",
    retrieved="2026-08-09",
)

# The GeoPackage carries every level in one table, so a query names the level it wants.
GADM_LAYER = "gadm_410"


def gadm_dir(cache_dir: Path) -> Path:
    return cache_dir / "gadm"


def gadm_path(cache_dir: Path) -> Path:
    """
    Return the path to the GADM GeoPackage, raising if it has not been placed in the cache.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    Path
        Location of ``gadm_410.gpkg``.

    Raises
    ------
    NotImplementedError
        If the GeoPackage is absent. Its licence forbids downloading it automatically.
    """
    return GADM.require(gadm_dir(cache_dir))
