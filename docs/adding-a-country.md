# Adding a country

A country is one TOML file in `climate_risk/config/places/`, named after its ISO 3166-1 alpha-3
code in lower case. Zambia needs two lines:

```toml
iso3 = "ZMB"
name = "Zambia"
```

That is the whole minimum. The geometry comes from slicing the World Bank world shapefile by
`iso3`, and everything else falls back to the project-wide defaults in `climate_risk/config/schema.py`.

Nothing else has to change. If you find yourself editing a loader to make a country work, the
loader is wrong, not the config.

## What you get without asking

The directory is walked, so a new file is picked up with no registration step. Its ISO codes are
checked against the World Bank country table, and the file has to parse and match the schema —
a typo in a key is an error, not a silently ignored default.

Downstream, `load_place("zmb")` gives you a `CountryConfig` that the loaders accept directly:

```python
from climate_risk.config.registry import load_place
from climate_risk.data_functions.disaster_point_data import load_grid_point_data

grid = load_grid_point_data(cache_dir, load_place("zmb"))
```

## What you can override

Every block below is optional.

**`[geometry]`** — `grid_size` (points per side before land clipping, default 400), and the
geographic and projected CRS.

**`[events]`** — `start_year`, `end_year`, `min_total_affected`, `min_deaths`. The defaults describe
the window the published panel uses. Lower them for a country with few recorded disasters, but
check first: all three shipped countries clear the defaults comfortably, and an empty event frame
is easy to mistake for a working pipeline.

**`[boundary]`** — a country-specific admin boundary archive, when the world shapefile is too coarse.
It needs `member` naming the layer to read inside the zip, alongside the usual source fields:

```toml
[boundary]
member = "lao_admin2.shp"
url = "https://…/lao_admin_boundaries.shp.zip"
filename = "lao_admin_boundaries.shp.zip"
licence = "CC BY 3.0 IGO"
citation = "National Geographic Department (NGD), via the Humanitarian Data Exchange."
retrieved = "2026-08-08"
```

A boundary declared here is fetched, cached and reachability-checked exactly like a source declared
in code. `licence` and `citation` are not decorative — fill them in from the publisher's own page.

**`[event_location_overrides]`** — longitude and latitude forced onto EM-DAT records whose published
position is wrong, keyed by event id. Two countries may not both claim the same event.

**`random_seed`** — seeds the synthetic non-disaster sampling. Change it only to draw a different
sample deliberately; two countries sharing a seed is fine, since they sample different geometry.

## What is still global

Three things do not yet vary by country, and will surprise you if you assume they do.

The **EM-DAT event frame** is filtered by severity and window, not by country. `[events]` narrows
which events count everywhere, not which country's events you get.

The **river-damage frames** cover every country at once. `create_floods_rivers_damage` returns
world-wide flood events; the coordinate overrides are applied across all of them, which works
because event ids are country-specific.

The **point grid carries no country label**. Every point in it lies inside the place you asked for,
but there is no `ISO` column until `load_non_disaster_grid` adds one.

## Before you trust it

The end-to-end tests run against synthetic fixtures, which are uniform in ways real countries are
not — a landlocked and a coastal country are represented, and the paths are asserted to differ, but
that is a weaker claim than a real run.

The one test that uses real data is marked `requires_emdat` and skips wherever the licensed
workbook is absent, which includes CI. Run it once on a machine that has the workbook:

```
pixi run pytest -m requires_emdat
```

It checks that your country actually has events clearing its own filters. A country that does not
produces an empty panel, and every other test will pass on it.
