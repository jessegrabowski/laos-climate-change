from typing import Literal

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xarray as xr

from matplotlib.gridspec import GridSpec
from matplotlib.offsetbox import AnchoredText
from scipy import stats

REGIONS = ["Asia", "Europe", "Africa", "Oceania", "Americas"]


def configure_plot_style(add_grid=False):
    config = {
        "figure.figsize": (14, 4),
        "figure.constrained_layout.use": True,
        "figure.facecolor": "w",
        "axes.grid": add_grid,
        "grid.linewidth": 0.5,
        "grid.linestyle": "--",
        "axes.spines.top": False,
        "axes.spines.bottom": False,
        "axes.spines.left": False,
        "axes.spines.right": False,
    }

    pd.set_option("display.float_format", "{:.2f}".format)
    plt.rcParams.update(config)


def prepare_gridspec_figure(n_cols: int, n_plots: int, figure: plt.Figure | None = None) -> tuple[GridSpec, list]:
    """Prepare a figure with a grid of subplots. Centers the last row of plots if the number of plots is not square.

    Parameters
    ----------
     n_cols : int
         The number of columns in the grid.
     n_plots : int
         The number of subplots in the grid.
    figure: plt.Figure, optional
        Figure on which to plot, passed to GridSpec constructor.

    Returns
    -------
     GridSpec
         A matplotlib GridSpec object representing the layout of the grid.
    list of tuple(slice, slice)
         A list of tuples of slices representing the indices of the grid cells to be used for each subplot.
    """
    remainder = n_plots % n_cols
    has_remainder = remainder > 0
    n_rows = n_plots // n_cols + int(has_remainder)

    gs = GridSpec(2 * n_rows, 2 * n_cols, figure=figure)
    plot_locs = []

    for i in range(n_rows - int(has_remainder)):
        for j in range(n_cols):
            plot_locs.append((slice(i * 2, (i + 1) * 2), slice(j * 2, (j + 1) * 2)))

    if has_remainder:
        last_row = slice((n_rows - 1) * 2, n_rows * 2)
        left_pad = int(n_cols - remainder)
        for j in range(remainder):
            col_slice = slice(left_pad + j * 2, left_pad + (j + 1) * 2)
            plot_locs.append((last_row, col_slice))

    return gs, plot_locs


def _plot_single_kde(
    data: pd.Series,
    axis=None,
    bins=30,
    color="tab:blue",
    leg_loc="upper left",
    set_title: bool = True,
    add_sum_box: bool = True,
):
    """Plot a single KDE plot on a given axis.

    Parameters
    ----------
    data : array_like
         The data to plot.
    axis : matplotlib.axes.Axes, optional
         The axis to plot on. If None, a new figure and axis are created.
    bins : int, optional
        Number of bins to use in the histogram.
    color : str, optional
        The color of the histogram bars

    Returns
    -------
     matplotlib.axes.Axes
         The axis the plot was created on.
    """
    data = data.dropna()
    if axis is None:
        _fig, axis = plt.subplots()

    axis.hist(data, bins=bins, density=True, facecolor="none", edgecolor="k", lw=0.5)
    axis.hist(data, bins=bins, density=True, facecolor=color, alpha=0.25)
    sns.kdeplot(data, ax=axis, lw=2, c="k", ls="--")

    if add_sum_box:
        n, minmax, mean, var, skew, kurt = stats.describe(data.values.squeeze())
        jb = stats.jarque_bera(data.values.squeeze())

        names = ["N", "Min", "Max", "Mean", "Std", "Skew", "Kurt", "JB"]
        values = [n, minmax[0], minmax[1], mean, np.sqrt(var), skew, kurt, jb.statistic]

        text = "\n".join(
            f"{name:<5} = {' ' if value > 0 else ''}{value:<3.3f}" for name, value in zip(names, values, strict=False)
        )
        box = AnchoredText(text, loc=leg_loc, prop={"fontfamily": "monospace"})
        box.patch.set_alpha(0.5)
        axis.add_artist(box)
    if set_title:
        axis.set_title(data.name)

    return axis


