import re
import sys

from collections import Counter, defaultdict
from pathlib import Path

from climate_risk.data.geocoding import units_from_geocoders
from climate_risk.data.place_names import (
    CONJUNCTION,
    DASH,
    FEATURE,
    MIN_APPROXIMATE_LENGTH,
    MIN_SPLIT_LENGTH,
    NAMED,
    UNIT_NOUNS,
    Gazetteer,
    match_key,
    read_gazetteer,
    resolve_event_places,
    resolve_place,
)
from climate_risk.data.placement import available_geocoders
from climate_risk.data_functions.emdat_processing import events_missing_units, load_emdat_events

CACHE_DIR = Path(__file__).parents[1] / "data"

# How far a written name is allowed to stray before the search stops calling it the same name.
EDIT_BUDGET = 2

# Longer than any single published name in GADM, so a mention this long is several run together.
LONGEST_SINGLE_NAME = 24

# Shorter than this, capitalisation says nothing: plenty of real names are three letters.
SHORTEST_SHOUTED_NAME = 3

MOJIBAKE = re.compile(r"[ÃÂ]")
ABBREVIATION = re.compile(r"\b(?:st|ste|sta|mt|ft|isl|is|no|dept)\b\.?", re.IGNORECASE)
ADJECTIVAL = re.compile(r"(?:ski|cki|zki|sky|ien|ais|ese|ien)$", re.IGNORECASE)
PARENTHETICAL = re.compile(r"[(\[]")
POSSESSIVE = re.compile(r"\w's\b", re.IGNORECASE)
SENTENCE = re.compile(r"\b(?:of|the|de|du|des|la|le|el|in|on|at)\b", re.IGNORECASE)


def edits_away(written: str, published: str, budget: int) -> int | None:
    """
    Count the edits turning one key into another, or None where it takes more than the budget.

    Parameters
    ----------
    written : str
        The key the mention reduces to.
    published : str
        The key a GADM name reduces to.
    budget : int
        The most edits worth counting.

    Returns
    -------
    int or None
        The distance, or None where it exceeds the budget.
    """
    if abs(len(written) - len(published)) > budget:
        return None

    previous = list(range(len(published) + 1))
    for position, letter in enumerate(written, start=1):
        current = [position]
        for other, published_letter in enumerate(published, start=1):
            current.append(
                min(previous[other] + 1, current[other - 1] + 1, previous[other - 1] + (letter != published_letter))
            )
        if min(current) > budget:
            return None
        previous = current

    return previous[-1] if previous[-1] <= budget else None


def signatures(name: str, parent: str | None, gazetteer: Gazetteer) -> set[str]:
    """
    Name every mechanically detectable property of a written place that a repair could act on.

    A property is listed whether or not anything acts on it yet, because the point of the survey is
    to show what the residual is made of rather than to confirm what is already handled. A name
    carrying none of them is what the next rule has to be found in.

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
        The properties the name carries.
    """
    found: set[str] = set()
    key = match_key(name)

    if MOJIBAKE.search(name):
        found.add("mis-decoded characters")
    if name.isupper() and len(name) > SHORTEST_SHOUTED_NAME:
        found.add("written in capitals")
    if any(character.isdigit() for character in name):
        found.add("carries a digit")
    if PARENTHETICAL.search(name):
        found.add("carries a parenthetical")
    if POSSESSIVE.search(name):
        found.add("carries a possessive")
    if ABBREVIATION.search(name):
        found.add("carries an abbreviation")
    if UNIT_NOUNS.search(name):
        found.add("carries a unit noun")
    if FEATURE.search(name):
        found.add("names a physical feature")
    if ADJECTIVAL.search(key):
        found.add("ends in an adjectival suffix")
    if len(SENTENCE.findall(name)) >= 2:
        found.add("reads as a phrase rather than a name")
    if len(key) < MIN_APPROXIMATE_LENGTH:
        found.add("too short to correct")
    if len(key) > LONGEST_SINGLE_NAME:
        found.add("long enough to be several names run together")

    parts = [part.strip() for part in DASH.split(name) if part.strip()]
    if len(parts) > 1:
        if any(len(match_key(part)) < MIN_SPLIT_LENGTH for part in parts):
            found.add("dashed, and a part is too short to be a place")
        else:
            reached = [bool(resolve_place(part, parent, gazetteer)) for part in parts]
            if not any(reached):
                found.add("dashed, and no part names a unit")
            elif not all(reached):
                found.add("dashed, and only some parts name a unit")

    if CONJUNCTION.search(name):
        joined = [part.strip() for part in CONJUNCTION.split(name) if part.strip()]
        if not any(resolve_place(part, parent, gazetteer) for part in joined):
            found.add("joined by a conjunction, and no part names a unit")

    if parent:
        found.add(
            "has a container that reaches a unit"
            if resolve_place(parent, None, gazetteer)
            else "has a container that reaches nothing"
        )
    else:
        found.add("has no container")

    return found


