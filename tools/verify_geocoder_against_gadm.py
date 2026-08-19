import sys

from collections import Counter
from pathlib import Path

from climate_risk.data.geocoding import score_geocoder, unambiguous_units
from climate_risk.data.geonames import geonames_geocoder
from climate_risk.data.place_names import read_gazetteer
from climate_risk.data_functions.emdat_processing import events_missing_units, load_emdat_events

CACHE_DIR = Path(__file__).parents[1] / "data"

# Candidate sources, each building a geocoder for one country.
GEOCODERS = {"geonames": geonames_geocoder}


def places_needing_geography(cache_dir: Path) -> dict[str, list[tuple[str, str | None]]]:
    """
    Collect the places every event EM-DAT left uncoded names, keyed by country.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    dict mapping str to list of tuple
        Each a name as written and the container the prose gave, or None.
    """
    by_country: dict[str, list[tuple[str, str | None]]] = {}
    for event in events_missing_units(load_emdat_events(cache_dir)):
        by_country.setdefault(event.iso, []).extend((place.name, place.parent) for place in event.places)

    return by_country


def report_answer_key(cache_dir: Path) -> None:
    """Report how many written names already resolve to one unit, which is what a score is built on."""
    totals: Counter[str] = Counter()
    per_country: Counter[str] = Counter()

    for iso, places in places_needing_geography(cache_dir).items():
        gazetteer = read_gazetteer(iso, cache_dir)
        if not gazetteer.names:
            continue
        settled = unambiguous_units(places, gazetteer)
        totals["names"] += len({name for name, _ in places})
        totals["with an answer"] += len(settled)
        per_country[iso] = len(settled)

    print(f"{totals['with an answer']} of {totals['names']} distinct written names resolve to exactly one unit")
    print(f"{sum(1 for count in per_country.values() if count >= 30)} countries carry at least 30\n")
    print(f"{'iso':<5}{'answer key':>12}")
    for iso, count in per_country.most_common(15):
        print(f"{iso:<5}{count:>12}")


def report_score(name: str, cache_dir: Path) -> None:
    """Score one registered geocoder against every country's answer key."""
    outcomes: Counter[str] = Counter()

    for iso, places in places_needing_geography(cache_dir).items():
        gazetteer = read_gazetteer(iso, cache_dir)
        if not gazetteer.names:
            continue
        geocode = GEOCODERS[name](iso, cache_dir)
        for scored in score_geocoder(geocode, iso, places, gazetteer, cache_dir):
            outcomes[scored.outcome] += 1

    judged = sum(outcomes.values())
    print(f"{name}: {judged} names judged")
    for outcome, count in outcomes.most_common():
        print(f"  {count:>7}  {count / judged:>5.1%}  {outcome}")


if __name__ == "__main__":
    requested = sys.argv[1] if len(sys.argv) > 1 else None
    if requested is None:
        report_answer_key(CACHE_DIR)
    elif requested in GEOCODERS:
        report_score(requested, CACHE_DIR)
    else:
        print(f"no geocoder named {requested!r} is registered; known: {sorted(GEOCODERS) or 'none yet'}")
        raise SystemExit(1)
