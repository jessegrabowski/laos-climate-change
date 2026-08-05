import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from climate_risk.statistics import (
    ADF_test_summary,
    create_grid_from_shape,
    make_var_names,
    nan_or_sum,
)
from tests.conftest import toy_world


def test_all_missing_stays_missing():
    """A country-year with no observations must not become a zero disaster count."""
    assert np.isnan(nan_or_sum(np.array([np.nan, np.nan])))


def test_partial_missing_sums_the_observed_values():
    assert nan_or_sum(np.array([1.0, np.nan, 2.0])) == 3.0


def test_all_zero_is_a_real_zero():
    assert nan_or_sum(np.array([0.0, 0.0])) == 0.0


@pytest.mark.parametrize(
    ("n_lags", "regression", "expected"),
    [
        (0, "n", ["L1.x"]),
        (1, "n", ["L1.x", "D1L1.x"]),
        (1, "c", ["L1.x", "D1L1.x", "Constant"]),
        (1, "ct", ["L1.x", "D1L1.x", "Constant", "Trend"]),
    ],
)
def test_var_names_follow_the_regression_terms(n_lags, regression, expected):
    """The names label ADF output columns positionally, so an extra or missing one misaligns them."""
    assert make_var_names("x", n_lags, regression) == expected


def test_missing_data_is_refused_by_default():
    """statsmodels would otherwise return a silent nan for the whole test."""
    with pytest.raises(ValueError, match="missing data"):
        ADF_test_summary(pd.DataFrame({"x": [1.0, np.nan, 3.0]}))


def test_grid_takes_its_iso_from_the_shapefile(rivers_clear_of_the_grid, coastline):
    """The fallback is a hardcoded LAO, so a shapefile carrying ISO_A3 must win."""
    grid = create_grid_from_shape(toy_world(), rivers_clear_of_the_grid, coastline, grid_size=4)

    assert set(grid["ISO"]) <= {"AAA", "BBB", "CCC"}


def test_grid_points_fall_inside_the_shapefile(rivers_clear_of_the_grid, coastline):
    world = toy_world()

    grid = create_grid_from_shape(world, rivers_clear_of_the_grid, coastline, grid_size=4)

    assert len(grid) > 0
    assert gpd.GeoSeries(grid.geometry, crs="EPSG:4326").covered_by(world.union_all()).all()


def test_zero_distances_do_not_become_infinite_logs(rivers_through_the_grid, coastline_through_the_grid):
    """A grid point on a river measures zero, and log(0) poisons the regressor with -inf."""
    grid = create_grid_from_shape(toy_world(), rivers_through_the_grid, coastline_through_the_grid, grid_size=4)

    on_a_river = grid[grid["distance_to_river"] == 0]

    assert len(on_a_river) > 0
    assert (grid["distance_to_coastline"] == 0).any()
    assert np.isfinite(grid[["log_distance_to_river", "log_distance_to_coastline"]]).all().all()
    assert on_a_river["log_distance_to_river"].eq(0.0).all()

    clear_of_a_river = grid[grid["distance_to_river"] > 0]

    assert len(clear_of_a_river) > 0
    assert clear_of_a_river["log_distance_to_river"].eq(np.log(clear_of_a_river["distance_to_river"])).all()
