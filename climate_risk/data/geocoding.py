from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import NamedTuple

import geopandas as gpd

from shapely.geometry import Point

from climate_risk.data.gadm import GADM_LAYER, load_admin_units, load_units_in_country
from climate_risk.data.place_names import Gazetteer, resolve_place
from climate_risk.geo.crs import GEOGRAPHIC_CRS

# A geocoder answers with longitude and latitude, or with nothing where it does not know the place.
Geocoder = Callable[[str, str], tuple[float, float] | None]

# Finest first: a point says where an event was, and the smallest unit holding it says it best.
PLACEABLE_LEVELS = (4, 3, 2, 1)

IN_THE_UNIT = "in the unit"
IN_ITS_PROVINCE = "in its province"
ELSEWHERE = "elsewhere"
NO_POINT = "no point"


class ScoredName(NamedTuple):
    """Where a geocoder put one written place, against the unit its name already resolves to.

    Parameters
    ----------
    name : str
        The place as written.
    gid : str
        The GADM identifier the name resolves to unambiguously.
    outcome : str
        One of ``IN_THE_UNIT``, ``IN_ITS_PROVINCE``, ``ELSEWHERE`` or ``NO_POINT``.
    """

    name: str
    gid: str
    outcome: str


def unambiguous_units(places: Iterable[tuple[str, str | None]], gazetteer: Gazetteer) -> dict[str, str]:
    """
    Keep the written places whose name reaches exactly one GADM unit.

    These are the geocoder's answer key: the name already tells us the unit, so a point that lands
    anywhere else is wrong without anyone having to adjudicate it.

    Parameters
    ----------
    places : iterable of tuple
        Each a name as written and the container the prose gave, or None.
    gazetteer : Gazetteer
        The country's units, from :func:`~climate_risk.data.place_names.read_gazetteer`.

    Returns
    -------
    dict mapping str to str
        The GADM identifier each usable name reaches.
    """
    settled = {}
    for name, parent in places:
        gids = resolve_place(name, parent, gazetteer)
        if len(gids) == 1:
            settled[name] = next(iter(gids))

    return settled


def score_geocoder(
    geocode: Geocoder,
    iso: str,
    places: Iterable[tuple[str, str | None]],
    gazetteer: Gazetteer,
    cache_dir: Path,
    *,
    layer: str = GADM_LAYER,
) -> list[ScoredName]:
    """
    Score a geocoder against the places whose names already resolve to one GADM unit.

    A point is judged three ways: inside the unit the name names, inside the level-1 unit containing
    it, or somewhere else. The middle case is what a coarse but usable geocoder looks like, and
    separating it from the last is the difference between a source worth aggregating upwards and one
    worth discarding.

    Parameters
    ----------
    geocode : callable
        Takes an ISO 3166-1 alpha-3 code and a place name, and returns longitude and latitude, or
        None where it does not know the place.
    iso : str
        ISO 3166-1 alpha-3 code of the country the places are in.
    places : iterable of tuple
        Each a name as written and the container the prose gave, or None.
    gazetteer : Gazetteer
        The country's units, from :func:`~climate_risk.data.place_names.read_gazetteer`.
    cache_dir : Path
        Directory the caches live under.
    layer : str, optional
        Layer to read inside the GeoPackage. Default ``GADM_LAYER``.

    Returns
    -------
    list of ScoredName
        One entry per name that had an answer to check against.
    """
    settled = unambiguous_units(places, gazetteer)
    if not settled:
        return []

    levels = {unit.gid: unit.level for units in gazetteer.names.values() for unit in units}
    wanted = {(gid, levels[gid]) for gid in settled.values()}
    wanted |= {(gazetteer.top_container(gid), 1) for gid in settled.values()}

    polygons = load_admin_units(wanted, cache_dir, layer=layer)
    shapes = dict(zip(polygons["gid"], polygons.geometry, strict=True))

    scored = []
    for name, gid in settled.items():
        located = geocode(iso, name)
        if located is None:
            scored.append(ScoredName(name, gid, NO_POINT))
            continue

        point = Point(*located)
        if shapes[gid].contains(point):
            outcome = IN_THE_UNIT
        elif shapes[gazetteer.top_container(gid)].contains(point):
            outcome = IN_ITS_PROVINCE
        else:
            outcome = ELSEWHERE
        scored.append(ScoredName(name, gid, outcome))

    return scored


def units_containing_points(
    points: Mapping[str, tuple[float, float]],
    iso: str,
    cache_dir: Path,
    *,
    levels: Iterable[int] = PLACEABLE_LEVELS,
    layer: str = GADM_LAYER,
) -> dict[str, str]:
    """
    Name the finest GADM unit holding each point.

    Falling back to the container a place was written in claims every unit inside it — a province
    spans fourteen districts at the median — so a point is worth reaching for first wherever one
    exists.

    Parameters
    ----------
    points : mapping of str to tuple of float
        Longitude and latitude, keyed on the written name they came from.
    iso : str
        ISO 3166-1 alpha-3 code of the country the points are in.
    cache_dir : Path
        Directory the caches live under.
    levels : iterable of int, optional
        Administrative levels to try, in order. Default finest to coarsest.
    layer : str, optional
        Layer to read inside the GeoPackage. Default ``GADM_LAYER``.

    Returns
    -------
    dict mapping str to str
        The GADM identifier each name's point falls in, absent where no level holds it.
    """
    if not points:
        return {}

    placed: dict[str, str] = {}
    outstanding = dict(points)

    for level in levels:
        if not outstanding:
            break
        units = load_units_in_country(iso, level, cache_dir, layer=layer)
        if units.empty:
            continue

        located = gpd.GeoDataFrame(
            {"name": list(outstanding)},
            geometry=gpd.points_from_xy(*zip(*outstanding.values(), strict=True)),
            crs=GEOGRAPHIC_CRS,
        )
        inside = gpd.sjoin(located, units[["gid", "geometry"]], how="inner", predicate="within")
        placed |= dict(zip(inside["name"], inside["gid"], strict=True))
        outstanding = {name: point for name, point in outstanding.items() if name not in placed}

    return placed
