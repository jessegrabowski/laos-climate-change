from typing import Any

import numpy as np
import pytest

from climate_risk import load_synthetic_non_disaster_points
from climate_risk.data_functions.disaster_point_data import (
    load_data,
    load_grid_point_data,
    load_non_disaster_grid,
    make_synthetic_data_fpath,
)

# A legacy cache spells longitude `long`; the value under `lon` is the one to keep.
STALE_LON = 9.9
CURRENT_LON = 102.5


def test_synthetic_filename_is_a_plain_csv(tmp_path):
    fpath = make_synthetic_data_fpath(tmp_path, "region", 1, "sea")

    assert fpath.name == "synthetic_non_disasters_region_times_1_sea.csv"


def test_unknown_sampling_strategy_is_rejected(tmp_path):
    """An unknown `by` once fell through both branches and failed on an unbound name."""
    with pytest.raises(ValueError, match="by should be one of"):
        load_synthetic_non_disaster_points(tmp_path, ["LAO"], "sea", by="continent")


@pytest.fixture
def grid(write_point_grid_cache):
    cache_dir = write_point_grid_cache()
    return load_grid_point_data(cache_dir, region="custom", iso_list=["FRA"], file_reg_name="toy", grid_size=3)


def test_grid_columns_use_lon_not_long(grid):
    """`lon` is the project's spelling, and the saved grid is what downstream reads back."""
    assert "lon" in grid.columns
    assert "long" not in grid.columns


def test_grid_carries_its_distance_features(grid):
    assert {"distance_to_river", "distance_to_coastline", "is_island"} <= set(grid.columns)
    assert (grid["distance_to_river"] > 0).all()


def test_zero_distances_do_not_become_infinite_logs(write_point_grid_cache, rivers_through_the_grid):
    """The grid is written to disk, so a -inf from log(0) persists into every later run."""
    cache_dir = write_point_grid_cache(rivers_through_the_grid)

    grid = load_grid_point_data(cache_dir, region="custom", iso_list=["FRA"], file_reg_name="toy", grid_size=3)

    on_a_river = grid[grid["distance_to_river"] == 0]

    assert len(on_a_river) > 0
    assert np.isfinite(grid[["log_distance_to_river", "log_distance_to_coastline"]]).all().all()
    assert on_a_river["log_distance_to_river"].eq(0.0).all()

    clear_of_a_river = grid[grid["distance_to_river"] > 0]

    assert len(clear_of_a_river) > 0
    assert clear_of_a_river["log_distance_to_river"].eq(np.log(clear_of_a_river["distance_to_river"])).all()


def test_reloading_the_cached_grid_restores_the_full_column_names(write_point_grid_cache):
    """Shapefile fields truncate to ten characters, so the warm path renames them back."""
    cache_dir = write_point_grid_cache()
    kwargs: dict[str, Any] = {"region": "custom", "iso_list": ["FRA"], "file_reg_name": "toy", "grid_size": 3}

    written = load_grid_point_data(cache_dir, **kwargs)
    reloaded = load_grid_point_data(cache_dir, **kwargs)

    assert set(written.columns) == set(reloaded.columns)
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


def test_the_synthetic_warm_path_normalises_longitude(tmp_path):
    """It reads the largest cache in the project, so it must go through the same shim."""
    fpath = make_synthetic_data_fpath(tmp_path, "region", 1, "sea")
    fpath.write_text(f",ISO,long,lat,Start_Year\n0,LAO,{CURRENT_LON},18.5,1990-01-01\n")

    points = load_synthetic_non_disaster_points(tmp_path, ["LAO"], "sea")

    assert "lon" in points.columns
    assert points.geometry.x.tolist() == [CURRENT_LON]


def test_the_non_disaster_grid_warm_path_normalises_longitude(tmp_path):
    fpath = tmp_path / "grid.csv"
    fpath.write_text(f",ISO,long,lat\n0,LAO,{CURRENT_LON},18.5\n")

    grid = load_non_disaster_grid(tmp_path, grid=None, grid_name="grid.csv")

    assert "lon" in grid.columns
    assert "long" not in grid.columns
