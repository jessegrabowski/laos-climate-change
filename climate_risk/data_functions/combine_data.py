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
PANEL_INDEX = ["ISO", "Start_Year"]

_merge_on_index = partial(pd.merge, left_index=True, right_index=True, how="outer")


def _as_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    """Convert a tidy polars frame from the data layer into the pandas this module merges in."""
    return frame.to_pandas()


def _panel_indexed(frame: pl.DataFrame) -> pd.DataFrame:
    """Convert an EM-DAT frame and key it the way the merge chain expects."""
    return frame.to_pandas().set_index(PANEL_INDEX)


def _suffixed_damage(damage: pd.DataFrame, suffix: str) -> pd.DataFrame:
    """Tag one disaster class's damage columns so both classes can sit in one frame."""
    return damage.drop(columns=["Region", "Subregion"]).rename(columns=lambda name: f"{name}_{suffix}")


def _combine_emdat(emdat: dict[str, pl.DataFrame]) -> dict[str, pd.DataFrame]:
    """Split EM-DAT into events and damages, with the hydrological and climatological classes joined on."""
    hydro = _suffixed_damage(_panel_indexed(emdat["df_inten_filtered_adjusted_hydro"]), "hydro")
    clim = _suffixed_damage(_panel_indexed(emdat["df_inten_filtered_adjusted_clim"]), "clim")

    damage = _panel_indexed(emdat["df_inten_filtered_adjusted"])
    for tagged in (hydro, clim):
        damage = pd.merge(damage, tagged, left_index=True, right_index=True, how="left")

    return {
        "emdat_events": _panel_indexed(emdat["df_prob_filtered_adjusted"]).drop(columns=["Subregion"]),
        "emdat_damage": damage,
        "emdat_damage_hydro": _panel_indexed(emdat["df_inten_filtered_adjusted_hydro"]),
        "emdat_damage_clim": _panel_indexed(emdat["df_inten_filtered_adjusted_clim"]),
        "df_inten_filtered_adjusted_hydro": hydro,
        "df_inten_filtered_adjusted_clim": clim,
    }


def _shape_world_bank(indicators: pd.DataFrame) -> pd.DataFrame:
    """Rename the World Bank columns onto the panel's index and date its years."""
    return (
        indicators.rename(columns={"country_code": "ISO", "year": "Start_Year"})
        .assign(Start_Year=lambda x: pd.to_datetime(x.Start_Year, format="%Y"))
        .set_index(PANEL_INDEX)
    )


def _annual_precipitation(gpcc: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Total monthly precipitation to years.

    Returns
    -------
    by_country : DataFrame
        One row per country and year.
    worldwide : DataFrame
        One row per year, summed across countries.
    """
    dated = gpcc.reset_index().rename(columns={"country_code": "ISO"})
    dated["year"] = pd.to_datetime(pd.to_datetime(dated["time"]).dt.year, format="%Y")

    return (
        dated.pivot_table(values="precip", index=["ISO", "year"], aggfunc="sum"),
        dated.pivot_table(values="precip", index=["year"], aggfunc="sum"),
    )


def _annual_co2(co2: pd.DataFrame) -> pd.DataFrame:
    """Key the observed CO2 by a year-start timestamp."""
    dated = co2.assign(year=lambda x: pd.to_datetime(x["Date"].dt.year, format="%Y"))

    return dated.pivot_table(values="co2", index="year", aggfunc="sum")


def _annual_ocean_heat(ocean_heat: pd.DataFrame) -> pd.DataFrame:
    """Average the ocean-heat anomalies to years, keyed by a year-start timestamp."""
    annual = ocean_heat.assign(year=lambda x: x["Date"].dt.year).pivot_table(
        values="Temp", index="year", aggfunc="mean"
    )
    annual.index = pd.to_datetime(annual.index, format="%Y")

    return annual


def _countries_in_common(*frames: pd.DataFrame) -> set[str]:
    """Return the ISO codes present in the first index level of every frame."""
    return set.intersection(*(set(frame.index.get_level_values(0).unique()) for frame in frames))


def _only_countries(frame: pd.DataFrame, codes: set[str]) -> pd.DataFrame:
    return frame.loc[lambda x: x.index.get_level_values(0).isin(codes)].copy()


def _country_constants(events: pd.DataFrame) -> pd.DataFrame:
    """Reduce the events to the columns that do not vary within a country."""
    flat = events.reset_index()
    varies_by_year = {*DISASTER_TYPES, "Start_Year"}
    constant_columns = [column for column in flat.columns if column not in varies_by_year]

    return flat[constant_columns].drop_duplicates().set_index("ISO")


def load_all_data(cache_dir: Path) -> dict[str, pd.DataFrame]:
    emdat = load_emdat_data(cache_dir)
    merged_dict = _combine_emdat(emdat)

    merged_dict["wb_data"] = _shape_world_bank(_as_pandas(load_wb_data(cache_dir)))
    merged_dict["gpcc"], merged_dict["gpcc_agg"] = _annual_precipitation(load_gpcc_data(cache_dir))
    merged_dict["co2"] = _annual_co2(_as_pandas(load_co2_data(cache_dir)))
    merged_dict["ocean_temperature"] = _annual_ocean_heat(_as_pandas(load_ocean_heat_data(cache_dir)))

    # A country needs both a disaster record and development indicators to earn a row in the panel.
    common = _countries_in_common(merged_dict["emdat_damage"], merged_dict["wb_data"])
    merged_dict["emdat_damage"] = _only_countries(merged_dict["emdat_damage"], common)
    merged_dict["emdat_events"] = _only_countries(merged_dict["emdat_events"], common).drop(columns=["Region"])
    merged_dict["wb_data"] = _only_countries(merged_dict["wb_data"], common)

    with_precipitation = _countries_in_common(merged_dict["wb_data"], merged_dict["gpcc"])
    merged_dict["gpcc"] = _only_countries(merged_dict["gpcc"], with_precipitation)

    merged_dict["country_constants"] = _country_constants(_panel_indexed(emdat["df_prob_filtered_adjusted"]))

    merged_dict["df_panel"] = reduce(
        _merge_on_index,
        [
            merged_dict["emdat_events"],
            merged_dict["emdat_damage"],
            merged_dict["wb_data"],
            merged_dict["gpcc"].reset_index().rename(columns={"year": "Start_Year"}).set_index(PANEL_INDEX),
        ],
    )

    merged_dict["df_time_series"] = reduce(
        _merge_on_index,
        [merged_dict["co2"], merged_dict["ocean_temperature"], merged_dict["gpcc_agg"]],
    )

    return merged_dict
