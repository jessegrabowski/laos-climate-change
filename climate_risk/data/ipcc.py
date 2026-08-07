import logging

from pathlib import Path

import pandas as pd

from climate_risk.data.cache import cached, pandas_csv
from climate_risk.data_functions.combine_data import load_all_data

_log = logging.getLogger(__name__)

# SEDAC, which published this figure's data, was decommissioned in June 2025, so the workbook is
# redistributed with the package. Its licence and citation are in vendored/ATTRIBUTION.md.
IPCC_FILE = Path(__file__).parent / "vendored" / "ipcc_ar6_syr_csb2_fig1a.xlsx"

IPCC_SHEET = "CO2 Emissions"

SCENARIO_COLUMNS = {
    "Panel emissions - SSP1-19 - x (year)": "year",
    "Panel emissions - SSP1-19 - y": "SSP1-19",
    "Panel emissions - SSP1-26 - y": "SSP1-26",
    "Panel emissions - SSP2-45 - y": "SSP2-45",
    "Panel emissions - SSP3-70 - y": "SSP3-70",
    "Panel emissions - SSP5-85 - y": "SSP5-85",
}

# The published series is five-yearly, and each row is a change from the one before it.
SCENARIO_STEP_YEARS = 5
ANCHOR_YEARS = (2015, 2020)
LAST_PROJECTED_YEAR = 2100


def transform_ipcc(scenarios: pd.DataFrame, co2_observations: pd.DataFrame) -> pd.DataFrame:
    """
    Turn five-yearly emission changes into annual levels, anchored on observed CO2.

    Parameters
    ----------
    scenarios : DataFrame
        Published changes, with a ``year`` column and one column per SSP scenario.
    co2_observations : DataFrame
        Observed CO2 indexed by year-start timestamp, carrying a ``co2`` column.

    Returns
    -------
    DataFrame
        One row per year from the anchor to ``LAST_PROJECTED_YEAR``, one column per scenario.
    """
    observed = co2_observations.reset_index().assign(year=lambda x: x["year"].dt.year)
    levels = scenarios.merge(observed, on="year", how="left").set_index("year")

    scenario_names = [name for name in SCENARIO_COLUMNS.values() if name != "year"]
    levels = levels.rename(columns={name: f"{name}_change" for name in scenario_names})

    for name in scenario_names:
        for year in levels.index:
            if year in ANCHOR_YEARS:
                levels.loc[year, name] = levels.loc[year, "co2"]
            else:
                previous = levels.loc[year - SCENARIO_STEP_YEARS, name]
                levels.loc[year, name] = levels.loc[year, f"{name}_change"] + previous

    annual = levels.reindex(range(ANCHOR_YEARS[1], LAST_PROJECTED_YEAR + 1))

    return annual.interpolate(method="linear").drop(columns=["co2"])


def process_ipcc_scenarios(cache_dir: Path, *, force_reload: bool = False) -> pd.DataFrame:
    def build() -> pd.DataFrame:
        _log.info("Reading IPCC scenario emissions")
        published = pd.read_excel(IPCC_FILE, sheet_name=IPCC_SHEET)
        scenarios = published[list(SCENARIO_COLUMNS)].rename(columns=SCENARIO_COLUMNS)

        return transform_ipcc(scenarios, load_all_data(cache_dir)["df_time_series"][["co2"]])

    return cached(cache_dir, "ipcc_scenarios", build, pandas_csv(index_col="year"), force=force_reload)
