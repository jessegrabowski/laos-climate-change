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
