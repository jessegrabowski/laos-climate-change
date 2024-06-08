import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.offsetbox import AnchoredText
import seaborn as sns
from scipy import stats
import numpy as np


def prepare_gridspec_figure(n_cols: int, n_plots: int) -> tuple[GridSpec, list]:
    """
     Prepare a figure with a grid of subplots. Centers the last row of plots if the number of plots is not square.

    Parameters
    ----------
     n_cols : int
         The number of columns in the grid.
     n_plots : int
         The number of subplots in the grid.

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

    gs = GridSpec(2 * n_rows, 2 * n_cols)
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


def _plot_single_kde(data: pd.Series, axis=None, bins=30, color="tab:blue"):
    """
    Plot a single KDE plot on a given axis.

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

    if axis is None:
        fig, axis = plt.subplots()

    axis.hist(data, bins=bins, density=True, facecolor="none", edgecolor="k", lw=0.5)
    axis.hist(data, bins=bins, density=True, facecolor=color, alpha=0.25)
    sns.kdeplot(data, ax=axis, lw=2, c="k", ls="--")

    n, minmax, mean, var, skew, kurt = stats.describe(data.values.squeeze())
    jb = stats.jarque_bera(data.values.squeeze())

    names = ["N", "Min", "Max", "Mean", "Std", "Skew", "Kurt", "JB"]
    values = [n, minmax[0], minmax[1], mean, np.sqrt(var), skew, kurt, jb.statistic]

    text = "\n".join(
        f'{name:<5} = {" " if value > 0 else ""}{value:<3.3f}'
        for name, value in zip(names, values)
    )
    box = AnchoredText(text, loc="upper left", prop={"fontfamily": "monospace"})
    box.patch.set_alpha(0.5)
    axis.add_artist(box)
    axis.set_title(data.name)

    return axis


def plot_descriptive(
    df: pd.DataFrame | pd.Series,
    n_cols: int = 3,
    bins: int = 30,
    color: str = "tab:blue",
    **figure_kwargs,
):
    """
    Plot a grid of KDE plots for each column in a DataFrame.

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
        return _plot_single_kde(df, axis=ax, bins=bins, color=color)

    fig = plt.figure(figsize=figsize, dpi=dpi, **figure_kwargs)

    n_cols = min(n_cols, n_plots)
    gs, locs = prepare_gridspec_figure(n_cols=n_cols, n_plots=n_plots)

    for name, loc in zip(df.columns, locs):
        axis = fig.add_subplot(gs[loc])
        _plot_single_kde(df[name], axis=axis, bins=bins, color=color)

    return fig
