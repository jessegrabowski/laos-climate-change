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

# "Hydrometereological" is the wire value written by this processing and queried downstream.
DISASTER_CLASSES = {
    "Storm": "Hydrometereological",
    "Flood": "Hydrometereological",
    "Mass movement (wet)": "Hydrometereological",
    "Wildfire": "Climatological",
    "Extreme temperature": "Climatological",
    "Drought": "Climatological",
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


def _country_years(events: pl.DataFrame, window_start: dt.date) -> pl.DataFrame:
    """Every country crossed with every year in the window, which is the grid all panels are laid on."""
    newest_event = events["Start_Year"].max()
    if not isinstance(newest_event, dt.date):
        raise ValueError("Every Start_Year in the workbook is missing, so the window has no end.")

    if window_start > newest_event:
        raise ValueError(
            f"window_start={window_start} is after the newest event in the workbook "
            f"({newest_event}), so every output frame would be empty."
        )

    years: pl.Series = pl.date_range(window_start, newest_event, interval="1y", eager=True)

    return (
        events.select(pl.col("ISO").unique())
        .join(years.alias("Start_Year").to_frame(), how="cross")
        .sort("ISO", "Start_Year")
    )


def _regions(events: pl.DataFrame) -> pl.DataFrame:
    """One row per country carrying its region and subregion."""
    return events.select("ISO", "Region", "Subregion").unique(subset="ISO", keep="first")


def _count_by_type(events: pl.DataFrame, grid: pl.DataFrame, regions: pl.DataFrame) -> pl.DataFrame:
    """Count events per country, year and disaster type, over the full grid."""
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
        .join(regions, on="ISO", how="left")
        .select("ISO", "Start_Year", "Region", "Subregion", *DISASTER_TYPES)
        .sort("ISO", "Start_Year")
    )


def _damage_totals(events: pl.DataFrame, grid: pl.DataFrame, regions: pl.DataFrame) -> pl.DataFrame:
    """Total each damage measure per country and year, over the full grid."""
    totals = (
        events.filter(pl.col("Disaster Type").is_in(DISASTER_TYPES))
        .select(INTENSITY_COLS)
        .group_by("ISO", "Start_Year")
        .agg(pl.col(name).sum().cast(COUNT_DTYPE) for name in DAMAGE_VARS)
    )

    return (
        grid.join(totals, on=["ISO", "Start_Year"], how="left")
        .join(regions, on="ISO", how="left")
        .select("ISO", "Start_Year", *DAMAGE_VARS, "Region", "Subregion")
        .sort("ISO", "Start_Year")
    )


def _selected_events(events: pl.DataFrame, filters: EventFilters) -> pl.DataFrame:
    """Keep the events a place's thresholds count, dropping any whose severity is unrecorded."""
    selected = events.filter(
        (pl.col("Total_Affected") > filters.min_total_affected)
        & (pl.col("Start_Year") >= pl.date(filters.start_year, 1, 1))
    )

    if filters.end_year is not None:
        selected = selected.filter(pl.col("Start_Year") <= pl.date(filters.end_year, 12, 31))

    if filters.min_deaths is not None:
        selected = selected.filter(pl.col("Deaths") > filters.min_deaths)

    return selected


def load_emdat_data(
    cache_dir: Path,
    *,
    window_start: dt.date = EMDAT_WINDOW_START,
    filters: EventFilters | None = None,
) -> dict[str, pl.DataFrame]:
    cache_dir.mkdir(parents=True, exist_ok=True)

    emdat_path = cache_dir / "emdat.xlsx"
    if not emdat_path.exists():
        raise NotImplementedError(
            f"No EM-DAT data was found at `{emdat_path}`. Please make an account at https://public.emdat.be/, "
            f"download the database, and place it at `{emdat_path}`"
        )

    df_raw = _read_workbook(emdat_path)

    # The two filtered views are what the published panel is built from; the unfiltered one is
    # kept because the severity thresholds are a modelling choice, not a data-quality one.
    df_raw_filtered = df_raw.filter(
        (pl.col("Total_Affected") > 1000) & (pl.col("Deaths") > 100) & (pl.col("Start_Year") > dt.date(1970, 1, 1))
    )
    df_raw_filtered_adj = _selected_events(df_raw, EventFilters() if filters is None else filters)

    grid = _country_years(df_raw, window_start)
    regions = _regions(df_raw)

    return {
        "df_raw": df_raw,
        "df_raw_filtered": df_raw_filtered,
        "df_raw_filtered_adj": df_raw_filtered_adj,
        "df_prob_unfiltered": _count_by_type(df_raw, grid, regions),
        "df_prob_filtered": _count_by_type(df_raw_filtered, grid, regions),
        "df_prob_filtered_adjusted": _count_by_type(df_raw_filtered_adj, grid, regions),
        "df_inten_unfiltered": _damage_totals(df_raw, grid, regions),
        "df_inten_filtered": _damage_totals(df_raw_filtered, grid, regions),
        "df_inten_filtered_adjusted": _damage_totals(df_raw_filtered_adj, grid, regions),
        "df_inten_filtered_adjusted_hydro": _damage_totals(
            df_raw_filtered_adj.filter(pl.col("disaster_class") == "Hydrometereological"), grid, regions
        ),
        "df_inten_filtered_adjusted_clim": _damage_totals(
            df_raw_filtered_adj.filter(pl.col("disaster_class") == "Climatological"), grid, regions
        ),
    }
