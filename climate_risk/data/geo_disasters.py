import logging
import unicodedata

from collections.abc import Mapping
from pathlib import Path

import geopandas as gpd
import pandas as pd

from climate_risk.data.gadm import load_units_in_country
from climate_risk.data.source import ManualSource
from climate_risk.exceptions import DataValidationError

_log = logging.getLogger(__name__)

# The geometries are a GAUL 2015 derivative and non-commercial, so the archive is placed by hand
# and never appears in the fetchable registry. The attribute table is CC-BY-4.0.
GEO_DISASTERS = ManualSource(
    filename="disaster_subnational_90_23.gpkg",
    homepage="https://doi.org/10.5281/zenodo.15487667",
    licence=(
        "Spatial geometries are © FAO 2015 under the GAUL 2015 Data Licence, non-commercial with "
        "attribution required. All non-spatial attributes are CC-BY-4.0."
    ),
    citation=(
        "Teber, K., Weynants, M., Gans, F., & Mahecha, M. D. (2025). Geo-Disasters v1.0.0: geocoded "
        "EM-DAT climate-disaster footprints (1990-2023). https://doi.org/10.5281/zenodo.15487667"
    ),
    retrieved="2026-08-09",
)

GEO_DISASTERS_LAYER = "disaster_subnational_90_23"

# What a location is keyed and named by, per admin level.
NAME_COLUMNS = {1: "ADM1_NAME", 2: "ADM2_NAME"}

LOCATION_COLUMNS = ["DisNo.", "ISO", "admin_level", "geocoding_q", "ADM1_NAME", "ADM2_NAME"]

# Attribution required by the GAUL 2015 Data Licence, clause 2(a), verbatim.
GAUL_ATTRIBUTION = (
    "Source of Administrative boundaries: The Global Administrative Unit Layers (GAUL) dataset, "
    "implemented by FAO within the CountrySTAT and Agricultural Market Information System (AMIS) "
    "projects"
)


def geo_disasters_dir(cache_dir: Path) -> Path:
    return cache_dir / "geo_disasters"


def geo_disasters_path(cache_dir: Path) -> Path:
    """
    Return the path to the Geo-Disasters GeoPackage, raising if it has not been placed in the cache.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    Path
        Location of ``disaster_subnational_90_23.gpkg``.
    """
    return GEO_DISASTERS.require(geo_disasters_dir(cache_dir))


def load_event_locations(cache_dir: Path, *, iso: str | None = None, layer: str = GEO_DISASTERS_LAYER) -> pd.DataFrame:
    """
    Read the geocoded locations Geo-Disasters records, one row per affected administrative unit.

    Geometry is left on disk. The polygons carry the non-commercial GAUL licence while the attribute
    table is CC-BY-4.0, and the attributes are what a comparison against EM-DAT needs.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.
    iso : str, optional
        Restrict to one ISO 3166-1 alpha-3 country code. Default None, meaning every country.
    layer : str, optional
        Layer to read inside the GeoPackage. Default ``GEO_DISASTERS_LAYER``.

    Returns
    -------
    DataFrame
        Columns ``DisNo.``, ``ISO``, ``admin_level``, ``geocoding_q``, ``ADM1_NAME`` and
        ``ADM2_NAME``, one row per location.
    """
    path = geo_disasters_path(cache_dir)
    where = f"ISO = '{iso}'" if iso is not None else None

    locations = gpd.read_file(path, layer=layer, columns=LOCATION_COLUMNS, where=where, ignore_geometry=True)

    return pd.DataFrame(locations).reset_index(drop=True)


def unit_names(locations: pd.DataFrame) -> pd.Series:
    """
    Name each location at the level it was geocoded to.

    Parameters
    ----------
    locations : DataFrame
        Rows as :func:`load_event_locations` returns them.

    Returns
    -------
    Series
        One name per row, taken from the column its ``admin_level`` points at.
    """
    named = pd.Series(pd.NA, index=locations.index, dtype="object")
    for level, column in NAME_COLUMNS.items():
        at_level = locations["admin_level"] == level
        named[at_level] = locations.loc[at_level, column]

    return named


