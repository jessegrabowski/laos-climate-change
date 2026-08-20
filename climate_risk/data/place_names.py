import csv
import re
import sqlite3

from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from itertools import batched
from pathlib import Path
from typing import NamedTuple

import polars as pl

from anyascii import anyascii

from climate_risk.data.cache import cached, polars_parquet
from climate_risk.data.gadm import GADM_LAYER, administered_territories, gadm_dir, gadm_path

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


# A sea, a river or a mountain range is not an administrative unit, whatever it is one edit from.
# Units named after a feature — `River Nile State`, `Bay of Plenty` — still match exactly; only the
# approximate lookup refuses them.
FEATURE = re.compile(
    r"\b(seas?|oceans?|rivers?|lakes?|gulfs?|straits?|detroit|bays?|mountains?|mts?|mount|peaks?|"
    r"valleys?|deltas?|peninsulas?|channels?|canals?|reservoirs?|dams?|volcanoe?s?|glaciers?|"
    r"basins?|capes?|sounds?|fjords?|lagoons?|swamps?|forests?|deserts?)\b",
    re.IGNORECASE,
)

# Below this a single edit is a large share of the name and the match stops meaning anything:
# `Arora` sits one edit from both `Aurora` and `Arora` in half the countries that have either.
MIN_APPROXIMATE_LENGTH = 6

# Corrections a person or a model has checked one at a time. Approximate matching proposes them;
# only what is written here is ever applied, so an unreviewed near miss leaves a place unplaced
# rather than renaming it.
NAME_CORRECTIONS = Path(__file__).parent / "name_corrections.csv"

# EM-DAT files an event under the country that existed at the time, and GADM only models the ones
# that exist now. Where a state left one successor the mapping is settled; where it left several
# the location text has to choose between them.
SUCCEEDED_BY = {
    "AZO": ("PRT",),
    "CSK": ("CZE", "SVK"),
    "DDR": ("DEU",),
    "DFR": ("DEU",),
    "SUN": (
        "ARM",
        "AZE",
        "BLR",
        "EST",
        "GEO",
        "KAZ",
        "KGZ",
        "LTU",
        "LVA",
        "MDA",
        "RUS",
        "TJK",
        "TKM",
        "UKR",
        "UZB",
    ),
    "YMD": ("YEM",),
    "YMN": ("YEM",),
    "YUG": ("BIH", "HRV", "MKD", "MNE", "SRB", "SVN", "XKO"),
}

# Written places that name no administrative unit and never will: a compass point covering the
# whole country, a position between two others, a stretch of water, or nothing at all. They are
# recorded rather than counted as failures, because no source can place them.
QUALIFIER = re.compile(
    r"^(?:north|south|east|west|central|centre|center|northern|southern|eastern|western|"
    r"north[- ]?(?:east|west)|south[- ]?(?:east|west)|countrywide|nationwide|whole country|"
    r"all country|widespread|unknown|not available|no information|n\.?a\.?(?: on the source)?)$",
    re.IGNORECASE,
)
NOTHING_LEGIBLE = re.compile(r"^[\W\d\s]*$")

# How a written place reached the units it did.
NAMED = "named"
LOCATED = "located"
CONTAINED_BY = "container"
CORRECTED = "corrected"
NAMES_NO_UNIT = "names no unit"


# GADM publishes a level 5, for Belgium and Rwanda only.
INDEXABLE_LEVELS = (1, 2, 3, 4)

