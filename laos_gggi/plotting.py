import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.offsetbox import AnchoredText
import seaborn as sns
from scipy import stats
import numpy as np
import math
from laos_gggi.const_vars import REGIONS
import arviz as az
import geopandas as gpd
from laos_gggi.model import get_distance_to


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

    plt.rcParams.update(config)


def prepare_gridspec_figure(
    n_cols: int, n_plots: int, figure: plt.Figure | None = None
) -> tuple[GridSpec, list]:
    """
     Prepare a figure with a grid of subplots. Centers the last row of plots if the number of plots is not square.

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
    data = data.dropna()
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


# Aggregated plotting function
def subplots_function(
    df,
    var_list,
    index,
    aggregation_funct,
    title,
    graph_rows=2,
    figure_size=(20, 18),
    subplot_title_fontsize=14,
):
    fig, axs = plt.subplots(graph_rows, 2, figsize=figure_size)

    for x in var_list:
        a = math.floor(var_list.index(x) / 2)
        b = var_list.index(x) % 2
        axs[a, b].plot(
            df.pivot_table(values=x, index=index, aggfunc=aggregation_funct)[x]
        )
        axs[a, b].set_title(x, fontsize=subplot_title_fontsize)

    if (len(var_list) % 2) != 0:
        axs[graph_rows - 1, 1].set_axis_off()

    plt.suptitle(title, fontsize=subplot_title_fontsize + 10)
    fig.tight_layout()


# Aggregated plotting function for regions
def subplots_function_regions(
    df,
    var_list,
    index,
    aggregation_funct,
    title,
    graph_rows=2,
    figure_size=(20, 18),
    subplot_title_fontsize=14,
):
    fig, axs = plt.subplots(graph_rows, 2, figsize=figure_size)

    for x in var_list:
        a = math.floor(var_list.index(x) / 2)
        b = var_list.index(x) % 2
        for y in REGIONS:
            axs[a, b].plot(
                df.query(f'Region == "{y}"').pivot_table(
                    values=x, index=index, aggfunc=aggregation_funct
                ),
                label=y,
            )
            axs[a, b].set_title(x, fontsize=subplot_title_fontsize)
        # axs[a,b].legend()

    if (len(var_list) % 2) != 0:
        axs[graph_rows - 1, 1].set_axis_off()
    fig.legend(REGIONS, loc="lower right", ncol=5, fontsize=16)
    plt.suptitle(title, fontsize=subplot_title_fontsize + 10)
    fig.tight_layout(rect=[0, 0, 1, 0.95])


def plot_ppc_loopit(
    idata: az.InferenceData, target_name: str, title: str | None = None, **ppc_kwargs
) -> list[plt.Axes]:
    """
    Plot the posterior predictive check (PPC) and the leave-one-out predictive interval (LOO-PIT) for a given target variable.

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
    for ax, ecdf in zip([ax_loo, ax_ecdf], [False, True]):
        az.plot_loo_pit(idata, y=target_name, ecdf=ecdf, ax=ax)

    if title is None:
        title = target_name
    ax_ppc.set_title(title)
    ax_ppc.set_xlabel("")
    return fig.axes


# Function to create plot inputs
def generate_plot_inputs(idata, df):
    # Extract predictions
    predictions = idata.posterior_predictive["y_hat"].mean(dim=["chain", "draw"])
    predictions = (
        predictions.to_dataframe()
        .drop(columns=["ISO"])
        .reset_index()
        .rename(columns={"y_hat": "predictions"})
    )

    hdi_mean = az.hdi(idata.posterior_predictive.y_hat)

    hdi = hdi_mean["y_hat"].to_dataframe().drop(columns=["ISO"]).reset_index()

    hdi_mean_50 = az.hdi(idata.posterior_predictive.y_hat, hdi_prob=0.5)

    hdi_50 = hdi_mean_50["y_hat"].to_dataframe().drop(columns=["ISO"]).reset_index()

    # Merge results and predictions in one df
    df_predictions = df[["ISO"]]

    # 95% HDI
    df_predictions = pd.merge(
        df_predictions,
        hdi.query('hdi == "lower"')[["ISO", "y_hat"]],
        left_on=["ISO"],
        right_on=["ISO"],
        how="left",
    ).rename(columns={"y_hat": "lower_y_hat_95"})
    df_predictions = pd.merge(
        df_predictions,
        hdi.query('hdi == "higher"')[["ISO", "y_hat"]],
        left_on=["ISO"],
        right_on=["ISO"],
        how="left",
    ).rename(columns={"y_hat": "higher_y_hat_95"})
    # 50% HDI
    df_predictions = pd.merge(
        df_predictions,
        hdi_50.query('hdi == "lower"')[["ISO", "y_hat"]],
        left_on=["ISO"],
        right_on=["ISO"],
        how="left",
    ).rename(columns={"y_hat": "lower_y_hat_50"})
    df_predictions = pd.merge(
        df_predictions,
        hdi_50.query('hdi == "higher"')[["ISO", "y_hat"]],
        left_on=["ISO"],
        right_on=["ISO"],
        how="left",
    ).rename(columns={"y_hat": "higher_y_hat_50"})

    # Predictions
    df_predictions = pd.merge(
        df_predictions, predictions, left_on=["ISO"], right_on=["ISO"], how="left"
    ).rename(columns={"y_hat": "predictions"})

    return df_predictions


