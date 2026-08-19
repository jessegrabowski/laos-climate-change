import re
import sqlite3

from collections import defaultdict
from collections.abc import Iterable, Iterator
from itertools import batched
from pathlib import Path
from typing import NamedTuple

from anyascii import anyascii

from climate_risk.data.gadm import GADM_LAYER, gadm_path

# Words naming what a unit is rather than which one it is. EM-DAT writes them inconsistently and
# GADM does not carry them, so `Kalin-Aapayo province` has to reach `Kalin-Aapayo`.
UNIT_NOUNS = re.compile(
    r"\b(provinces?|prov|districts?|regencies|regency|regions?|cities|city of|city|states?|towns?|"
    r"municipalit(?:y|ies)|islands?|isl|departments?|counties|county|governorates?|prefectures?|"
    r"areas?|near|around|outskirts of|vicinity of|coast of)\b\.?",
    re.IGNORECASE,
)


# EM-DAT writes `Aceh and West Sumatra Provinces` for two units and `Newfoundland and Labrador` for
# one, so the whole string has to be tried before its parts.
CONJUNCTION = re.compile(r"\s+(?:and|&)\s+", re.IGNORECASE)

# `Between Java and Bali` names a stretch of sea by its shores. Splitting it puts the event on
# whichever shore happens to resolve.
RELATIONAL = re.compile(r"^\s*(?:between|off|offshore|au large)\b", re.IGNORECASE)


# How a written place reached the units it did.
NAMED = "named"
CONTAINED_BY = "container"


# GADM publishes a level 5, for Belgium and Rwanda only.
INDEXABLE_LEVELS = (1, 2, 3, 4)


class Placement(NamedTuple):
    """Where one written place put an event.

    Parameters
    ----------
    gids : set of str
        The GADM identifiers reached, empty where the place reached none.
    how : str
        ``NAMED`` where the written place itself resolved, ``CONTAINED_BY`` where only the container
        it was written in did, which is coarser than the prose supports. ``NAMED`` where ``gids`` is
        empty and nothing was reached at all.
    """

    gids: set[str]
    how: str


class Unit(NamedTuple):
    """A GADM unit a name can refer to.

    Parameters
    ----------
    gid : str
        The GADM identifier.
    level : int
        Administrative level, 1 through 4.
    parent : str or None
        The identifier of the unit one level up, or None at level 1.
    """

    gid: str
    level: int
    parent: str | None


class Gazetteer(NamedTuple):
    """One country's units, searchable by name and walkable upwards.

    Parameters
    ----------
    names : dict mapping str to set of Unit
        Units keyed on :func:`match_key` of every name they are published under.
    parent_of : dict mapping str to str or None
        The unit one level up from each identifier.
    """

    names: dict[str, set[Unit]]
    parent_of: dict[str, str | None]

    def _upwards(self, gid: str) -> Iterator[str]:
        """Yield the unit and each container above it, outwards."""
        seen: set[str] = set()
        current: str | None = gid
        # A Gazetteer can be built by hand as well as read, so the walk does not assume acyclic
        # parentage even though :func:`read_gazetteer` refuses to record it.
        while current and current not in seen:
            seen.add(current)
            yield current
            current = self.parent_of.get(current)

    def ancestry(self, gid: str) -> set[str]:
        """Name the unit and every unit containing it."""
        return set(self._upwards(gid))

    def top_container(self, gid: str) -> str:
        """Name the outermost unit holding this one, which is the unit itself where it has no parent."""
        *_, outermost = self._upwards(gid)

        return outermost


_NAME_FIELDS = ("GID", "NAME", "VARNAME")


def _name_columns(level: int, available: set[str]) -> str:
    """Select one level's identifier and names, substituting an empty literal for an absent column."""
    return ", ".join(f"{field}_{level}" if f"{field}_{level}" in available else "''" for field in _NAME_FIELDS)


def match_key(name: str) -> str:
    """
    Reduce a place name to what a written mention and a GADM name can be expected to share.

    Transliterated, stripped of the noun saying what kind of unit it is, and reduced to letters and
    digits, so ``Kalin-Aapayo province`` and ``Kalin Aapayo`` meet.

    Parameters
    ----------
    name : str
        A place as written, from either source.

    Returns
    -------
    str
        The comparison key, empty where the name was only a unit noun.
    """
    return "".join(character for character in anyascii(UNIT_NOUNS.sub(" ", name)) if character.isalnum()).casefold()


