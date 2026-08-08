import re

from dataclasses import replace

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import Point

from climate_risk import load_synthetic_non_disaster_points
from climate_risk.config.registry import load_place
from climate_risk.config.schema import CountryConfig, GeometrySpec
from climate_risk.data_functions.disaster_point_data import (
    _load_disaster_point_data,
    load_data,
    load_grid_point_data,
    load_non_disaster_grid,
)
from climate_risk.geo.crs import GEOGRAPHIC_CRS
from tests.conftest import SYNTHETIC_SOURCE_EVENTS, toy_world_needing_repair, toy_world_with_places

# Every shipped country, with the longitudes `toy_world_with_places` puts it between. Stated
# here rather than read from the fixture, so a country sliced out of the wrong box fails.
COUNTRY_BOUNDS = [("lao", 20.0, 21.0), ("zmb", 23.0, 24.0), ("cri", 29.5, 30.5)]

EARTH_CIRCUMFERENCE_KM = 40_075

# A legacy cache spells longitude `long`; the value under `lon` is the one to keep.
STALE_LON = 9.9
CURRENT_LON = 102.5


def france(grid_size=3):
    """The one country of the toy world the grid fixtures put rivers and coastline near."""
    return CountryConfig(iso3="FRA", name="France", geometry=GeometrySpec(grid_size=grid_size))


def test_missing_geocoded_locations_names_the_file_it_looked_for(tmp_path):
    """The message is the only guidance a fresh clone gets, so it has to say which file is absent."""
    with pytest.raises(ValueError, match=re.escape("disaster_locations_gpt_repaired_w_features.csv")):
        _load_disaster_point_data(tmp_path)


def test_unknown_sampling_strategy_is_rejected(tmp_path):
    """An unknown `by` once fell through both branches and failed on an unbound name."""
    with pytest.raises(ValueError, match="by should be one of"):
        load_synthetic_non_disaster_points(tmp_path, france(), by="continent")


@pytest.fixture
def grid(write_point_grid_cache):
    cache_dir = write_point_grid_cache()
    return load_grid_point_data(cache_dir, france())


def test_grid_columns_use_lon_not_long(grid):
    """`lon` is the project's spelling, and the saved grid is what downstream reads back."""
    assert "lon" in grid.columns
    assert "long" not in grid.columns


def test_grid_carries_its_distance_features(grid):
    assert {"distance_to_river", "distance_to_coastline", "is_island"} <= set(grid.columns)
    assert (grid["distance_to_river"] > 0).all()


@pytest.mark.parametrize("column", ["distance_to_river", "distance_to_coastline"])
def test_grid_distances_are_in_kilometres(grid, column):
    """Two other loaders write these same column names in kilometres, and the frames get merged.

    Bounded by the circumference rather than by a value read off the fixture, so the assertion says
    what it means: no distance on Earth is larger, and the same figure in metres would be.
    """
    assert grid[column].max() < EARTH_CIRCUMFERENCE_KM


def test_zero_distances_do_not_become_infinite_logs(write_point_grid_cache, rivers_through_the_grid):
    """The grid is written to disk, so a -inf from log(0) persists into every later run."""
    cache_dir = write_point_grid_cache(rivers_through_the_grid)

    grid = load_grid_point_data(cache_dir, france())

    on_a_river = grid[grid["distance_to_river"] == 0]

    assert len(on_a_river) > 0
    assert np.isfinite(grid[["log_distance_to_river", "log_distance_to_coastline"]]).all().all()
    # The floor is one metre, which is 0.001 in the kilometres the column reports.
    assert on_a_river["log_distance_to_river"].eq(np.log(0.001)).all()

    clear_of_a_river = grid[grid["distance_to_river"] > 0]

    assert len(clear_of_a_river) > 0
    assert clear_of_a_river["log_distance_to_river"].eq(np.log(clear_of_a_river["distance_to_river"])).all()


def test_a_different_grid_size_is_a_different_cache_entry(write_point_grid_cache):
    """Two resolutions sharing one entry would serve whichever run happened first."""
    cache_dir = write_point_grid_cache()

    coarse = load_grid_point_data(cache_dir, france(grid_size=3))
    fine = load_grid_point_data(cache_dir, france(grid_size=6))

    assert len(fine) > len(coarse)


def test_two_places_do_not_share_a_cache_entry(write_point_grid_cache):
    """One entry for both would serve whichever place happened to be gridded first."""
    cache_dir = write_point_grid_cache()
    netherlands = CountryConfig(iso3="NLD", name="Netherlands", geometry=GeometrySpec(grid_size=3))

    french = load_grid_point_data(cache_dir, france())
    dutch = load_grid_point_data(cache_dir, netherlands)

    assert french["lon"].max() < dutch["lon"].min()


