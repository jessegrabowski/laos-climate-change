import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from climate_risk.plotting import (
    create_grid_from_shape,
    generate_plot_inputs,
    generate_plot_inputs_damages,
    plotting_function,
    plotting_function_damages,
)
from tests.conftest import toy_world

OBSERVATIONS = 4
ISO_CODES = ["AAA", "AAA", "BBB", "BBB"]
YEARS = pd.to_datetime(["1990", "1991", "1990", "1991"])


@pytest.fixture
def counts():
    return pd.DataFrame({"ISO": ISO_CODES, "Start_Year": YEARS, "is_disaster": [1, 0, 1, 1]})


@pytest.fixture
def damages():
    return pd.DataFrame({"ISO": ISO_CODES, "year": YEARS, "damage_millions": [1.0, 2.0, 3.0, 4.0]})


def _posterior_predictive(name):
    """Draws spread around a per-observation mean, so the HDI bounds are genuinely distinct."""
    rng = np.random.default_rng(0)
    draws = np.arange(OBSERVATIONS, dtype=float) + rng.normal(0, 1, size=(2, 50, OBSERVATIONS))
    variable = xr.DataArray(draws, dims=("chain", "draw", "obs"), coords={"obs": np.arange(OBSERVATIONS)})
    return xr.DataTree.from_dict({"posterior_predictive": xr.Dataset({name: variable})})


@pytest.fixture
def idata():
    return _posterior_predictive("y_hat")


@pytest.fixture
def damages_idata():
    return _posterior_predictive("damage_millions")


def test_predictions_are_attached_in_row_order(idata, counts):
    inputs = generate_plot_inputs(idata, counts)

    assert set(counts.columns) <= set(inputs.columns)
    assert inputs["predictions"].is_monotonic_increasing


def test_hdi_bounds_bracket_the_prediction(idata, counts):
    """The bands are drawn as fill_between, so an inverted bound silently plots nothing."""
    inputs = generate_plot_inputs(idata, counts)

    assert (inputs["lower_y_hat_95"] < inputs["predictions"]).all()
    assert (inputs["higher_y_hat_95"] > inputs["predictions"]).all()
    assert (inputs["lower_y_hat_50"] >= inputs["lower_y_hat_95"]).all()
    assert (inputs["higher_y_hat_50"] <= inputs["higher_y_hat_95"]).all()


def test_a_frame_of_the_wrong_length_is_rejected(idata, counts):
    """Aligning by position means a mismatched frame would otherwise plot the wrong country."""
    with pytest.raises(ValueError, match="observations but df has"):
        generate_plot_inputs(idata, counts.iloc[:2])


def test_plotting_one_country_draws_only_its_observations(idata, counts):
    fig = plotting_function(idata, counts, "AAA")

    predicted_line = fig.axes[0].lines[0]
    assert len(predicted_line.get_xdata()) == 2


def test_damage_bounds_bracket_the_prediction(damages_idata, damages):
    inputs = generate_plot_inputs_damages(damages_idata, damages)

    assert (inputs["lower_damage_75"] < inputs["predictions"]).all()
    assert (inputs["higher_damage_75"] > inputs["predictions"]).all()
    assert (inputs["lower_damage_50"] >= inputs["lower_damage_75"]).all()
    assert (inputs["higher_damage_50"] <= inputs["higher_damage_75"]).all()


def test_plotting_damages_draws_only_one_country(damages_idata, damages):
    fig = plotting_function_damages(damages_idata, damages, "AAA", "damage_millions")

    observed_points = fig.axes[0].collections[0]
    assert len(observed_points.get_offsets()) == 2


def test_grid_takes_its_iso_from_the_shapefile(rivers_clear_of_the_grid, coastline):
    """The fallback is a hardcoded LAO, so a shapefile carrying ISO_A3 must win."""
    grid = create_grid_from_shape(toy_world(), rivers_clear_of_the_grid, coastline, grid_size=4)

    assert set(grid["ISO"]) <= {"AAA", "BBB", "CCC"}


def test_grid_points_fall_inside_the_shapefile(rivers_clear_of_the_grid, coastline):
    world = toy_world()

    grid = create_grid_from_shape(world, rivers_clear_of_the_grid, coastline, grid_size=4)

    assert len(grid) > 0
    assert gpd.GeoSeries(grid.geometry, crs="EPSG:4326").covered_by(world.union_all()).all()
