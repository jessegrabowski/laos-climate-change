import logging

from collections.abc import Mapping
from pathlib import Path

import polars as pl

from kuznets import wb

from climate_risk.data.cache import cached, polars_parquet

_log = logging.getLogger(__name__)

# Every country name the World Bank can return, its ISO code, and whether we ask for it. The rows
# it does not request are the Bank's regional and income aggregates, which are not countries.
COUNTRIES_FILE = Path(__file__).parent / "world_bank_countries.csv"


def _read_countries() -> tuple[dict[str, str], list[str]]:
    """Return the name-to-code mapping and the codes to download, read from ``COUNTRIES_FILE``."""
    table = pl.read_csv(COUNTRIES_FILE)

    return (
        dict(zip(table["country"], table["country_code"], strict=True)),
        table.filter("requested")["country_code"].to_list(),
    )


COUNTRY_CODE_BY_NAME, REQUESTED_COUNTRY_CODES = _read_countries()

# KD is constant 2015 US$. The CD variant carries inflation and the exchange rate.
INDICATOR_NAMES = {
    "EN.POP.DNST": "population_density",
    "NY.GDP.PCAP.KD": "gdp_per_cap",
    "SP.POP.TOTL": "Population",
    "NY.GDP.MKTP.KD": "real_gdp",
    "AG.SRF.TOTL.K2": "surface_area_km2",
}

WB_INDICATORS = list(INDICATOR_NAMES)

# Earlier than any indicator's coverage, so the series starts wherever the data does.
FIRST_YEAR = 1900


def transform_world_bank(raw: pl.DataFrame, indicator_names: Mapping[str, str]) -> pl.DataFrame:
    """
    Key the World Bank indicators by ISO code and year, under their readable names.

    Parameters
    ----------
    raw : DataFrame
        Indicators as ``kuznets`` returns them tidy, with ``country`` and ``year`` columns.
    indicator_names : mapping of str to str
        The indicator codes to keep, each mapped to the name it is stored under.

    Returns
    -------
    DataFrame
        One row per country and year, sorted, with an integer ``year``.
    """
    coded = raw.with_columns(pl.col("country").replace_strict(COUNTRY_CODE_BY_NAME, default=None).alias("country_code"))

    unmatched = sorted(set(coded.filter(pl.col("country_code").is_null())["country"].to_list()))
    if unmatched:
        _log.warning(f"Dropping {len(unmatched)} countries with no ISO code: {', '.join(unmatched)}")

    return (
        coded.drop_nulls("country_code")
        .select(
            "country_code",
            # Upstream dates the year. dt.year() narrows it to Int32, and a join key that changes
            # width is a join that stops matching.
            pl.col("year").dt.year().cast(pl.Int64),
            *(pl.col(code).alias(name) for code, name in indicator_names.items()),
        )
        .sort("country_code", "year")
    )


def _load_indicators(
    cache_dir: Path,
    name: str,
    indicator_names: Mapping[str, str],
    *,
    force_reload: bool,
) -> pl.DataFrame:
    """Download ``indicator_names`` for every requested country and cache the panel under ``name``."""

    def build() -> pl.DataFrame:
        _log.info(f"Downloading {len(indicator_names)} World Bank indicators for {name}")
        downloaded = wb.download(
            indicator=list(indicator_names),
            country=REQUESTED_COUNTRY_CODES,
            start=FIRST_YEAR,
            end=None,
            output_type="polars",
        )
        if not isinstance(downloaded, pl.DataFrame):
            raise TypeError(f"kuznets returned a {type(downloaded).__name__} for output_type='polars'")

        return transform_world_bank(downloaded, indicator_names)

    return cached(cache_dir, name, build, polars_parquet(), force=force_reload)


def load_wb_data(cache_dir: Path, *, force_reload: bool = False) -> pl.DataFrame:
    """Return the population, area and output panel, one row per country and year."""
    return _load_indicators(cache_dir, "world_bank", INDICATOR_NAMES, force_reload=force_reload)