def test_the_cached_grid_round_trips_unchanged(write_point_grid_cache):
    """The grid is written once and read on every later run, so the two must be the same frame."""
    cache_dir = write_point_grid_cache()

    written = load_grid_point_data(cache_dir, france())
    reloaded = load_grid_point_data(cache_dir, france())

    assert_geodataframe_equal(reloaded, written)
    assert {"distance_to_river", "log_distance_to_river", "log_distance_to_coastline"} <= set(reloaded.columns)


def test_a_cache_may_spell_longitude_long(tmp_path):
    """A cache on disk may spell longitude `long`."""
    legacy = tmp_path / "points.csv"
    legacy.write_text(f"emdat_index,location_id,long,lat\n0,0,{CURRENT_LON},18.5\n")

    data = load_data(legacy)

    assert "lon" in data.columns
    assert "long" not in data.columns
    assert data.geometry.x.tolist() == [CURRENT_LON]


def test_a_cache_holding_both_spellings_keeps_one_lon(tmp_path):
    """Renaming unconditionally would give two columns named lon, and attribute lookup a frame."""
    half_migrated = tmp_path / "points.csv"
    half_migrated.write_text(f"emdat_index,location_id,long,lon,lat\n0,0,{STALE_LON},{CURRENT_LON},18.5\n")

    data = load_data(half_migrated)

    assert list(data.columns).count("lon") == 1
    assert data.geometry.x.tolist() == [CURRENT_LON]
    assert STALE_LON not in data.geometry.x.tolist()


def test_a_warm_synthetic_cache_is_reused(tmp_path):
    """The old key never matched the name it wrote, so synthetics were regenerated on every run.

    Nothing here seeds the inputs a build needs, so a key that misses reaches for the network and
    the socket guard fails the test.
    """
    # Stated literally, so a changed key fails rather than agreeing with the loader.
    cache = tmp_path / "synthetic_non_disasters__by=region__list_name=lao__times=1.parquet"
    gpd.GeoDataFrame(
        {"ISO": ["LAO"], "Start_Year": [pd.Timestamp("1990-01-01")], "geometry": [Point(102.5, 18.5)]},
        crs=GEOGRAPHIC_CRS,
    ).to_parquet(cache)

    points = load_synthetic_non_disaster_points(tmp_path, CountryConfig(iso3="LAO", name="Lao PDR"))

    assert points["ISO"].tolist() == ["LAO"]


def test_a_warm_non_disaster_grid_is_reused(tmp_path):
    """As above: the grid name has to reach the cache key, or every call rebuilds."""
    cache = tmp_path / "non_disaster_grid__grid=laos.parquet"
    gpd.GeoDataFrame(
        {"ISO": ["LAO"], "is_disaster": [0], "geometry": [Point(102.5, 18.5)]}, crs=GEOGRAPHIC_CRS
    ).to_parquet(cache)

    grid = load_non_disaster_grid(tmp_path, grid=None, grid_name="laos")

    assert grid["ISO"].tolist() == ["LAO"]


def test_a_cold_non_disaster_grid_labels_each_point_with_its_country(write_shapefile_cache):
    """The spatial join is the only thing assigning ISO, and a point can silently land in no country.

    France and the Netherlands sit at opposite ends of the toy world, so a join that matched by row
    order rather than geometry would swap them.
    """
    cache_dir = write_shapefile_cache("world", toy_world_needing_repair())
    # The last point is open ocean: a control there is unlabelled, not discarded.
    points = gpd.GeoDataFrame(geometry=[Point(12.25, 0.5), Point(0.25, 0.5), Point(50.0, 50.0)], crs=GEOGRAPHIC_CRS)

    grid = load_non_disaster_grid(cache_dir, points, "toy")

    assert grid["ISO"].tolist()[:2] == ["NLD", "FRA"]
    assert pd.isna(grid["ISO"].tolist()[2])
    assert grid["is_disaster"].tolist() == [0, 0, 0]
    # The literal date, not CONTROL_YEAR, which would move with the code it is checking.
    assert set(grid["Start_Year"]) == {pd.Timestamp("1984-01-01")}