def load_event_footprints(cache_dir: Path, *, iso: str, layer: str = GEO_DISASTERS_LAYER) -> gpd.GeoDataFrame:
    """
    Read one country's geocoded locations with the polygons attached.

    These polygons are the non-commercial half of the licence, and :data:`GAUL_ATTRIBUTION` has to
    appear on anything derived from them. :func:`load_event_locations` reads the same rows without
    geometry where the attributes alone will do.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.
    iso : str
        ISO 3166-1 alpha-3 country code to read.
    layer : str, optional
        Layer to read inside the GeoPackage. Default ``GEO_DISASTERS_LAYER``.

    Returns
    -------
    GeoDataFrame
        The columns of :func:`load_event_locations` and the footprint of each location.
    """
    footprints = gpd.read_file(geo_disasters_path(cache_dir), layer=layer, where=f"ISO = '{iso}'")

    return footprints.reset_index(drop=True)


EQUAL_AREA_CRS = "ESRI:54009"

RESOLVED_DTYPES = {
    "DisNo.": "string",
    "ISO": "string",
    "geometry_source": "string",
    "gid": "string",
    "name": "string",
    "admin_level": "Int64",
    "geocoding_q": "Int64",
    "overlap": "float64",
}

RESOLVED_COLUMNS = list(RESOLVED_DTYPES)


def _best_unit_per_footprint(footprints: gpd.GeoDataFrame, units: gpd.GeoDataFrame) -> pd.DataFrame:
    """Pair each footprint with the single unit covering most of it, dropping any that meet none."""
    located = footprints[["DisNo.", "ISO", "geocoding_q", "geometry"]].reset_index(names="footprint")
    pieces = gpd.overlay(located, units, how="intersection", keep_geom_type=False)

    # Two polygons meeting along an edge intersect in a line, which `keep_geom_type=False` keeps and
    # which covers none of the footprint. Taking the largest would place it in a unit it only borders.
    pieces = pieces.assign(covered=pieces.geometry.area)
    pieces = pieces[pieces["covered"] > 0.0]
    if pieces.empty:
        return pd.DataFrame(columns=RESOLVED_COLUMNS)

    best = pieces.sort_values("covered").groupby("footprint").tail(1).set_index("footprint")
    shares = best["covered"] / footprints.geometry.area.reindex(best.index)

    return best.assign(overlap=shares).drop(columns=["geometry", "covered"])


def resolve_to_gadm(footprints: gpd.GeoDataFrame, cache_dir: Path) -> pd.DataFrame:
    """
    Name each Geo-Disasters footprint as the GADM unit it covers, so it can join EM-DAT's own units.

    The two gazetteers share no identifier and spell the same unit differently, so a footprint is
    placed by where it is rather than what it is called, and the largest overlap wins outright. No
    minimum share applies: the published polygons are simplified to 0.005°, roughly 550 m, which
    costs a small municipality a third of its area and a province almost none, so the same share
    means different things at different sizes.

    A footprint covering no unit at all is dropped and logged.

    Parameters
    ----------
    footprints : GeoDataFrame
        Locations for one country, as :func:`load_event_footprints` returns them.
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    DataFrame
        ``DisNo.``, ``ISO``, ``geometry_source``, the GADM unit that was matched, the location's
        ``geocoding_q``, and ``overlap``, the share of the footprint the unit covers.
    """
    if footprints.empty:
        return pd.DataFrame(columns=RESOLVED_COLUMNS).astype(RESOLVED_DTYPES)

    countries = set(footprints["ISO"])
    if len(countries) > 1:
        raise DataValidationError(
            f"resolve_to_gadm reads one country's units at a time, but these footprints span "
            f"{sorted(countries)}. Call it once per country."
        )

    iso = countries.pop()
    matched = []

    for level in sorted(set(footprints["admin_level"]) & set(NAME_COLUMNS)):
        at_level = footprints[footprints["admin_level"] == level].to_crs(EQUAL_AREA_CRS)
        units = load_units_in_country(iso, level, cache_dir).to_crs(EQUAL_AREA_CRS)
        if units.empty:
            _log.warning("GADM holds no level-%d unit for %s, so %d footprints go unplaced", level, iso, len(at_level))
            continue

        matched.append(_best_unit_per_footprint(at_level, units))

    resolved = pd.concat(matched) if matched else pd.DataFrame(columns=RESOLVED_COLUMNS)
    unplaced = len(footprints) - len(resolved)
    if unplaced:
        _log.warning("%d of %d %s footprints cover no GADM unit and were dropped", unplaced, len(footprints), iso)

    return (
        pd.DataFrame(resolved)
        .assign(geometry_source="geo_disasters")[RESOLVED_COLUMNS]
        .sort_values(["DisNo.", "gid"])
        .reset_index(drop=True)
        .astype(RESOLVED_DTYPES)
    )


