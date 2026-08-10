import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from climate_risk.plotting import (
    REGIONS,
    attach_count_predictions,
    attach_damage_predictions,
    configure_plot_style,
    plot_aggregated_series,
    plot_aggregated_series_by_region,
    plot_descriptive,
    plot_predicted_counts,
    plot_predicted_damages,
    prepare_gridspec_figure,
)

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
    inputs = attach_count_predictions(idata, counts)

    assert set(counts.columns) <= set(inputs.columns)
    assert inputs["predictions"].is_monotonic_increasing


def test_hdi_bounds_bracket_the_prediction(idata, counts):
    """The bands are drawn as fill_between, so an inverted bound silently plots nothing."""
    inputs = attach_count_predictions(idata, counts)

    assert (inputs["lower_y_hat_95"] < inputs["predictions"]).all()
    assert (inputs["higher_y_hat_95"] > inputs["predictions"]).all()
    assert (inputs["lower_y_hat_50"] >= inputs["lower_y_hat_95"]).all()
    assert (inputs["higher_y_hat_50"] <= inputs["higher_y_hat_95"]).all()


def test_a_frame_of_the_wrong_length_is_rejected(idata, counts):
    """Aligning by position means a mismatched frame would otherwise plot the wrong country."""
    with pytest.raises(ValueError, match="observations but df has"):
        attach_count_predictions(idata, counts.iloc[:2])


def test_plotting_one_country_draws_only_its_observations(idata, counts):
    fig = plot_predicted_counts(idata, counts, "AAA")

    predicted_line = fig.axes[0].lines[0]
    assert len(np.asarray(predicted_line.get_xdata())) == 2


def test_damage_bounds_bracket_the_prediction(damages_idata, damages):
    inputs = attach_damage_predictions(damages_idata, damages)

    assert (inputs["lower_damage_75"] < inputs["predictions"]).all()
    assert (inputs["higher_damage_75"] > inputs["predictions"]).all()
    assert (inputs["lower_damage_50"] >= inputs["lower_damage_75"]).all()
    assert (inputs["higher_damage_50"] <= inputs["higher_damage_75"]).all()


def test_plotting_damages_draws_only_one_country(damages_idata, damages):
    fig = plot_predicted_damages(damages_idata, damages, "AAA", "damage_millions")

    observed_points = fig.axes[0].collections[0]
    assert len(np.asarray(observed_points.get_offsets())) == 2


def test_each_variable_lands_on_its_own_panel():
    """Panels are filled by position; the previous index lookup sent duplicate names to one axis."""
    df = pd.DataFrame({"year": [1990, 1991] * 3, "a": range(6), "b": range(6), "c": range(6)})

    fig = plot_aggregated_series(df, ["a", "b", "c"], index="year", aggregation="mean", title="t")

    drawn = [axis.get_title() for axis in fig.axes if axis.get_title()]
    assert drawn == ["a", "b", "c"]


def test_an_odd_number_of_variables_blanks_the_spare_panel():
    """A grid is two wide, so an odd count leaves an empty axis that would otherwise show as blank
    ticks and a frame."""
    df = pd.DataFrame({"year": [1990, 1991] * 3, "a": range(6), "b": range(6), "c": range(6)})

    fig = plot_aggregated_series(df, ["a", "b", "c"], index="year", aggregation="mean", title="t")

    assert not fig.axes[3].axison


def test_every_region_is_drawn_on_each_panel():
    """One line per region per variable; a mis-scoped loop silently plots only the last region."""
    df = pd.DataFrame(
        {
            "year": [1990, 1991] * len(REGIONS),
            "Region": [region for region in REGIONS for _ in range(2)],
            "a": range(2 * len(REGIONS)),
            "b": range(2 * len(REGIONS)),
        }
    )

    fig = plot_aggregated_series_by_region(df, ["a", "b"], index="year", aggregation="mean", title="t")

    panels = [axis for axis in fig.axes if axis.get_title()]
    assert [axis.get_title() for axis in panels] == ["a", "b"]
    assert all(len(axis.get_lines()) == len(REGIONS) for axis in panels)


def test_the_grid_centres_a_short_last_row():
    """Five plots in three columns leaves two on the bottom row; left-aligning them looks broken."""
    _, locations = prepare_gridspec_figure(n_cols=3, n_plots=5)

    assert len(locations) == 5
    last_row_columns = [columns.start for _, columns in locations[3:]]
    assert last_row_columns == [1, 3], "the short row should be inset, not flush left"


def test_the_grid_is_exact_when_the_plots_fill_it():
    _, locations = prepare_gridspec_figure(n_cols=3, n_plots=6)

    assert len(locations) == 6
    assert [columns.start for _, columns in locations[:3]] == [0, 2, 4]


def test_configuring_the_style_turns_the_grid_on_and_off():
    """Every notebook opens with this call, and a silently ignored argument is invisible."""
    configure_plot_style(add_grid=True)
    assert plt.rcParams["axes.grid"] is True

    configure_plot_style()
    assert plt.rcParams["axes.grid"] is False


def test_a_single_column_frame_plots_without_unwrapping_it_first():
    """A one-column DataFrame took the single-panel branch and reached `data.name`, which a frame
    does not have, so every caller with one variable raised AttributeError."""
    df = pd.DataFrame({"only": np.linspace(0.0, 1.0, 40)})

    axis = plot_descriptive(df, add_sum_box=False)

    assert isinstance(axis, plt.Axes), "one column returns the axis, not the figure"
    assert axis.get_title() == "only"


def test_one_panel_is_drawn_per_column():
    df = pd.DataFrame({name: np.linspace(0.0, 1.0, 40) for name in ("a", "b", "c")})

    fig = plot_descriptive(df, add_sum_box=False)

    assert isinstance(fig, plt.Figure), "several columns return the figure, not an axis"
    assert [axis.get_title() for axis in fig.axes] == ["a", "b", "c"]
