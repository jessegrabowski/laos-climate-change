import datetime as dt
import json

from pathlib import Path

import polars as pl

from climate_risk.config.schema import EventFilters
from climate_risk.data.source import ManualSource

# EM-DAT requires an account and forbids redistribution, so it is fetched by a person, not by code.
EMDAT = ManualSource(
    filename="emdat.xlsx",
    homepage="https://public.emdat.be/",
    licence=(
        "Free for non-commercial use with attribution. Redistribution of the database is not "
        "permitted; users must download it themselves after registering."
    ),
    citation=(
        "EM-DAT, CRED / UCLouvain, Brussels, Belgium. Delforge, D. et al. (2025), EM-DAT: the "
        "Emergency Events Database. International Journal of Disaster Risk Reduction 124, 105509. "
        "https://doi.org/10.1016/j.ijdrr.2025.105509"
    ),
    retrieved="2026-08-03",
)

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
REQUIRED_EMDAT_COLUMNS = {"ISO", "Region", "Subregion", "Disaster Type", "GADM Admin Units"} | set(EM_DAT_COL_DICT)

# EM-DAT writes empty strings, not blank cells: undeclared, a cost column reads as text and an
# all-empty text column warns.
EMDAT_DTYPES = {
    "AID Contribution ('000 US$)": "float",
    "Reconstruction Costs ('000 US$)": "float",
    "Reconstruction Costs, Adjusted ('000 US$)": "float",
    "Admin Units": "string",
    "GADM Admin Units": "string",
}

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
    workbook = pl.read_excel(
        emdat_path,
        sheet_name="EM-DAT Data",
        raise_if_empty=False,
        read_options={"dtypes": EMDAT_DTYPES},
    )

    if workbook.is_empty():
        raise ValueError(f"The `EM-DAT Data` sheet in `{emdat_path}` has no rows.")

    missing_columns = REQUIRED_EMDAT_COLUMNS - set(workbook.columns)
    if missing_columns:
        raise ValueError(
            f"The `EM-DAT Data` sheet in `{emdat_path}` is missing {sorted(missing_columns)}. "
            f"Re-download the database, or update EM_DAT_COL_DICT if the export has changed."
        )

    return workbook.rename(EM_DAT_COL_DICT).with_columns(
        pl.date(pl.col("Start_Year"), 1, 1).alias("Start_Year"),
        pl.col("Disaster Type").replace_strict(DISASTER_CLASSES, default=None).alias("disaster_class"),
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
        One row per recorded event, keyed by ``DisNo.``, carrying ``disaster_class`` and the renamed
        damage columns.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    return _read_workbook(EMDAT.require(cache_dir))


GADM_UNITS_COLUMN = "GADM Admin Units"

# One row per affected administrative unit. `name` and `migration_method` are absent on some units:
# EM-DAT omits the name where GADM has none, and the method where the unit was never migrated.
EVENT_UNIT_SCHEMA = {
    "DisNo.": pl.String,
    "gid": pl.String,
    "name": pl.String,
    "admin_level": pl.Int8,
    "migration_method": pl.String,
}


def event_units(events: pl.DataFrame) -> pl.DataFrame:
    """
    Explode each event's GADM administrative units into one row per event-unit.

    The level comes from the key EM-DAT files a unit under, ``gid_1`` or ``gid_2``, because a GADM
    identifier does not reliably state it: Ghana's are numbered ``GHA11_2`` and ``GHA7.13_2``.

    Parameters
    ----------
    events : DataFrame
        The workbook, as :func:`load_emdat_events` returns it.

    Returns
    -------
    DataFrame
        ``DisNo.``, ``gid``, ``name``, ``admin_level`` and ``migration_method``. An event carrying no
        units contributes no rows, so this is narrower than ``events``.
    """
    rows = []

    for disno, raw in zip(events["DisNo."], events[GADM_UNITS_COLUMN], strict=True):
        if not str(raw or "").strip():
            continue

        for unit in json.loads(raw):
            level = 2 if "gid_2" in unit else 1
            if f"gid_{level}" not in unit:
                raise ValueError(f"{disno}: an administrative unit carries no gid_1 or gid_2: {unit}")

            rows.append(
                {
                    "DisNo.": disno,
                    "gid": unit[f"gid_{level}"],
                    "name": unit.get(f"name_{level}"),
                    "admin_level": level,
                    "migration_method": unit.get("migration_method"),
                }
            )

    return pl.DataFrame(rows, schema=EVENT_UNIT_SCHEMA)


# Where an event's geometry comes from, best first. Nothing is filtered on this: the column records
# what the source holds, and a model chooses which tiers it will accept.
GEOMETRY_SOURCES = ("gadm", "geo_disasters", "emdat_point", "country")

EVENT_GEOGRAPHY_COLUMNS = (
    "DisNo.",
    "ISO",
    "geometry_source",
    "gid",
    "name",
    "admin_level",
    "migration_method",
    "Latitude",
    "Longitude",
)


def event_geography(events: pl.DataFrame) -> pl.DataFrame:
    """
    Say where every event's geometry comes from, one row per event-unit and one per event otherwise.

    An event coded to administrative units contributes a row per unit; one with only a coordinate,
    or with nothing, contributes a single row. Every event in ``events`` appears, so an absence of
    geography is stated rather than implied by a missing row.

    ``Latitude`` and ``Longitude`` are carried wherever EM-DAT supplies them, including on ``gadm``
    rows, so the two claims stay visible side by side rather than one being discarded.

    Parameters
    ----------
    events : DataFrame
        The workbook, as :func:`load_emdat_events` returns it.

    Returns
    -------
    DataFrame
        ``DisNo.``, ``ISO``, ``geometry_source`` from ``GEOMETRY_SOURCES``, the unit columns of
        :func:`event_units` where one applies, and the event's coordinate where it has one.
    """
    units = event_units(events)
    located = events.select("DisNo.", "ISO", "Latitude", "Longitude")

    from_units = units.join(located, on="DisNo.", how="left").with_columns(pl.lit("gadm").alias("geometry_source"))

    rest = located.join(units.select("DisNo.").unique(), on="DisNo.", how="anti").with_columns(
        pl.when(pl.col("Latitude").is_not_null())
        .then(pl.lit("emdat_point"))
        .otherwise(pl.lit("country"))
        .alias("geometry_source"),
        pl.lit(None, dtype=pl.String).alias("gid"),
        pl.lit(None, dtype=pl.String).alias("name"),
        pl.lit(None, dtype=pl.Int8).alias("admin_level"),
        pl.lit(None, dtype=pl.String).alias("migration_method"),
    )

    return pl.concat([from_units.select(EVENT_GEOGRAPHY_COLUMNS), rest.select(EVENT_GEOGRAPHY_COLUMNS)]).sort(
        "DisNo.", "gid", nulls_last=True
    )


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