def plot_descriptive(
    df: pd.DataFrame | pd.Series,
    n_cols: int = 3,
    bins: int = 30,
    color: str = "tab:blue",
    leg_loc="upper left",
    labels_size: int = 14,
    add_sum_box: bool = True,
    **figure_kwargs,
):
    """Plot a grid of KDE plots for each column in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame or pd.Series
        The data to plot.
    n_cols : int, optional
        The number of columns in the grid of plots.
    bins : int, optional
        Number of bins to use in the histogram.
    color : str, optional
        The color of the histogram bars
    figure_kwargs : dict
        Additional keyword arguments to pass to plt.figure().

    Returns
    -------
    fig: matplotlib.figure.Figure
        The figure the plots were created on.
    """
    figsize = figure_kwargs.pop("figsize", (14, 4))
    dpi = figure_kwargs.pop("dpi", 144)

    n_plots = df.shape[1] if isinstance(df, pd.DataFrame) else 1

    if n_plots == 1:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        return _plot_single_kde(df, axis=ax, bins=bins, color=color, add_sum_box=add_sum_box)

    fig = plt.figure(figsize=figsize, dpi=dpi, **figure_kwargs)

    n_cols = min(n_cols, n_plots)
    gs, locs = prepare_gridspec_figure(n_cols=n_cols, n_plots=n_plots)

    for name, loc in zip(df.columns, locs, strict=False):
        axis = fig.add_subplot(gs[loc])
        axis.set_ylabel("Density", fontsize=labels_size)
        _plot_single_kde(
            df[name],
            axis=axis,
            bins=bins,
            color=color,
            leg_loc=leg_loc,
            add_sum_box=add_sum_box,
        )

    return fig


AGGREGATE_COLUMNS = 2

Aggregation = Literal["count", "first", "last", "max", "mean", "median", "min", "nunique", "std", "sum", "var"]


