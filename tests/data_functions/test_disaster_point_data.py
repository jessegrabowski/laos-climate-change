import numpy as np
import pytest

from climate_risk import load_synthetic_non_disaster_points
from climate_risk.data_functions.disaster_point_data import (
    load_grid_point_data,
    make_synthetic_data_fpath,
)


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
    kwargs = {"region": "custom", "iso_list": ["FRA"], "file_reg_name": "toy", "grid_size": 3}

    written = load_grid_point_data(cache_dir, **kwargs)
    reloaded = load_grid_point_data(cache_dir, **kwargs)

    assert set(written.columns) == set(reloaded.columns)
    assert {"distance_to_river", "log_distance_to_river", "log_distance_to_coastline"} <= set(reloaded.columns)