# Plotting function
def plotting_function(idata, country: str):
    df_predictions = generate_plot_inputs(idata=idata)

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

    # plt.title(f"{country} disaster count and predictions")

    plt.xlabel("Start_Year")
    plt.ylabel("Disaster Count")

    plt.show()


############################################ Functions for the damage model  #############################################
# Function to create plot inputs


def generate_plot_inputs_damages(
    target_variable: str,
    idata,
    disaster_type: str = "hydrological_disasters",
    df=pd.DataFrame,
):
    # Extract predictions
    predictions = idata.posterior_predictive["damage_millions"].mean(
        dim=["chain", "draw"]
    )
    predictions = (
        predictions.to_dataframe()
        .drop(columns=["year", "ISO"])
        .reset_index()
        .rename(columns={target_variable: "predictions"})
    )

    hdi_mean = az.hdi(idata.posterior_predictive.damage_millions, hdi_prob=0.75)

    hdi = (
        hdi_mean["damage_millions"]
        .to_dataframe()
        .drop(columns=["year", "ISO"])
        .reset_index()
    )

    hdi_mean_50 = az.hdi(idata.posterior_predictive.damage_millions, hdi_prob=0.5)

    hdi_50 = (
        hdi_mean_50["damage_millions"]
        .to_dataframe()
        .drop(columns=["year", "ISO"])
        .reset_index()
    )

    # Merge results and predictions in one df
    df_predictions = df[[target_variable, "ISO", "year"]]

    # Obtain mean hdis per year and countries
    lower_hdi_75_mean = hdi.query('hdi == "lower"')[
        ["ISO", "year", "damage_millions"]
    ].rename(columns={"damage_millions": "lower_damage_75"})

    higher_hdi_75_mean = hdi.query('hdi == "higher"')[
        ["ISO", "year", "damage_millions"]
    ].rename(columns={"damage_millions": "higher_damage_75"})

    lower_hdi_50_mean = hdi_50.query('hdi == "lower"')[
        ["ISO", "year", "damage_millions"]
    ].rename(columns={"damage_millions": "lower_damage_50"})

    higher_hdi_50_mean = hdi_50.query('hdi == "higher"')[
        ["ISO", "year", "damage_millions"]
    ].rename(columns={"damage_millions": "higher_damage_50"})

    predictions_mean = predictions

    # 75% HDI
    df_predictions = pd.merge(
        df_predictions,
        lower_hdi_75_mean,
        left_on=["ISO", "year"],
        right_on=["ISO", "year"],
        how="left",
    )
    df_predictions = pd.merge(
        df_predictions,
        higher_hdi_75_mean,
        left_on=["ISO", "year"],
        right_on=["ISO", "year"],
        how="left",
    )
    # 50% HDI
    df_predictions = pd.merge(
        df_predictions,
        lower_hdi_50_mean,
        left_on=["ISO", "year"],
        right_on=["ISO", "year"],
        how="left",
    )
    df_predictions = pd.merge(
        df_predictions,
        higher_hdi_50_mean,
        left_on=["ISO", "year"],
        right_on=["ISO", "year"],
        how="left",
    )
    # Predictions
    df_predictions = pd.merge(
        df_predictions,
        predictions_mean,
        left_on=["ISO", "year"],
        right_on=["ISO", "year"],
        how="left",
    )
    return df_predictions


def plotting_function_damages(
    idata, country: str, df: pd.DataFrame, target_variable: str
):
    df_predictions = generate_plot_inputs_damages(
        idata=idata, df=df, target_variable=target_variable
    )

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
    ax.legend(loc="upper left")

    # plt.title(f"{country} disaster count and predictions")

    plt.xlabel("year")
    plt.ylabel("hydrometereological events damage in millions of dollars")

    plt.show()


def create_grid_from_shape(shapefile, rivers, coastline, grid_size=100):
    long_min, lat_min, long_max, lat_max = shapefile.dissolve().bounds.values.ravel()
    long_grid = np.linspace(long_min, long_max, grid_size)
    lat_grid = np.linspace(lat_min, lat_max, grid_size)

    grid = np.column_stack([x.ravel() for x in np.meshgrid(long_grid, lat_grid)])
    grid = gpd.GeoSeries(gpd.points_from_xy(*grid.T), crs="EPSG:4326")
    grid = gpd.GeoDataFrame({"geometry": grid})

    point_overlay = grid.overlay(shapefile, how="intersection")
    points = point_overlay.geometry
    points = points.to_frame().assign(
        long=lambda x: x.geometry.x, lat=lambda x: x.geometry.y
    )

    # Obtain distance with rivers
    distances_to_rivers = get_distance_to(
        rivers, points=points, return_columns=["ORD_FLOW", "HYRIV_ID"]
    ).rename(columns={"distance_to_closest": "distance_to_river"})

    points = pd.merge(
        points, distances_to_rivers, left_index=True, right_index=True, how="left"
    )

    # Obtain Laos distance with coastlines
    distances_to_coastlines = get_distance_to(
        coastline.boundary, points=points, return_columns=None
    ).rename(columns={"distance_to_closest": "distance_to_coastline"})

    points = pd.merge(
        points, distances_to_coastlines, left_index=True, right_index=True, how="left"
    )

    # Create log of distances
    points = points.assign(
        log_distance_to_river=lambda x: np.log(x.distance_to_river),
        log_distance_to_coastline=lambda x: np.log(x.distance_to_coastline),
    )

    if "ISO_A3" in point_overlay.columns:
        points["ISO"] = point_overlay.ISO_A3
    else:
        points["ISO"] = "LAO"

    return points
