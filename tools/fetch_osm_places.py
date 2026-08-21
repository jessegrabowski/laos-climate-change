import logging
import sys

from collections import defaultdict
from pathlib import Path

import requests

from climate_risk.data.geocoding import units_containing_points, units_from_geocoders
from climate_risk.data.geonames import read_country_codes
from climate_risk.data.osm import (
    PLACE_CATEGORIES,
    RATE_LIMIT_SECONDS,
    NominatimAnswer,
    osm_geocoder,
    read_osm_places,
    record_lookups,
    search_nominatim,
)
from climate_risk.data.place_names import NAMED, read_gazetteer, resolve_event_places
from climate_risk.data.placement import available_geocoders
from climate_risk.data_functions.emdat_processing import events_missing_units, load_emdat_events
from climate_risk.exceptions import UpstreamUnavailableError

_log = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parents[1] / "data"

# Written often enough to be worth a request, and no more than Nominatim should be asked in one go.
MOST_NAMES_PER_RUN = 4000

# A failed request is usually one bad name and sometimes a block. Enough failures in a row mean
# the second, and carrying on would cache thousands of absences that were never asked about.
MOST_FAILURES_IN_A_ROW = 5


def places_still_unplaced(cache_dir: Path) -> dict[str, set[str]]:
    """
    Collect the written places the resolver still reaches no unit for, keyed by country.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    dict mapping str to set of str
        The distinct names left unplaced in each country.
    """
    by_country: dict[str, list] = defaultdict(list)
    for event in events_missing_units(load_emdat_events(cache_dir)):
        by_country[event.iso].append(event)

    unplaced: dict[str, set[str]] = defaultdict(set)
    for iso, events in sorted(by_country.items()):
        gazetteer = read_gazetteer(iso, cache_dir)
        if not gazetteer.names:
            continue
        wanted = {place.name for event in events for place in event.places}
        located = units_from_geocoders(wanted, iso, cache_dir, available_geocoders(iso, cache_dir))

        for event in events:
            placed = resolve_event_places([(p.name, p.parent) for p in event.places], gazetteer, located=located)
            for place, placement in zip(event.places, placed, strict=True):
                if not placement.gids and placement.how == NAMED:
                    unplaced[iso].add(place.name)

    return unplaced


def crawl(cache_dir: Path, wanted: list[str] | None = None) -> None:
    """
    Ask Nominatim about every unplaced name not already asked about, and cache what it says.

    A name is asked about once, ever. Misses are cached alongside hits, so a second run costs a
    request only for names the workbook has gained since the first.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.
    wanted : list of str, optional
        ISO 3166-1 alpha-3 codes to crawl. Default None, which crawls every country with unplaced
        names.
    """
    unplaced = places_still_unplaced(cache_dir)
    countries = [iso for iso in sorted(unplaced) if not wanted or iso in wanted]
    alpha2 = read_country_codes(cache_dir)

    outstanding = {
        iso: sorted(unplaced[iso] - set(read_osm_places(iso, cache_dir)["written"].to_list())) for iso in countries
    }
    total = sum(len(names) for names in outstanding.values())
    if total > MOST_NAMES_PER_RUN:
        print(f"{total} names outstanding, which is more than {MOST_NAMES_PER_RUN} to ask in one run.")
        print("Name the countries to crawl, worst first — see tools/survey_unplaced_places.py.")
        return

    print(
        f"{total} names to ask about across {len(countries)} countries, {total * RATE_LIMIT_SECONDS / 60:.0f} minutes"
    )
    with requests.Session() as session:
        for iso in countries:
            names = outstanding[iso]
            if not names:
                continue
            answers = ask_about(names, alpha2.get(iso), session)
            record_lookups(iso, cache_dir, answers)
            usable = sum(1 for answer in answers.values() if answer and answer.category in PLACE_CATEGORIES)
            print(
                f"  {iso}  asked {len(answers):4d}, {sum(answer is not None for answer in answers.values()):4d} found, "
                f"{usable:4d} of them a place or boundary",
                flush=True,
            )
            if len(answers) < len(names):
                print(f"  stopping: Nominatim failed {MOST_FAILURES_IN_A_ROW} times running. Nothing else was asked.")
                return

    report(cache_dir, countries)


def ask_about(names: list[str], alpha2: str | None, session: requests.Session) -> dict[str, NominatimAnswer | None]:
    """
    Ask Nominatim about each name, stopping early if it stops answering at all.

    Parameters
    ----------
    names : list of str
        The places as written.
    alpha2 : str or None
        ISO 3166-1 alpha-2 code to confine the search to.
    session : requests.Session
        Session to make the requests on.

    Returns
    -------
    dict mapping str to NominatimAnswer or None
        What Nominatim said about each name it was asked about. Shorter than ``names`` where the run
        stopped early, so the names it never reached stay unasked rather than cached as missing.
    """
    answers: dict[str, NominatimAnswer | None] = {}
    failures = 0
    for name in names:
        try:
            answers[name] = search_nominatim(name, alpha2, session=session)
        except UpstreamUnavailableError as unreachable:
            _log.warning(unreachable)
            failures += 1
            if failures >= MOST_FAILURES_IN_A_ROW:
                break
            continue
        failures = 0

    return answers


def report(cache_dir: Path, countries: list[str]) -> None:
    """
    Say how many unplaced names the cached answers would now place, country by country.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.
    countries : list of str
        ISO 3166-1 alpha-3 codes to report on.
    """
    unplaced = places_still_unplaced(cache_dir)
    asked = placeable = 0
    for iso in countries:
        locate = osm_geocoder(iso, cache_dir)
        points = {name: xy for name in unplaced.get(iso, ()) if (xy := locate(iso, name)) is not None}
        inside = units_containing_points(points, iso, cache_dir) if points else {}
        asked += len(unplaced.get(iso, ()))
        placeable += len(inside)
        if points:
            print(f"  {iso}  {len(inside):4d} of {len(unplaced.get(iso, ())):4d} unplaced names now reach a unit")

    if asked:
        print(
            f"\n{placeable} of {asked} unplaced names reach a GADM unit through OpenStreetMap ({placeable / asked:.1%})"
        )


if __name__ == "__main__":
    crawl(CACHE_DIR, [code.upper() for code in sys.argv[1:]] or None)
