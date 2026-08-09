import datetime as dt

from pathlib import Path

import polars as pl

from climate_risk.config.schema import EventFilters

EM_DAT_COL_DICT = {
    "Start Year": "Start_Year",
    "Total Deaths": "Deaths",
    "No. Injured": "Injured",
    "No. Affected": "Numb_Affected",
    "No. Homeless": "Homeless",
    "Total Affected": "Total_Affected",
    "Reconstruction Costs ('000 US$)": "Reconstruction_Costs",
    "Reconstruction Costs, Adjusted ('000 US$)": "Reconstruction_Costs_Adjusted",
    "Insured Damage ('000 US$)": "Insured_Damage",
    "Insured Damage, Adjusted ('000 US$)": "Insured_Damage_Adjusted",
    "Total Damage ('000 US$)": "Total_Damage",
    "Total Damage, Adjusted ('000 US$)": "Total_Damage_Adjusted",
}

PROB_COLS = [
    "Country",
    "ISO",
    "Start_Year",
    "Drought",
    "Extreme temperature",
    "Flood",
    "Storm",
    "Wildfire",
    "Mass movement (dry)",
    "Mass movement (wet)",
    "Region",
    "Subregion",
]

INTENSITY_COLS = [
    "Country",
    "ISO",
    "Start_Year",
    "Region",
    "Deaths",
    "Injured",
    "Numb_Affected",
    "Homeless",
    "Total_Affected",
    "Total_Damage",
    "Total_Damage_Adjusted",
    "Disaster Type",
]

# The study window opens in 1969 and closes on the newest event in the workbook.
EMDAT_WINDOW_START = dt.date(1969, 1, 1)

# The types the panel counts. A country with no wildfires still needs a Wildfire column, so these
# are the columns the count frames carry whether or not the data contains them.
DISASTER_TYPES = tuple(c for c in PROB_COLS if c not in {"Country", "ISO", "Start_Year", "Region", "Subregion"})

# Columns read before any rename. Nothing detects upstream schema drift, so this check is the
# earliest point a changed export becomes a named error rather than a missing attribute.
REQUIRED_EMDAT_COLUMNS = {"ISO", "Region", "Subregion", "Disaster Type"} | set(EM_DAT_COL_DICT)

# Misspelled on the wire. Correcting it would invalidate every cached CSV on every machine, so the
# literal stays and the constants are how code should refer to it.
HYDROMETEOROLOGICAL = "Hydrometereological"
CLIMATOLOGICAL = "Climatological"

DISASTER_CLASSES = {
    "Storm": HYDROMETEOROLOGICAL,
    "Flood": HYDROMETEOROLOGICAL,
    "Mass movement (wet)": HYDROMETEOROLOGICAL,
    "Wildfire": CLIMATOLOGICAL,
    "Extreme temperature": CLIMATOLOGICAL,
    "Drought": CLIMATOLOGICAL,
}

DAMAGE_VARS = [
    "Deaths",
    "Injured",
    "Numb_Affected",
    "Homeless",
    "Total_Affected",
    "Total_Damage",
    "Total_Damage_Adjusted",
]

# A country-year with no events reads as missing rather than zero, which is what the replication
# panel relies on. Floats keep that true whether the frame is read as polars or as pandas.
COUNT_DTYPE = pl.Float64


def _read_workbook(emdat_path: Path) -> pl.DataFrame:
    """Read the EM-DAT sheet, raising a named error rather than letting a changed export surface later."""
    workbook = pl.read_excel(emdat_path, sheet_name="EM-DAT Data", raise_if_empty=False)

    if workbook.is_empty():
        raise ValueError(f"The `EM-DAT Data` sheet in `{emdat_path}` has no rows.")

    missing_columns = REQUIRED_EMDAT_COLUMNS - set(workbook.columns)
    if missing_columns:
        raise ValueError(
            f"The `EM-DAT Data` sheet in `{emdat_path}` is missing {sorted(missing_columns)}. "
            f"Re-download the database, or update EM_DAT_COL_DICT if the export has changed."
        )

    # disaster_point_data stores this row number in its own cache, so it is a key the workbook's
    # row order defines and must survive filtering.
    return (
        workbook.with_row_index("emdat_index")
        .rename(EM_DAT_COL_DICT)
        .with_columns(
            pl.date(pl.col("Start_Year"), 1, 1).alias("Start_Year"),
            pl.col("Disaster Type").replace_strict(DISASTER_CLASSES, default=None).alias("disaster_class"),
        )
    )


