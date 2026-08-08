from functools import partial, reduce
from pathlib import Path

import pandas as pd
import polars as pl

from climate_risk.data.co2 import load_co2_data
from climate_risk.data.gpcc import load_gpcc_data
from climate_risk.data.ocean_heat import load_ocean_heat_data
from climate_risk.data.world_bank import load_wb_data
from climate_risk.data_functions.emdat_processing import DISASTER_TYPES, load_emdat_data

# The panel is keyed on the EM-DAT column names, which the other sources are renamed onto.
PANEL_KEY = ["ISO", "Start_Year"]
SERIES_KEY = "year"


def _as_polars(frame: pd.DataFrame) -> pl.DataFrame:
    """Convert a pandas frame from the geospatial layer into the polars this module merges in."""
    return pl.from_pandas(frame.reset_index())


def _outer_join(left: pl.DataFrame, right: pl.DataFrame, on: list[str] | str) -> pl.DataFrame:
    """Join keeping every key from both sides, with the key columns merged rather than suffixed."""
    return left.join(right, on=on, how="full", coalesce=True)


def _suffixed_damage(damage: pl.DataFrame, suffix: str) -> pl.DataFrame:
    """Tag one disaster class's damage columns so both classes can sit in one frame."""
    measures = [column for column in damage.columns if column not in {*PANEL_KEY, "Region", "Subregion"}]

    return damage.select(*PANEL_KEY, *(pl.col(name).alias(f"{name}_{suffix}") for name in measures))


def _combine_emdat(emdat: dict[str, pl.DataFrame]) -> dict[str, pl.DataFrame]:
    """Split EM-DAT into events and damages, with the hydrological and climatological classes joined on."""
    hydro = _suffixed_damage(emdat["df_inten_filtered_adjusted_hydro"], "hydro")
    clim = _suffixed_damage(emdat["df_inten_filtered_adjusted_clim"], "clim")

    damage = emdat["df_inten_filtered_adjusted"]
    for tagged in (hydro, clim):
        damage = damage.join(tagged, on=PANEL_KEY, how="left")

    return {
        "emdat_events": emdat["df_prob_filtered_adjusted"].drop("Subregion"),
        "emdat_damage": damage,
        "emdat_damage_hydro": emdat["df_inten_filtered_adjusted_hydro"],
        "emdat_damage_clim": emdat["df_inten_filtered_adjusted_clim"],
        "df_inten_filtered_adjusted_hydro": hydro,
        "df_inten_filtered_adjusted_clim": clim,
    }


def _shape_world_bank(indicators: pl.DataFrame) -> pl.DataFrame:
    """Rename the World Bank columns onto the panel's key and date its years."""
    return indicators.select(
        pl.col("country_code").alias("ISO"),
        pl.date(pl.col("year"), 1, 1).alias("Start_Year"),
        pl.exclude("country_code", "year"),
    )


def _annual_precipitation(gpcc: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Total monthly precipitation to years.

    Returns
    -------
    by_country : DataFrame
        One row per country and year.
    worldwide : DataFrame
        One row per year, summed across countries.
    """
    dated = gpcc.select(
        pl.col("country_code").alias("ISO"),
        pl.date(pl.col("time").dt.year(), 1, 1).alias(SERIES_KEY),
        "precip",
    )

    return (
        dated.group_by("ISO", SERIES_KEY).agg(pl.col("precip").sum()).sort("ISO", SERIES_KEY),
        dated.group_by(SERIES_KEY).agg(pl.col("precip").sum()).sort(SERIES_KEY),
    )


def _keyed_by_year(series: pl.DataFrame) -> pl.DataFrame:
    """Re-key an annual series onto the panel's year column. Both loaders date theirs to a year start."""
    return series.rename({"Date": SERIES_KEY}).sort(SERIES_KEY)


def _countries_in_common(*frames: pl.DataFrame) -> set[str]:
    """Return the ISO codes present in every frame."""
    return set.intersection(*(set(frame["ISO"].unique().to_list()) for frame in frames))


def _only_countries(frame: pl.DataFrame, codes: set[str]) -> pl.DataFrame:
    return frame.filter(pl.col("ISO").is_in(codes))


def _country_constants(events: pl.DataFrame) -> pl.DataFrame:
    """Reduce the events to the columns that do not vary within a country."""
    varies_by_year = {*DISASTER_TYPES, "Start_Year"}
    constant_columns = [column for column in events.columns if column not in varies_by_year]

    return events.select(constant_columns).unique().sort("ISO")


def load_all_data(cache_dir: Path) -> dict[str, pl.DataFrame]:
    emdat = load_emdat_data(cache_dir)
    merged_dict = _combine_emdat(emdat)

    merged_dict["wb_data"] = _shape_world_bank(load_wb_data(cache_dir))
    merged_dict["gpcc"], merged_dict["gpcc_agg"] = _annual_precipitation(_as_polars(load_gpcc_data(cache_dir)))
    merged_dict["co2"] = _keyed_by_year(load_co2_data(cache_dir))
    merged_dict["ocean_temperature"] = _keyed_by_year(load_ocean_heat_data(cache_dir))

    # A country needs both a disaster record and development indicators to earn a row in the panel.
    common = _countries_in_common(merged_dict["emdat_damage"], merged_dict["wb_data"])
    merged_dict["emdat_damage"] = _only_countries(merged_dict["emdat_damage"], common)
    merged_dict["emdat_events"] = _only_countries(merged_dict["emdat_events"], common).drop("Region")
    merged_dict["wb_data"] = _only_countries(merged_dict["wb_data"], common)

    with_precipitation = _countries_in_common(merged_dict["wb_data"], merged_dict["gpcc"])
    merged_dict["gpcc"] = _only_countries(merged_dict["gpcc"], with_precipitation)

    merged_dict["country_constants"] = _country_constants(emdat["df_prob_filtered_adjusted"])

    merged_dict["df_panel"] = reduce(
        partial(_outer_join, on=PANEL_KEY),
        [
            merged_dict["emdat_events"],
            merged_dict["emdat_damage"],
            merged_dict["wb_data"],
            merged_dict["gpcc"].rename({SERIES_KEY: "Start_Year"}),
        ],
    ).sort(PANEL_KEY)

    merged_dict["df_time_series"] = reduce(
        partial(_outer_join, on=SERIES_KEY),
        [merged_dict["co2"], merged_dict["ocean_temperature"], merged_dict["gpcc_agg"]],
    ).sort(SERIES_KEY)

    return merged_dict
