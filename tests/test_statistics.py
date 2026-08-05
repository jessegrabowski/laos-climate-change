import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from shapely.geometry import LineString

from climate_risk.statistics import (
    ADF_test_summary,
    create_grid_from_shape,
    get_distance_to,
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


def test_distance_is_measured_in_metres_of_the_projected_crs(grid_points):
    """The callers divide by 1000 to get km, which only holds while the CRS is metric."""
    rivers = gpd.GeoDataFrame(
        {"ORD_FLOW": [4], "HYRIV_ID": [1], "geometry": [LineString([(0, -1), (0, 2)])]}, crs="EPSG:4326"
    )

    distances = get_distance_to(rivers, points=grid_points, n_cores=1)["distance_to_closest"]

    assert distances.iloc[0] > 10_000
    assert distances.iloc[0] < distances.iloc[1]


def test_requested_columns_come_from_the_nearest_feature(grid_points):
    far = LineString([(50, 50), (50, 51)])
    near = LineString([(0, -1), (0, 2)])
    rivers = gpd.GeoDataFrame({"ORD_FLOW": [9, 4], "HYRIV_ID": [99, 1], "geometry": [far, near]}, crs="EPSG:4326")

    nearest = get_distance_to(rivers, points=grid_points, return_columns=["ORD_FLOW", "HYRIV_ID"], n_cores=1)

    assert nearest["HYRIV_ID"].tolist() == [1, 1]
    assert nearest["ORD_FLOW"].tolist() == [4, 4]


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
