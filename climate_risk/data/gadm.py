from collections.abc import Collection, Iterator
from pathlib import Path

import geopandas as gpd
import pandas as pd

from climate_risk.data.source import ManualSource
from climate_risk.exceptions import DataValidationError

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

# One table holds every country at its finest level, so a unit above that is the union of its rows.
GADM_LAYER = "gadm_410"

GID_COLUMNS = {1: ("GID_1", "NAME_1"), 2: ("GID_2", "NAME_2")}

# SQLite caps how many terms an IN list may carry, and a long WHERE also costs more to parse than
# the extra passes cost to run.
GID_CHUNK = 400


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


def _chunks(values: list[str], size: int) -> Iterator[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _units_at_level(gids: list[str], level: int, path: Path, layer: str) -> list[gpd.GeoDataFrame]:
    gid_column, name_column = GID_COLUMNS[level]
    read = []

    for chunk in _chunks(gids, GID_CHUNK):
        quoted = ",".join(f"'{gid}'" for gid in chunk)
        rows = gpd.read_file(path, layer=layer, columns=[gid_column, name_column], where=f"{gid_column} IN ({quoted})")
        if not rows.empty:
            # The table stores the finest level, so a unit above it spans several rows.
            read.append(rows.dissolve(by=gid_column, aggfunc="first", as_index=False))

    return [frame.rename(columns={gid_column: "gid", name_column: "name"}).assign(admin_level=level) for frame in read]


def load_admin_units(
    units: Collection[tuple[str, int]], cache_dir: Path, *, layer: str = GADM_LAYER
) -> gpd.GeoDataFrame:
    """
    Read one polygon per GADM unit named.

    The level comes from the caller because a GADM id does not reliably state it: most countries are
    numbered ``LAO.11_1`` and ``LAO.11.3_1``, but Ghana's provinces are ``GHA11_2`` and its districts
    ``GHA7.13_2``. EM-DAT records the level in the key it files each unit under.

    Parameters
    ----------
    units : collection of tuple of (str, int)
        Each a GADM identifier and its administrative level, 1 or 2. Duplicates are read once.
    cache_dir : Path
        Directory the caches live under.
    layer : str, optional
        Layer to read inside the GeoPackage. Default ``GADM_LAYER``.

    Returns
    -------
    GeoDataFrame
        Columns ``gid``, ``name``, ``admin_level`` and ``geometry``, one row per distinct id.

    Raises
    ------
    NotImplementedError
        If the GeoPackage is absent.
    DataValidationError
        If GADM holds no unit for one of the ids, or a level is one GADM is not read at.
    """
    path = gadm_path(cache_dir)
    requested = set(units)

    by_level: dict[int, list[str]] = {}
    for gid, level in sorted(requested):
        by_level.setdefault(level, []).append(gid)

    unsupported = sorted(set(by_level) - set(GID_COLUMNS))
    if unsupported:
        raise DataValidationError(
            f"Units are read at levels {sorted(GID_COLUMNS)}, but these were asked for at "
            f"{unsupported}: {[gid for level in unsupported for gid in by_level[level][:3]]}"
        )

    frames = [
        frame for level, gids_here in by_level.items() for frame in _units_at_level(gids_here, level, path, layer)
    ]
    resolved = (
        gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs)
        if frames
        else gpd.GeoDataFrame({"gid": [], "name": [], "admin_level": []}, geometry=[])
    )

    missing = sorted({gid for gid, _ in requested} - set(resolved["gid"]))
    if missing:
        raise DataValidationError(
            f"GADM holds no unit for {len(missing)} of {len(requested)} ids, starting {missing[:5]}. "
            f"The GeoPackage version may not match the one the ids were coded against."
        )

    return resolved[["gid", "name", "admin_level", "geometry"]]