# The flattened index, as it is cached: one row per name a unit is published under.
INDEX_COLUMNS = {"key": pl.String, "gid": pl.String, "level": pl.Int8, "parent": pl.String}


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
    corrections : dict mapping str to str
        The published name each checked misspelling stands for, keyed on :func:`match_key`.
    """

    names: dict[str, set[Unit]]
    parent_of: dict[str, str | None]
    corrections: dict[str, str]

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


def read_gazetteer(iso: str, cache_dir: Path, *, layer: str = GADM_LAYER, force_reload: bool = False) -> Gazetteer:
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
    force_reload : bool, optional
        Rebuild even when the index is already cached. Default False.

    Returns
    -------
    Gazetteer
        The country's units.
    """

    def build() -> pl.DataFrame:
        indexed: list[tuple[str, str, int, str | None]] = []
        with sqlite3.connect(gadm_path(cache_dir)) as connection:
            available = {row[1] for row in connection.execute(f'PRAGMA table_info("{layer}")')}
            # A variant-name column is optional; an identifier and a name are what make a level readable.
            levels = [level for level in INDEXABLE_LEVELS if {f"GID_{level}", f"NAME_{level}"} <= available]
            columns = ", ".join(_name_columns(level, available) for level in levels)
            # Kashmir is filed under codes of its own, not under the country administering it.
            held = (iso, *administered_territories(iso, cache_dir, layer=layer))
            placeholders = ", ".join("?" * len(held))
            query = f'SELECT DISTINCT {columns} FROM "{layer}" WHERE GID_0 IN ({placeholders})'

            for row in connection.execute(query, held):
                parent = None
                for level, (gid, name, variants) in zip(levels, batched(row, len(_NAME_FIELDS)), strict=True):
                    # GADM writes an unnamed unit as `?` at every level it spans, and a unit cannot
                    # contain itself: the chain ends where the identifier stops changing.
                    if not gid or gid == parent:
                        break
                    # A row without a key still records the unit's parentage: GADM leaves some
                    # units unnamed, and a walk upwards passes through them.
                    indexed.append(("", gid, level, parent))
                    for field in (name, variants):
                        for alternative in str(field or "").split("|"):
                            if key := match_key(alternative):
                                indexed.append((key, gid, level, parent))
                    parent = gid

        return pl.DataFrame(indexed, schema=INDEX_COLUMNS, orient="row")

    indexed = cached(
        gadm_dir(cache_dir),
        "gazetteer",
        build,
        polars_parquet(),
        # The index is keyed by `match_key`, so the cache turns over when those rules change.
        params={"iso": iso},
        force=force_reload,
    )

    names: dict[str, set[Unit]] = defaultdict(set)
    parent_of: dict[str, str | None] = {}
    for key, gid, level, parent in indexed.iter_rows():
        if key:
            names[key].add(Unit(gid, level, parent))
        parent_of[gid] = parent

    return Gazetteer(dict(names), parent_of, read_name_corrections(iso))


def read_name_corrections(iso: str, *, path: Path = NAME_CORRECTIONS) -> dict[str, str]:
    """
    Read the checked corrections for one country.

    Parameters
    ----------
    iso : str
        ISO 3166-1 alpha-3 code of the country to read.
    path : Path, optional
        The corrections table. Default the one shipped with the package.

    Returns
    -------
    dict mapping str to str
        The published name each misspelling stands for, both keyed by :func:`match_key`.
    """
    if not path.exists():
        return {}

    with path.open(encoding="utf-8", newline="") as handle:
        return {
            match_key(row["written"]): row["corrected"]
            for row in csv.DictReader(handle)
            if row["iso"] == iso and row["corrected"]
        }


def name_shapes(gazetteer: Gazetteer) -> dict[tuple[str, int], set[str]]:
    """Group a country's names by first character and length, which is what :func:`nearest_name` scans."""
    shapes: dict[tuple[str, int], set[str]] = defaultdict(set)
    for key in gazetteer.names:
        shapes[(key[0], len(key))].add(key)

    return dict(shapes)


def _one_edit_apart(written: str, published: str) -> bool:
    """Whether one insertion, deletion or substitution turns one key into the other."""
    if abs(len(written) - len(published)) > 1:
        return False
    if len(written) == len(published):
        return sum(a != b for a, b in zip(written, published, strict=True)) <= 1

    longer, shorter = (written, published) if len(written) > len(published) else (published, written)
    skipped = next(
        (position for position, pair in enumerate(zip(longer, shorter, strict=False)) if pair[0] != pair[1]),
        len(shorter),
    )

    return longer[skipped + 1 :] == shorter[skipped:]


def nearest_name(name: str, gazetteer: Gazetteer, shapes: dict[tuple[str, int], set[str]]) -> str | None:
    """
    Find the one published name a written place is a misspelling of.

    A match is only offered where the written name is long enough for a single edit to be a small
    part of it, does not name a physical feature, and is one edit from exactly one published name. Two names equally close is not a near miss, it is a
    choice, and this makes none.

    Parameters
    ----------
    name : str
        The place as written.
    gazetteer : Gazetteer
        The country's units, from :func:`read_gazetteer`.
    shapes : dict mapping tuple to set of str
        The country's names grouped for searching, from :func:`name_shapes`.

    Returns
    -------
    str or None
        The matching key in ``gazetteer.names``, or None where the gates reject the name or no
        single published name is close enough.
    """
    if FEATURE.search(name):
        return None

    key = match_key(name)
    if len(key) < MIN_APPROXIMATE_LENGTH or key in gazetteer.names:
        return None

    # A typo rarely changes the first character, and scanning by it keeps the search local.
    nearby = {
        candidate
        for length in range(len(key) - 1, len(key) + 2)
        for candidate in shapes.get((key[0], length), ())
        if _one_edit_apart(key, candidate)
    }

    return next(iter(nearby)) if len(nearby) == 1 else None


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


