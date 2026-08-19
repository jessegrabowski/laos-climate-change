import sys

from pathlib import Path

import requests

from climate_risk.data.geonames import load_place_points, read_country_codes
from climate_risk.data_functions.emdat_processing import events_missing_units, load_emdat_events

CACHE_DIR = Path(__file__).parents[1] / "data"


def countries_needing_a_geocoder(cache_dir: Path) -> list[str]:
    """
    Name every country holding an event EM-DAT left without administrative units.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    list of str
        ISO 3166-1 alpha-3 codes, in alphabetical order.
    """
    return sorted({event.iso for event in events_missing_units(load_emdat_events(cache_dir))})


# One host, a couple of hundred requests: a transient timeout is expected, not exceptional.
ATTEMPTS = 3


def _index_country(iso: str, cache_dir: Path) -> int:
    for attempt in range(1, ATTEMPTS):
        try:
            return len(load_place_points(iso, cache_dir))
        except requests.RequestException as failure:
            print(f"  {iso}: {type(failure).__name__}, retrying ({attempt}/{ATTEMPTS})", flush=True)

    return len(load_place_points(iso, cache_dir))


def fetch(isos: list[str], cache_dir: Path) -> int:
    """
    Download and index each country's dump, carrying on past the ones that fail.

    Parameters
    ----------
    isos : list of str
        ISO 3166-1 alpha-3 codes to index.
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    int
        How many countries could not be indexed, which is the process exit status.
    """
    codes = read_country_codes(cache_dir)
    absent, failed, built = [], [], 0

    for position, iso in enumerate(isos, start=1):
        if iso not in codes:
            absent.append(iso)
            continue
        try:
            names = _index_country(iso, cache_dir)
        except (requests.RequestException, OSError, ValueError) as failure:
            failed.append(iso)
            print(f"[{position}/{len(isos)}] {iso}: FAILED, {type(failure).__name__}: {failure}", flush=True)
            continue
        built += 1
        print(f"[{position}/{len(isos)}] {iso} ({codes[iso]}): {names} names", flush=True)

    print(f"\nindexed {built} countries")
    if absent:
        print(f"GeoNames publishes no dump for {len(absent)}: {', '.join(absent)}")
    if failed:
        print(f"{len(failed)} failed and can be retried by running again: {', '.join(failed)}")

    return len(failed)


if __name__ == "__main__":
    requested = [iso.upper() for iso in sys.argv[1:]] or countries_needing_a_geocoder(CACHE_DIR)
    raise SystemExit(fetch(requested, CACHE_DIR))
