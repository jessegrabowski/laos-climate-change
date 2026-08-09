import unicodedata

from collections.abc import Mapping
from pathlib import Path

import geopandas as gpd
import pandas as pd

from climate_risk.data.source import ManualSource

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
