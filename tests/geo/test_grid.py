import geopandas as gpd
import numpy as np

from climate_risk.geo.grid import create_grid_from_shape
from tests.conftest import toy_world


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
