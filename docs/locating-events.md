# Locating events

EM-DAT gives most events a country and nothing finer. About 28% carry administrative units it
coded itself; the rest carry a free-text `Location` column, or nothing at all. This is how that
text becomes GADM units, and what to run to reproduce it from a fresh clone.

## The path a location takes

```
"Muang Nakhon Si Thammarat, Hua Sai districts (Nakhon Si Thammarat province)"
        |
        |  named_places        climate_risk/data_functions/emdat_processing.py
        v
[("Muang Nakhon Si Thammarat", "Nakhon Si Thammarat province"), ("Hua Sai districts", ...)]
        |
        |  resolve_place       climate_risk/data/place_names.py
        v
{"THA.40.5_1"}, {"THA.40.3_1"}
```

`named_places` splits on commas and semicolons outside parentheses, and treats a parenthesised
group as the container of every place since the last one. It never splits on `and`: 75 GADM units
are named like `Newfoundland and Labrador`.

`resolve_place` matches a name against every name GADM publishes a unit under, having stripped the
noun saying what kind of unit it is. It resolves ambiguity three ways, in order: a unit contained by
another candidate is dropped, the container from the prose narrows what is left, and
`resolve_event_places` lets the places an event names unambiguously narrow the ones it does not.
Where the whole string reaches nothing and every part of an `and` does, the parts are taken instead.

What is left over goes to a gazetteer of points. `geonames_geocoder` answers with a longitude and
latitude, and the point is placed in whichever GADM unit contains it.

## Getting the data

Two archives are placed by hand, because their terms forbid automated download:

| file | where it goes | obtained from |
|---|---|---|
| `emdat.xlsx` | `data/` | https://public.emdat.be — a free account, non-commercial use |
| `gadm_410.gpkg` | `data/gadm/` | https://gadm.org/download_world.html — non-commercial use |

Everything else downloads itself:

```
pixi run fetch-geonames          # every country EM-DAT names, ~200 dumps
pixi run fetch-geonames PHL IDN  # or just the ones you need
```

Each dump is indexed into `data/geonames/places__iso=XXX.parquet`, one row per distinct name, the
most populous place keeping a name where several share it. Re-running skips whatever is already
there.

## Checking it still works

```
pixi run verify-geocoder             # how many names have a unit to be scored against
pixi run verify-geocoder geonames    # score the geocoder against them
```

The answer key is every written name that already resolves to exactly one GADM unit. A point is
scored as landing in that unit, in the level-1 unit containing it, or somewhere else. Names
reaching more than one unit are excluded — whichever the geocoder picked, the other was available,
so they cannot judge anything.

This is a check, not a test: it needs both hand-placed archives and takes minutes, so it is a
script rather than part of the suite.
