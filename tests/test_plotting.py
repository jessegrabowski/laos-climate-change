import numpy as np
import pandas as pd
import pytest
import xarray as xr

from climate_risk.plotting import generate_plot_inputs, plotting_function

OBSERVATIONS = 4
ISO_CODES = ["AAA", "AAA", "BBB", "BBB"]
YEARS = pd.to_datetime(["1990", "1991", "1990", "1991"])


@pytest.fixture
def counts():
    return pd.DataFrame({"ISO": ISO_CODES, "Start_Year": YEARS, "is_disaster": [1, 0, 1, 1]})


def _posterior_predictive(name):
    """Draws spread around a per-observation mean, so the HDI bounds are genuinely distinct."""
    rng = np.random.default_rng(0)
    draws = np.arange(OBSERVATIONS, dtype=float) + rng.normal(0, 1, size=(2, 50, OBSERVATIONS))
    variable = xr.DataArray(draws, dims=("chain", "draw", "obs"), coords={"obs": np.arange(OBSERVATIONS)})
    return xr.DataTree.from_dict({"posterior_predictive": xr.Dataset({name: variable})})


@pytest.fixture
def idata():
    return _posterior_predictive("y_hat")


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