def plot_aggregated_series(
    df: pd.DataFrame,
    variables: list[str],
    index: str,
    aggregation: Aggregation,
    title: str,
    graph_rows: int = 2,
    figure_size: tuple[float, float] = (20, 18),
    subplot_title_fontsize: int = 14,
) -> plt.Figure:
    """
    Plot one variable per panel, each aggregated over ``index``.

    Parameters
    ----------
    df : DataFrame
        The observations to aggregate.
    variables : list of str
        Columns to plot, one panel each, filling the grid left to right.
    index : str
        Column to aggregate over, which becomes the x axis.
    aggregation : str
        How to combine rows sharing an index value, as named in ``Aggregation``.
    title : str
        Heading for the figure.
    graph_rows : int, optional
        Rows in the grid, which is two columns wide. Default 2.
    figure_size : tuple of float, optional
        Figure width and height in inches. Default (20, 18).
    subplot_title_fontsize : int, optional
        Point size for each panel's title; the figure heading is ten points larger. Default 14.

    Returns
    -------
    Figure
        The figure the panels were drawn on.
    """
    fig, axes = plt.subplots(graph_rows, AGGREGATE_COLUMNS, figsize=figure_size)

    for position, variable in enumerate(variables):
        axis = axes[position // AGGREGATE_COLUMNS, position % AGGREGATE_COLUMNS]
        axis.plot(df.pivot_table(values=variable, index=index, aggfunc=aggregation)[variable])
        axis.set_title(variable, fontsize=subplot_title_fontsize)

    if len(variables) % AGGREGATE_COLUMNS:
        axes[graph_rows - 1, 1].set_axis_off()

    plt.suptitle(title, fontsize=subplot_title_fontsize + 10)
    fig.tight_layout()

    return fig


def plot_aggregated_series_by_region(
    df: pd.DataFrame,
    variables: list[str],
    index: str,
    aggregation: Aggregation,
    title: str,
    graph_rows: int = 2,
    figure_size: tuple[float, float] = (20, 18),
    subplot_title_fontsize: int = 14,
) -> plt.Figure:
    """
    Plot one variable per panel, aggregated over ``index`` and drawn once per region.

    Parameters
    ----------
    df : DataFrame
        The observations to aggregate, carrying a ``Region`` column.
    variables : list of str
        Columns to plot, one panel each, filling the grid left to right.
    index : str
        Column to aggregate over, which becomes the x axis.
    aggregation : str
        How to combine rows sharing an index value, as named in ``Aggregation``.
    title : str
        Heading for the figure.
    graph_rows : int, optional
        Rows in the grid, which is two columns wide. Default 2.
    figure_size : tuple of float, optional
        Figure width and height in inches. Default (20, 18).
    subplot_title_fontsize : int, optional
        Point size for each panel's title; the figure heading is ten points larger. Default 14.

    Returns
    -------
    Figure
        The figure the panels were drawn on.
    """
    fig, axes = plt.subplots(graph_rows, AGGREGATE_COLUMNS, figsize=figure_size)

    for position, variable in enumerate(variables):
        axis = axes[position // AGGREGATE_COLUMNS, position % AGGREGATE_COLUMNS]
        for region in REGIONS:
            in_region = df[df["Region"] == region]
            axis.plot(in_region.pivot_table(values=variable, index=index, aggfunc=aggregation), label=region)
        axis.set_title(variable, fontsize=subplot_title_fontsize)

    if len(variables) % AGGREGATE_COLUMNS:
        axes[graph_rows - 1, 1].set_axis_off()

    fig.legend(list(REGIONS), loc="lower right", ncol=len(REGIONS), fontsize=16)
    plt.suptitle(title, fontsize=subplot_title_fontsize + 10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    return fig


def plot_ppc_loopit(idata: xr.DataTree, target_name: str, title: str | None = None, **ppc_kwargs) -> list[plt.Axes]:
    """Plot the posterior predictive check (PPC) and the leave-one-out predictive interval (LOO-PIT) for a given target variable.

    Parameters
    ----------
    idata : arviz.InferenceData
        The inference data object containing the posterior samples.
    title : str
        The title for the plot.
    target_name : str, optional
        The name of the target variable. If None, the first variable in the posterior predictive data is used.

    Returns
    -------
    list
        A list of matplotlib axes objects representing the plot.
    """
    fig = plt.figure(figsize=(12, 9))
    gs = plt.GridSpec(2, 2, figure=fig)
    ax_ppc = fig.add_subplot(gs[0, :])
    ax_loo = fig.add_subplot(gs[1, 0])
    ax_ecdf = fig.add_subplot(gs[1, 1])

    az.plot_ppc(idata, ax=ax_ppc, var_names=[target_name], **ppc_kwargs)
    for ax, ecdf in zip([ax_loo, ax_ecdf], [False, True], strict=False):
        az.plot_loo_pit(idata, y=target_name, ecdf=ecdf, ax=ax)

    if title is None:
        title = target_name
    ax_ppc.set_title(title)
    ax_ppc.set_xlabel("")
    return fig.axes


SAMPLE_DIMS = ("chain", "draw")


def _aligned_prediction_mean(draws, df):
    """Return the posterior-predictive mean, checked against the frame it will be attached to."""
    predictions = draws.mean(dim=SAMPLE_DIMS)
    if predictions.size != len(df):
        raise ValueError(
            f"posterior_predictive holds {predictions.size} observations but df has {len(df)} rows; "
            f"they must be the observations the model saw, in the same order."
        )
    return predictions.values


def attach_count_predictions(idata, df):
    """Attach posterior-predictive means and HDI bounds to the observed frame.

    Parameters
    ----------
    idata : DataTree
        Inference data carrying a ``posterior_predictive`` group with a ``y_hat`` variable.
    df : DataFrame
        The observed frame, in the order the model saw it.

    Returns
    -------
    DataFrame
        ``df`` with ``predictions`` and the 95% and 50% HDI bounds appended.
    """
    y_hat = idata.posterior_predictive["y_hat"]
    predictions = _aligned_prediction_mean(y_hat, df)

    hdi_95 = az.hdi(y_hat, prob=0.95)
    hdi_50 = az.hdi(y_hat, prob=0.5)

    return df.assign(
        predictions=predictions,
        lower_y_hat_95=hdi_95.sel(ci_bound="lower").values,
        higher_y_hat_95=hdi_95.sel(ci_bound="upper").values,
        lower_y_hat_50=hdi_50.sel(ci_bound="lower").values,
        higher_y_hat_50=hdi_50.sel(ci_bound="upper").values,
    )


def plot_predicted_counts(idata, df, country: str) -> plt.Figure:
    df_predictions = attach_count_predictions(idata=idata, df=df)

    # Filter country
    data = df_predictions.query("ISO == @country")

    fig, ax = plt.subplots()
    ax.plot(
        data["Start_Year"],
        data["predictions"],
        zorder=1000,
        color="tab:red",
        label="Mean Predicted Disaster Count",
    )
    ax.scatter(data["Start_Year"], data["is_disaster"], color="k", label="Actual prob")
    ax.fill_between(
        data["Start_Year"],
        data["higher_y_hat_95"],
        data["lower_y_hat_95"],
        alpha=0.25,
        color="tab:blue",
        label="95% HDI",
    )
    ax.fill_between(
        data["Start_Year"],
        data["lower_y_hat_50"],
        data["higher_y_hat_50"],
        alpha=0.5,
        color="tab:blue",
        label="50% HDI",
    )
    ax.legend(loc="upper left")

    ax.set_xlabel("Start_Year")
    ax.set_ylabel("Disaster Count")

    return fig


############################################ Functions for the damage model  #############################################
def attach_damage_predictions(idata, df):
    """Attach posterior-predictive damage means and HDI bounds to the observed frame.

    Parameters
    ----------
    idata : DataTree
        Inference data carrying a ``posterior_predictive`` group with a ``damage_millions`` variable.
    df : DataFrame
        The observed frame, in the order the model saw it.

    Returns
    -------
    DataFrame
        ``df`` with ``predictions`` and the 75% and 50% HDI bounds appended.
    """
    damages = idata.posterior_predictive["damage_millions"]
    predictions = _aligned_prediction_mean(damages, df)

    hdi_75 = az.hdi(damages, prob=0.75)
    hdi_50 = az.hdi(damages, prob=0.5)

    return df.assign(
        predictions=predictions,
        lower_damage_75=hdi_75.sel(ci_bound="lower").values,
        higher_damage_75=hdi_75.sel(ci_bound="upper").values,
        lower_damage_50=hdi_50.sel(ci_bound="lower").values,
        higher_damage_50=hdi_50.sel(ci_bound="upper").values,
    )


def plot_predicted_damages(idata, df: pd.DataFrame, country: str, target_variable: str) -> plt.Figure:
    df_predictions = attach_damage_predictions(idata=idata, df=df)

    # Filter country
    data = df_predictions.query("ISO == @country")

    fig, ax = plt.subplots()
    ax.scatter(
        data["year"],
        (data[target_variable].astype(float)),
        color="k",
        label=("Real hydrometereological events damage in millions of dollars"),
    )
    ax.fill_between(
        data["year"],
        data["higher_damage_75"],
        data["lower_damage_75"],
        alpha=0.25,
        color="tab:blue",
        label="75% HDI",
    )
    ax.fill_between(
        data["year"],
        data["lower_damage_50"],
        data["higher_damage_50"],
        alpha=0.5,
        color="tab:blue",
        label="50% HDI",
    )
    ax.legend(loc="upper left", fontsize=14)
    ax.set_xlabel("year", fontsize=14)
    ax.set_ylabel("Disaster damages in 2000 USD millions", fontsize=14)
    ax.tick_params(axis="both", which="major", labelsize=12)

    return fig