def country_year_grid(events: pl.DataFrame, *, window_start: dt.date = EMDAT_WINDOW_START) -> pl.DataFrame:
    """
    Cross every country with every year in the window, carrying each country's region.

    This is the grid the count and damage panels are laid over, so it is built from the *unfiltered*
    workbook: a country-year with no qualifying event still needs a row.

    Parameters
    ----------
    events : DataFrame
        The workbook, as :func:`load_emdat_events` returns it.
    window_start : datetime.date, optional
        First year of the panel. Default ``EMDAT_WINDOW_START``.

    Returns
    -------
    DataFrame
        ``ISO``, ``Start_Year``, ``Region`` and ``Subregion``, sorted by country and year.

    Raises
    ------
    ValueError
        If every ``Start_Year`` is missing, or the window starts after the newest event.
    """
    newest_event = events["Start_Year"].max()
    if not isinstance(newest_event, dt.date):
        raise ValueError("Every Start_Year in the workbook is missing, so the window has no end.")

    if window_start > newest_event:
        raise ValueError(
            f"window_start={window_start} is after the newest event in the workbook "
            f"({newest_event}), so every output frame would be empty."
        )

    years: pl.Series = pl.date_range(window_start, newest_event, interval="1y", eager=True)

    regions = events.select("ISO", "Region", "Subregion").unique(subset="ISO", keep="first")

    return (
        events.select(pl.col("ISO").unique())
        .join(years.alias("Start_Year").to_frame(), how="cross")
        .join(regions, on="ISO", how="left")
        .sort("ISO", "Start_Year")
    )


def count_events_by_type(events: pl.DataFrame, grid: pl.DataFrame) -> pl.DataFrame:
    """
    Count events per country, year and disaster type, over every row of ``grid``.

    Parameters
    ----------
    events : DataFrame
        Events to count, already narrowed to whichever ones should be counted.
    grid : DataFrame
        The country-year panel from :func:`country_year_grid`.

    Returns
    -------
    DataFrame
        One row per country-year, one column per disaster type. A country-year with no events
        reads as null rather than zero.
    """
    counted = (
        events.filter(pl.col("Disaster Type").is_in(DISASTER_TYPES))
        .group_by("ISO", "Start_Year", "Disaster Type")
        .len()
        .with_columns(pl.col("len").cast(COUNT_DTYPE))
        .pivot(on="Disaster Type", index=["ISO", "Start_Year"], values="len")
    )
    absent = [pl.lit(None, dtype=COUNT_DTYPE).alias(name) for name in DISASTER_TYPES if name not in counted.columns]

    return (
        grid.join(counted.with_columns(absent), on=["ISO", "Start_Year"], how="left")
        .select("ISO", "Start_Year", "Region", "Subregion", *DISASTER_TYPES)
        .sort("ISO", "Start_Year")
    )


def total_damage(events: pl.DataFrame, grid: pl.DataFrame) -> pl.DataFrame:
    """
    Total each damage measure per country and year, over every row of ``grid``.

    Parameters
    ----------
    events : DataFrame
        Events to total, already narrowed to whichever ones should count.
    grid : DataFrame
        The country-year panel from :func:`country_year_grid`.

    Returns
    -------
    DataFrame
        One row per country-year, one column per measure in ``DAMAGE_VARS``.
    """
    totals = (
        events.filter(pl.col("Disaster Type").is_in(DISASTER_TYPES))
        .select(INTENSITY_COLS)
        .group_by("ISO", "Start_Year")
        .agg(pl.col(name).sum().cast(COUNT_DTYPE) for name in DAMAGE_VARS)
    )

    return (
        grid.join(totals, on=["ISO", "Start_Year"], how="left")
        .select("ISO", "Start_Year", *DAMAGE_VARS, "Region", "Subregion")
        .sort("ISO", "Start_Year")
    )


def load_emdat_events(cache_dir: Path) -> pl.DataFrame:
    """
    Read the EM-DAT workbook, renamed and classified, with nothing filtered out.

    Narrow it with :func:`event_filter`, or with any other polars predicate.

    Parameters
    ----------
    cache_dir : Path
        Directory holding ``emdat.xlsx``.

    Returns
    -------
    DataFrame
        One row per recorded event, carrying ``emdat_index``, ``disaster_class`` and the renamed
        damage columns.

    Raises
    ------
    NotImplementedError
        If the workbook is absent. It is licensed and cannot be downloaded automatically.
    ValueError
        If the sheet is empty or its columns have changed.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    emdat_path = cache_dir / "emdat.xlsx"
    if not emdat_path.exists():
        raise NotImplementedError(
            f"No EM-DAT data was found at `{emdat_path}`. Please make an account at https://public.emdat.be/, "
            f"download the database, and place it at `{emdat_path}`"
        )

    return _read_workbook(emdat_path)


def event_filter(filters: EventFilters) -> pl.Expr:
    """
    Turn a place's thresholds into a predicate for :meth:`polars.DataFrame.filter`.

    Combine it with ``&`` to narrow further, such as to one country.

    Parameters
    ----------
    filters : EventFilters
        The window and severity thresholds an event has to clear.

    Returns
    -------
    Expr
        True for events that count. An event whose severity is unrecorded does not.
    """
    counts = (pl.col("Total_Affected") > filters.min_total_affected) & (
        pl.col("Start_Year") >= pl.date(filters.start_year, 1, 1)
    )

    if filters.end_year is not None:
        counts = counts & (pl.col("Start_Year") <= pl.date(filters.end_year, 12, 31))

    if filters.min_deaths is not None:
        counts = counts & (pl.col("Deaths") > filters.min_deaths)

    return counts