def survey(cache_dir: Path, only: str | None = None) -> None:
    """
    Partition every unplaced place by what it is made of, and by how far it sits from a published name.

    Countries are ranked by the share of their rows left unplaced rather than by the count. A count
    ranking follows how many events a country has, so it puts the countries the resolver already
    handles at the top and buries the ones with a cause of their own.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.
    only : str, optional
        ISO 3166-1 alpha-3 code to list every distinct unplaced name for, instead of surveying every
        country. Default None, which surveys all of them.
    """
    by_country: dict[str, list] = defaultdict(list)
    for event in events_missing_units(load_emdat_events(cache_dir)):
        by_country[event.iso].append(event)
    if only:
        by_country = {only: by_country.get(only, [])}

    carried: Counter[str] = Counter()
    unplaced_per_country: Counter[str] = Counter()
    rows_per_country: Counter[str] = Counter()
    distances: Counter[str] = Counter()
    repeated: Counter[tuple[str, str]] = Counter()
    unsignatured: list[tuple[str, str, str | None]] = []
    rows = 0

    for position, (iso, events) in enumerate(sorted(by_country.items()), start=1):
        gazetteer = read_gazetteer(iso, cache_dir)
        if not gazetteer.names:
            continue
        wanted = {place.name for event in events for place in event.places}
        located = units_from_geocoders(wanted, iso, cache_dir, available_geocoders(iso, cache_dir))

        for event in events:
            placed = resolve_event_places([(p.name, p.parent) for p in event.places], gazetteer, located=located)
            for place, placement in zip(event.places, placed, strict=True):
                rows_per_country[iso] += 1
                if placement.gids or placement.how != NAMED:
                    continue
                rows += 1
                unplaced_per_country[iso] += 1
                repeated[(iso, place.name)] += 1
                carrying = signatures(place.name, place.parent, gazetteer)
                carried.update(carrying)
                if not (
                    carrying
                    - {
                        "has no container",
                        "has a container that reaches a unit",
                        "has a container that reaches nothing",
                    }
                ):
                    unsignatured.append((iso, place.name, place.parent))

                key = match_key(place.name)
                near = {
                    distance
                    for published in gazetteer.names
                    if (distance := edits_away(key, published, EDIT_BUDGET)) is not None
                }
                distances[
                    f"{min(near)} edits from a published name" if near else "no published name within two edits"
                ] += 1

        if position % 40 == 0:
            print(f"  ... {position}/{len(by_country)} countries", flush=True)

    if only:
        print(f"\n{rows} of {rows_per_country[only]} {only} rows unplaced, {len(repeated)} distinct names:\n")
        for (_, name), count in sorted(repeated.items(), key=lambda item: item[0][1]):
            print(f"  x{count}  {name!r}")
        return

    distinct = len(repeated)
    print(f"\n{rows} unplaced rows, {distinct} distinct names, {rows / distinct:.2f} rows per name\n")

    print("how far each sits from the nearest published name:")
    for label, count in distances.most_common():
        print(f"  {count:6d}  {count / rows:5.1%}  {label}")

    print("\nwhat the names are made of, one row counted under every property it carries:")
    for label, count in carried.most_common():
        print(f"  {count:6d}  {count / rows:5.1%}  {label}")

    print(f"\n{len(unsignatured)} rows carry no property at all, which is where the next rule has to be found:")
    for iso, name, parent in unsignatured[:40]:
        print(f"    {iso}  {name!r}   container: {parent!r}")

    print("\nwhere a country-wide cause is most likely, by the share of its rows left unplaced:")
    print("  (countries with fewer than 20 unplaced rows are left out, being too small to read)")
    running = 0
    worst = sorted(
        unplaced_per_country, key=lambda iso: unplaced_per_country[iso] / rows_per_country[iso], reverse=True
    )
    for iso in [iso for iso in worst if unplaced_per_country[iso] >= 20][:25]:
        count = unplaced_per_country[iso]
        running += count
        share = count / rows_per_country[iso]
        print(f"  {iso}  {count:5d} of {rows_per_country[iso]:6d} rows  {share:5.1%} unplaced   {running / rows:5.1%}")
    holding_half = 0
    running = 0
    for _, count in unplaced_per_country.most_common():
        running += count
        holding_half += 1
        if running >= rows // 2:
            break
    print(f"\n  {holding_half} of {len(unplaced_per_country)} countries hold half the residual")

    print("\nthe names that would repay a fix most, by how many rows carry them:")
    for (iso, name), count in repeated.most_common(30):
        print(f"  {count:4d}  {iso}  {name!r}")


if __name__ == "__main__":
    requested = sys.argv[1].upper() if len(sys.argv) > 1 else None
    survey(CACHE_DIR, requested)