@pytest.mark.parametrize("by", ["region", "country"])
def test_the_sampled_years_come_from_the_generator_the_caller_passed(write_synthetic_source_cache, by):
    """Every other draw honours `rng`, so a caller seeding it gets reproducibility for all but this one."""
    cache_dir = write_synthetic_source_cache()
    first = load_synthetic_non_disaster_points(cache_dir, france(), rng=np.random.default_rng(0), by=by)
    second = load_synthetic_non_disaster_points(
        cache_dir, france(), rng=np.random.default_rng(0), force_generate=True, by=by
    )

    # Without these the comparison holds vacuously when the country filter matches nothing.
    assert len(first) == SYNTHETIC_SOURCE_EVENTS
    assert first["Start_Year"].nunique() > 1
    # The whole frame, so the sampled locations are covered as well as the years.
    assert_geodataframe_equal(first, second)


def test_a_place_reproduces_its_own_sample_without_being_handed_a_generator(write_synthetic_source_cache):
    """`random_seed` is the place's, so a run with no `rng` still has to repeat exactly."""
    cache_dir = write_synthetic_source_cache()

    first = load_synthetic_non_disaster_points(cache_dir, france())
    second = load_synthetic_non_disaster_points(cache_dir, france(), force_generate=True)

    assert len(first) == SYNTHETIC_SOURCE_EVENTS
    assert_geodataframe_equal(first, second)


def test_two_places_seeded_differently_draw_differently(write_synthetic_source_cache):
    """One seed for every place would make the synthetic controls correlated across countries."""
    cache_dir = write_synthetic_source_cache()
    other = CountryConfig(iso3="FRA", name="France", random_seed=1234, geometry=GeometrySpec(grid_size=3))

    default = load_synthetic_non_disaster_points(cache_dir, france())
    reseeded = load_synthetic_non_disaster_points(cache_dir, other, force_generate=True)

    assert not default.geometry.geom_equals(reseeded.geometry).all()


def test_the_multiplier_scales_how_many_points_are_sampled(write_synthetic_source_cache):
    """It sets how many non-disasters stand against each disaster, and it keys the cache entry."""
    cache_dir = write_synthetic_source_cache()
    single = load_synthetic_non_disaster_points(cache_dir, france(), rng=np.random.default_rng(0), multiplier=1)
    tripled = load_synthetic_non_disaster_points(cache_dir, france(), rng=np.random.default_rng(0), multiplier=3)

    assert len(single) == SYNTHETIC_SOURCE_EVENTS
    assert len(tripled) == SYNTHETIC_SOURCE_EVENTS * 3


@pytest.mark.parametrize(("key", "west", "east"), COUNTRY_BOUNDS, ids=[key for key, _, _ in COUNTRY_BOUNDS])
def test_every_shipped_country_grids_from_its_config_alone(write_point_grid_cache, key, west, east):
    """The step's whole claim: a country the loaders have never heard of grids from its config alone.

    The bounds check is what makes it more than a smoke test — a place resolving to the wrong ISO
    still produces a grid, just somewhere else.
    """
    cache_dir = write_point_grid_cache(world=toy_world_with_places())
    place = replace(load_place(key), geometry=GeometrySpec(grid_size=4))

    grid = load_grid_point_data(cache_dir, place)

    assert len(grid) > 0
    assert grid["lon"].between(west, east).all()
    assert grid["lat"].between(0.0, 1.0).all()


def test_the_coastal_country_grids_nearer_the_sea_than_a_landlocked_one(write_point_grid_cache):
    """Landlocked and coastal must take genuinely different paths, not both return nulls."""
    cache_dir = write_point_grid_cache(world=toy_world_with_places())
    coastal = replace(load_place("cri"), geometry=GeometrySpec(grid_size=4))
    landlocked = replace(load_place("zmb"), geometry=GeometrySpec(grid_size=4))

    on_the_coast = load_grid_point_data(cache_dir, coastal)
    inland = load_grid_point_data(cache_dir, landlocked)

    assert on_the_coast["distance_to_coastline"].max() < inland["distance_to_coastline"].min()


def test_a_grid_size_set_in_a_place_file_reaches_the_grid(write_point_grid_cache, tmp_path):
    """Every other test hands the loader a `Place` it built; this one starts from a file on disk.

    Without it the whole config layer could be inert and the suite would not notice.
    """
    cache_dir = write_point_grid_cache(world=toy_world_with_places())

    def zambia_gridded_at(size: int) -> gpd.GeoDataFrame:
        root = tmp_path / str(size)
        (root / "places").mkdir(parents=True)
        (root / "places" / "zmb.toml").write_text(f'iso3 = "ZMB"\nname = "Zambia"\n\n[geometry]\ngrid_size = {size}\n')
        return load_grid_point_data(cache_dir, load_place("zmb", root=root))

    assert len(zambia_gridded_at(9)) > len(zambia_gridded_at(3))