def read_gazetteer(iso: str, cache_dir: Path, *, layer: str = GADM_LAYER) -> Gazetteer:
    """
    Read one country's GADM units into a gazetteer.

    Every level the archive publishes is indexed, because written mentions reach all of them: a
    location string names provinces, districts and villages in the same breath. A name reaches a
    set rather than a unit because names repeat — a province and its capital district often share
    one, and a village name recurs freely.

    Parentage comes from the row rather than from the shape of the identifier. Identifiers usually
    nest, but 37 rows across five countries do not, and a prefix test would place those units
    outside their own province.

    Parameters
    ----------
    iso : str
        ISO 3166-1 alpha-3 code of the country to read.
    cache_dir : Path
        Directory the caches live under.
    layer : str, optional
        Layer to read inside the GeoPackage. Default ``GADM_LAYER``.

    Returns
    -------
    Gazetteer
        The country's units.
    """
    names: dict[str, set[Unit]] = defaultdict(set)
    parent_of: dict[str, str | None] = {}

    with sqlite3.connect(gadm_path(cache_dir)) as connection:
        available = {row[1] for row in connection.execute(f'PRAGMA table_info("{layer}")')}
        # A variant-name column is optional; an identifier and a name are what make a level readable.
        levels = [level for level in INDEXABLE_LEVELS if {f"GID_{level}", f"NAME_{level}"} <= available]
        columns = ", ".join(_name_columns(level, available) for level in levels)
        query = f'SELECT DISTINCT {columns} FROM "{layer}" WHERE GID_0 = ?'

        for row in connection.execute(query, (iso,)):
            parent = None
            for level, (gid, name, variants) in zip(levels, batched(row, len(_NAME_FIELDS)), strict=True):
                if not gid:
                    break
                parent_of[gid] = parent
                for field in (name, variants):
                    for alternative in str(field or "").split("|"):
                        if key := match_key(alternative):
                            names[key].add(Unit(gid, level, parent))
                parent = gid

    return Gazetteer(dict(names), parent_of)


def _narrowed(gids: set[str], pinned: set[str], gazetteer: Gazetteer) -> set[str]:
    """Keep the candidates inside something the event already pinned, or all of them if none are."""
    if len(gids) < 2:
        return gids

    return {gid for gid in gids if gazetteer.ancestry(gid) & pinned} or gids


def _outermost(gids: set[str], gazetteer: Gazetteer) -> set[str]:
    """Drop every unit another candidate already contains, leaving what the name can mean at its coarsest."""
    return {gid for gid in gids if not (gazetteer.ancestry(gid) - {gid}) & gids}


def _units_named(name: str, parent: str | None, gazetteer: Gazetteer) -> set[str]:
    """Name the units one written place reaches, narrowed by its stated container where it has one."""
    gids = {unit.gid for unit in gazetteer.names.get(match_key(name), set())}
    if not gids or parent is None:
        return gids

    containers = {unit.gid for unit in gazetteer.names.get(match_key(parent), set())}
    inside = {gid for gid in gids if (gazetteer.ancestry(gid) - {gid}) & containers}

    return inside or gids


def resolve_place(name: str, parent: str | None, gazetteer: Gazetteer) -> set[str]:
    """
    Name the GADM units a written place refers to, using its stated container to choose between them.

    Where the prose gives a container, only units it holds at any depth survive — which is what
    separates one ``Pitogo`` from the other without a similarity threshold. A container that names
    nothing, or that holds none of the candidates, is ignored rather than treated as a
    contradiction: the prose routinely names a region GADM does not model.

    A name joined by ``and`` is split only where the whole fails, so ``Newfoundland and Labrador``
    stays one unit while ``Aceh and West Sumatra`` becomes two. Every part that names something is
    kept, except where the name opens with a word placing the event between its parts rather than
    in them.

    Parameters
    ----------
    name : str
        The place as written.
    parent : str or None
        The container the prose gave, or None.
    gazetteer : Gazetteer
        The country's units, from :func:`read_gazetteer`.

    Returns
    -------
    set of str
        The GADM identifiers the name reaches, empty where it reaches none.
    """
    gids = _units_named(name, parent, gazetteer)
    if gids:
        return _outermost(gids, gazetteer)

    parts = [part.strip() for part in CONJUNCTION.split(name) if part.strip()]
    if len(parts) > 1 and not RELATIONAL.match(name):
        reached = [found for part in parts if (found := _units_named(part, parent, gazetteer))]
        if reached:
            return _outermost(set().union(*reached), gazetteer)

    return set()


def resolve_event_places(places: Iterable[tuple[str, str | None]], gazetteer: Gazetteer) -> list[Placement]:
    """
    Resolve the places one event names together, letting the unambiguous ones narrow the rest.

    An event's places share a footprint, so a mention that lands on exactly one unit tells the
    ambiguous mentions beside it where to look. Candidates outside everything the event has already
    pinned are dropped, and a mention narrowed to nothing keeps its candidates.

    A place naming nothing falls back to the container the prose wrote it in — ``Pesisir Selaten
    (West Sumatra province)`` becomes the province — which is coarser than the prose supports, so
    the result records that it was reached that way.

    Parameters
    ----------
    places : iterable of tuple
        Each a name as written and the container the prose gave, or None.
    gazetteer : Gazetteer
        The country's units, from :func:`read_gazetteer`.

    Returns
    -------
    list of Placement
        Where each place put the event, in the order the places were given.
    """
    written = list(places)
    resolved = [resolve_place(name, parent, gazetteer) for name, parent in written]

    pinned: set[str] = set()
    for gids in resolved:
        if len(gids) == 1:
            pinned |= gazetteer.ancestry(next(iter(gids)))

    placed = []
    for (_, parent), gids in zip(written, resolved, strict=True):
        if gids:
            placed.append(Placement(_narrowed(gids, pinned, gazetteer), NAMED))
            continue
        container = resolve_place(parent, None, gazetteer) if parent else set()
        how = CONTAINED_BY if container else NAMED
        placed.append(Placement(_narrowed(container, pinned, gazetteer), how))

    return placed