def resolve_event_places(
    places: Iterable[tuple[str, str | None]],
    gazetteer: Gazetteer,
    *,
    located: Mapping[str, str] | None = None,
) -> list[Placement]:
    """
    Resolve the places one event names together, letting the unambiguous ones narrow the rest.

    An event's places share a footprint, so a mention that lands on exactly one unit tells the
    ambiguous mentions beside it where to look. Candidates outside everything the event has already
    pinned are dropped, and a mention narrowed to nothing keeps its candidates.

    A place naming nothing takes the unit a point put it in where one is offered. Failing that it
    falls back to the container the prose wrote it in — ``Pesisir Selaten (West Sumatra province)``
    becomes the province, which spans fourteen districts at the median — so the result records
    which of the two it was reached by. A place with no container that is one edit from
    exactly one published name is taken as a misspelling of it, recorded as such.

    Parameters
    ----------
    places : iterable of tuple
        Each a name as written and the container the prose gave, or None.
    gazetteer : Gazetteer
        The country's units, from :func:`read_gazetteer`.
    located : mapping of str to str, optional
        The unit a point put a written place in, keyed on the name. Default None. A point beats the
        container because it names one unit where the container names everything inside it.

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
    for (name, parent), gids in zip(written, resolved, strict=True):
        if gids:
            placed.append(Placement(_narrowed(gids, pinned, gazetteer), NAMED))
            continue
        by_point = (located or {}).get(name)
        if by_point:
            placed.append(Placement({by_point}, LOCATED))
            continue
        container = resolve_place(parent, None, gazetteer) if parent else set()
        if container:
            placed.append(Placement(_narrowed(container, pinned, gazetteer), CONTAINED_BY))
            continue
        published = gazetteer.corrections.get(match_key(name))
        if published:
            corrected = _outermost({unit.gid for unit in gazetteer.names[published]}, gazetteer)
            placed.append(Placement(_narrowed(corrected, pinned, gazetteer), CORRECTED))
            continue
        placed.append(Placement(set(), NAMES_NO_UNIT if names_no_unit(name) else NAMED))

    return placed


def successor_state(
    places: Iterable[tuple[str, str | None]],
    iso: str,
    cache_dir: Path,
    *,
    layer: str = GADM_LAYER,
) -> str | None:
    """
    Name the modern country whose gazetteer an event's places belong to.

    A state that left one successor needs no evidence. Where it left several, the successor placing
    strictly more of the written places than any other takes the event: a Soviet flood naming
    Tashkent is Uzbek, and one naming nothing recognisable stays unplaced rather than being assigned
    to the largest successor.

    Parameters
    ----------
    places : iterable of tuple
        Each a name as written and the container the prose gave, or None.
    iso : str
        ISO 3166-1 alpha-3 code EM-DAT filed the event under.
    cache_dir : Path
        Directory the caches live under.
    layer : str, optional
        Layer to read inside the GeoPackage. Default ``GADM_LAYER``.

    Returns
    -------
    str or None
        The successor's ISO code, or None where the state has no successor recorded or its
        successors cannot be told apart.
    """
    successors = SUCCEEDED_BY.get(iso)
    if not successors:
        return None
    if len(successors) == 1:
        return successors[0]

    written = list(places)
    placed: dict[str, int] = {}
    for successor in successors:
        gazetteer = read_gazetteer(successor, cache_dir, layer=layer)
        if gazetteer.names:
            placed[successor] = sum(bool(resolve_place(name, parent, gazetteer)) for name, parent in written)

    best = max(placed.values(), default=0)
    if best == 0:
        return None

    winners = [successor for successor, count in placed.items() if count == best]

    return winners[0] if len(winners) == 1 else None


def names_no_unit(name: str) -> bool:
    """
    Whether a written place can never name an administrative unit.

    A compass point standing in for the whole country, a position between two other places, a sea
    or a river, and a string with no letters in it are all beyond any gazetteer. Counting them as
    coverage failures understates what the resolver reaches, so they are told apart.

    Parameters
    ----------
    name : str
        The place as written.

    Returns
    -------
    bool
        True where no administrative unit could answer to this name.
    """
    written = name.strip()

    return bool(
        NOTHING_LEGIBLE.match(written)
        or QUALIFIER.match(written)
        or RELATIONAL.match(written)
        or FEATURE.search(written)
    )
