import json
import sys

from collections import defaultdict
from pathlib import Path

import pandas as pd

from climate_risk.config.registry import load_place, resolve_isos
from climate_risk.data.geo_disasters import load_event_footprints, resolve_to_gadm
from climate_risk.data_functions.emdat_processing import load_emdat_events

CACHE_DIR = Path(__file__).parents[1] / "data"
DEFAULT_PLACE = "sea"


def read_pinned_migration(cache_dir: Path) -> dict[tuple[int, int], tuple[frozenset[str], str]]:
    """
    Recover EM-DAT's own GAUL-to-GADM migration for the units the workbook pins unambiguously.

    EM-DAT publishes the two codings as separate lists with nothing linking a pair, so a
    correspondence is only recoverable where an event names exactly one GAUL unit: every GADM unit
    it names then belongs to that one, however many there are.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.

    Returns
    -------
    dict mapping tuple to tuple
        Keyed on GAUL code and administrative level, holding the GADM identifiers EM-DAT migrated
        that unit to and the migration methods it used.
    """
    events = load_emdat_events(cache_dir)
    pinned: dict[tuple[int, int], set[tuple[frozenset[str], str]]] = defaultdict(set)

    for gaul_raw, gadm_raw in zip(events["Admin Units"], events["GADM Admin Units"], strict=True):
        if not str(gaul_raw or "").strip() or not str(gadm_raw or "").strip():
            continue
        gaul, gadm = json.loads(gaul_raw), json.loads(gadm_raw)
        if len(gaul) != 1:
            continue

        for level in (1, 2):
            if f"adm{level}_code" not in gaul[0]:
                continue
            at_level = [unit for unit in gadm if f"gid_{level}" in unit and (level == 2 or "gid_2" not in unit)]
            if not at_level:
                continue
            named = frozenset(unit[f"gid_{level}"] for unit in at_level)
            methods = "+".join(sorted({str(unit.get("migration_method")) for unit in at_level}))
            pinned[(int(gaul[0][f"adm{level}_code"]), level)].add((named, methods))

    return {key: next(iter(answers)) for key, answers in pinned.items() if len({gids for gids, _ in answers}) == 1}


def countries_with_pinned_units(expected: dict[tuple[int, int], tuple[frozenset[str], str]]) -> tuple[str, ...]:
    """Every country EM-DAT pins at least one migrated unit in, read off the GADM identifiers."""
    return tuple(sorted({next(iter(gids))[:3] for gids, _ in expected.values()}))


def place_pinned_units(
    cache_dir: Path, isos: tuple[str, ...], wanted: set[tuple[int, int]]
) -> dict[tuple[int, int], set[str]]:
    """
    Place each pinned GAUL unit's footprint with the rule the library uses today.

    :func:`resolve_to_gadm` groups footprints on ``DisNo.``; each group here is one GAUL unit rather
    than one event, so the comparison is against a unit-level answer.

    Parameters
    ----------
    cache_dir : Path
        Directory the caches live under.
    isos : tuple of str
        Countries to read.
    wanted : set of tuple
        GAUL code and administrative level of every unit to place.

    Returns
    -------
    dict mapping tuple to set of str
        The GADM identifiers placed for each GAUL unit that had a footprint.
    """
    placed: dict[tuple[int, int], set[str]] = {}

    for position, iso in enumerate(isos, start=1):
        print(f"  [{position}/{len(isos)}] {iso}", file=sys.stderr, flush=True)
        footprints = load_event_footprints(cache_dir, iso=iso)
        codes = [
            int(adm2) if level == 2 and adm2 is not None else (int(adm1) if adm1 is not None else -1)
            for adm1, adm2, level in zip(
                footprints["ADM1_CODE"], footprints["ADM2_CODE"], footprints["admin_level"], strict=True
            )
        ]
        footprints = footprints.assign(gaul_code=codes)

        for level in (1, 2):
            at_level = footprints[
                (footprints["admin_level"] == level)
                & (footprints["gaul_code"].isin({code for code, at in wanted if at == level}))
            ]
            if at_level.empty:
                continue

            resolved = resolve_to_gadm(at_level.assign(**{"DisNo.": at_level["gaul_code"].astype(str)}), cache_dir)
            for code, gids in resolved.groupby("DisNo.")["gid"]:
                placed[(int(str(code)), level)] = set(gids)

    return placed


def compare(
    expected: dict[tuple[int, int], tuple[frozenset[str], str]], placed: dict[tuple[int, int], set[str]]
) -> pd.DataFrame:
    """
    Score the placement of every pinned unit that had a footprint.

    Parameters
    ----------
    expected : dict mapping tuple to tuple
        EM-DAT's own answer, as :func:`read_pinned_migration` returns it.
    placed : dict mapping tuple to set of str
        The library's answer, as :func:`place_pinned_units` returns it.

    Returns
    -------
    DataFrame
        One row per unit, with its GAUL code, level, EM-DAT migration method, the unit counts each
        side named, and whether the two agree.
    """
    return pd.DataFrame(
        [
            {
                "gaul": code,
                "level": level,
                "method": methods,
                "em_dat": len(gids),
                "placed": len(placed[(code, level)]),
                "agrees": placed[(code, level)] == set(gids),
            }
            for (code, level), (gids, methods) in expected.items()
            if (code, level) in placed
        ]
    )


def main() -> int:
    place = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PLACE
    expected = read_pinned_migration(CACHE_DIR)
    isos = countries_with_pinned_units(expected) if place == "all" else resolve_isos(load_place(place))
    scored = compare(expected, place_pinned_units(CACHE_DIR, isos, set(expected)))

    print(f"EM-DAT pins {len(expected)} GAUL units across the whole workbook.")
    print(f"{place}: {len(isos)} countries, {len(scored)} of those units with a footprint to place")
    if scored.empty:
        print("nothing to compare — the archives may be absent, or this place has no geocoded footprints")
        return 1

    print(f"agreement: {scored['agrees'].sum()}/{len(scored)} ({scored['agrees'].mean():.1%})\n")
    by_method = (
        scored.groupby("method")
        .agg(matched=("agrees", "sum"), units=("agrees", "count"), share=("agrees", "mean"))
        .sort_values("units", ascending=False)
    )
    print("by the migration method EM-DAT used, which the units partition between:")
    print(by_method.to_string(formatters={"share": "{:.0%}".format}))

    disagreements = scored[~scored["agrees"]].drop(columns="agrees")
    if not disagreements.empty:
        print(f"\n{len(disagreements)} disagreements:")
        print(disagreements.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
