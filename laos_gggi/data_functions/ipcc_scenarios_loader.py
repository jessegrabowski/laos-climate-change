from pyprojroot import here
import pandas as pd
import os
from os.path import exists
import logging
from laos_gggi.const_vars import (
    RCMIP_URL,
    IPCC_SSP_SCENARIOS,
    IPCC_SSP_COLUMN_NAMES,
    IPCC_CACHED_FILENAME,
)

_log = logging.getLogger(__name__)


def process_ipcc_scenarios(data_path=None, force_reload: bool = False):
    """Load SSP atmospheric CO2 concentration scenarios from the RCMIP dataset.

    Downloads annual-mean CO2 concentration data from the RCMIP dataset (Zenodo)
    for the five core SSP scenarios.

    Returns a DataFrame indexed by year (2015-2100) with columns for each SSP
    scenario containing atmospheric CO2 concentration in ppm.
    """
    if data_path is None:
        data_path = here("data")
    if not exists(data_path):
        os.makedirs(data_path)

    cached_path = os.path.join(data_path, IPCC_CACHED_FILENAME)

    if os.path.isfile(cached_path) and not force_reload:
        _log.info("Loading cached IPCC SSP CO2 concentration data")
        return pd.read_csv(cached_path, index_col="year")

    _log.info("Downloading RCMIP CO2 concentration data from Zenodo")
    raw = pd.read_csv(RCMIP_URL)

    # Filter to atmospheric CO2 concentration for the target scenarios (global)
    mask = (
        (raw["Variable"] == "Atmospheric Concentrations|CO2")
        & (raw["Scenario"].isin(IPCC_SSP_SCENARIOS))
        & (raw["Region"] == "World")
    )
    co2 = raw.loc[mask].copy()

    # Pivot: year columns are strings like "2015", "2016", ...
    year_cols = [c for c in co2.columns if c.isdigit()]
    co2 = co2.set_index("Scenario")[year_cols].T
    co2.index = co2.index.astype(int)
    co2.index.name = "year"

    # Rename columns from scenario codes to display names
    co2 = co2.rename(columns=IPCC_SSP_COLUMN_NAMES)

    # Keep 2015-2100
    df = co2.loc[(co2.index >= 2015) & (co2.index <= 2100)]

    # Cache locally
    df.to_csv(cached_path)
    _log.info(f"Cached IPCC SSP data to {cached_path}")

    return df