def normalise_unit_name(name: str) -> str:
    """
    Reduce an administrative unit's name to what two gazetteers can be expected to agree on.

    GADM and GAUL romanise the same unit differently — accents, hyphens and casing all drift — so a
    literal comparison reports spelling as disagreement.

    Parameters
    ----------
    name : str
        A unit name as either source publishes it.

    Returns
    -------
    str
        Casefolded, stripped of accents and of everything that is not a letter or digit.
    """
    decomposed = unicodedata.normalize("NFKD", name)
    return "".join(character for character in decomposed if character.isalnum()).casefold()


def event_unit_names(locations: pd.DataFrame) -> dict[str, set[str]]:
    """
    Collect the unit names Geo-Disasters records, keyed on the EM-DAT event id.

    Parameters
    ----------
    locations : DataFrame
        Rows as :func:`load_event_locations` returns them.

    Returns
    -------
    dict mapping str to set of str
        One entry per event, holding every unit it was geocoded to, named as published.
    """
    named = locations.assign(unit=unit_names(locations))

    return {str(disno): set(group) for disno, group in named.groupby("DisNo.")["unit"]}


AGREEMENT_LEVELS = ("exact", "partial", "disjoint", "gained", "unmatched")

AGREEMENT_COLUMNS = ["DisNo.", "agreement", "em_dat_units", "geo_disasters_units", "shared_units"]


def _classify(em_dat: set[str], geo_disasters: set[str]) -> str:
    if not em_dat:
        return "gained"
    if not geo_disasters:
        return "unmatched"
    if em_dat == geo_disasters:
        return "exact"

    return "partial" if em_dat & geo_disasters else "disjoint"


def compare_event_units(em_dat: Mapping[str, set[str]], geo_disasters: Mapping[str, set[str]]) -> pd.DataFrame:
    """
    Report how EM-DAT's own geocoding and Geo-Disasters' agree, event by event.

    The two are keyed on ``DisNo.`` and nothing else: EM-DAT names GADM units and Geo-Disasters names
    GAUL ones, and the two gazetteers share no identifier, so units are matched on their names, put
    through :func:`normalise_unit_name` here rather than by either caller.

    Each event is classified as ``exact`` when both name the same units, ``partial`` when they
    overlap, ``disjoint`` when both name units and none is shared, ``gained`` when only
    Geo-Disasters has any, and ``unmatched`` when only EM-DAT does. An event neither has is absent.

    Parameters
    ----------
    em_dat : mapping of str to set of str
        Unit names EM-DAT records, keyed on event id.
    geo_disasters : mapping of str to set of str
        The same from Geo-Disasters, as :func:`event_unit_names` returns it.

    Returns
    -------
    DataFrame
        Columns ``DisNo.``, ``agreement`` and the three counts, one row per event either source
        geocoded, ordered by event id.
    """
    rows = []

    for disno in sorted(em_dat.keys() | geo_disasters.keys()):
        recorded = {normalise_unit_name(name) for name in em_dat.get(disno, ()) if name}
        published = {normalise_unit_name(name) for name in geo_disasters.get(disno, ()) if name}
        if not recorded and not published:
            continue

        rows.append(
            {
                "DisNo.": disno,
                "agreement": _classify(recorded, published),
                "em_dat_units": len(recorded),
                "geo_disasters_units": len(published),
                "shared_units": len(recorded & published),
            }
        )

    return pd.DataFrame(rows, columns=AGREEMENT_COLUMNS)
