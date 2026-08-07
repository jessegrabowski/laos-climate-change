import logging

from pathlib import Path

import polars as pl

from climate_risk.data.cache import cached, polars_parquet
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

ANCHOR_YEARS = (2015, 2020)
LAST_PROJECTED_YEAR = 2100


def transform_ipcc(scenarios: pl.DataFrame, co2_observations: pl.DataFrame) -> pl.DataFrame:
    """
    Turn five-yearly emission changes into annual levels, anchored on observed CO2.

    Parameters
    ----------
    scenarios : DataFrame
        Published changes, with a ``year`` column and one column per SSP scenario.
    co2_observations : DataFrame
        Observed CO2, with a dated ``year`` column and a ``co2`` column.

    Returns
    -------
    DataFrame
        One row per year from the anchor to ``LAST_PROJECTED_YEAR``, one column per scenario.
    """
    observed = co2_observations.select(pl.col("year").dt.year().alias("year"), "co2")
    scenario_names = [name for name in SCENARIO_COLUMNS.values() if name != "year"]

    anchor = ANCHOR_YEARS[-1]
    anchor_level = pl.col("co2").filter(pl.col("year") == anchor).first()

    def level(name: str) -> pl.Expr:
        # Each published row is a change from the one before, so a level is the anchor plus every
        # change since it. Years at or before the anchor contribute nothing to that running total.
        accumulated = pl.when(pl.col("year") > anchor).then(pl.col(f"{name}_change")).otherwise(0.0).cum_sum()

        return (
            pl.when(pl.col("year").is_in(ANCHOR_YEARS))
            .then(pl.col("co2"))
            .otherwise(anchor_level + accumulated)
            .alias(name)
        )

    published = (
        scenarios.join(observed, on="year", how="left")
        .sort("year")
        .rename({name: f"{name}_change" for name in scenario_names})
    )
    levels = published.with_columns(level(name) for name in scenario_names)

    every_year = pl.DataFrame({"year": range(anchor, LAST_PROJECTED_YEAR + 1)}, schema={"year": pl.Int64})

    return (
        every_year.join(levels, on="year", how="left")
        .sort("year")
        .with_columns(pl.exclude("year").interpolate())
        .drop("co2")
    )


def process_ipcc_scenarios(cache_dir: Path, *, force_reload: bool = False) -> pl.DataFrame:
    def build() -> pl.DataFrame:
        _log.info("Reading IPCC scenario emissions")
        published = pl.read_excel(IPCC_FILE, sheet_name=IPCC_SHEET)
        scenarios = published.select(pl.col(code).alias(name) for code, name in SCENARIO_COLUMNS.items())

        return transform_ipcc(scenarios, load_all_data(cache_dir)["df_time_series"].select("year", "co2"))

    return cached(cache_dir, "ipcc_scenarios", build, polars_parquet(), force=force_reload)
