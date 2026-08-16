import logging

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

INDICATOR_NAMES = {
    "EN.POP.DNST": "population_density",
    "NY.GDP.PCAP.KD": "gdp_per_cap",
    "SP.POP.TOTL": "Population",
    "NY.GDP.MKTP.CD": "real_gdp",
    "AG.SRF.TOTL.K2": "surface_area_km2",
}

WB_INDICATORS = list(INDICATOR_NAMES)

# Earlier than any indicator's coverage, so the series starts wherever the data does.
FIRST_YEAR = 1900


def transform_world_bank(raw: pl.DataFrame) -> pl.DataFrame:
    """
    Key the World Bank indicators by ISO code and year, under their readable names.

    Parameters
    ----------
    raw : DataFrame
        Indicators as ``kuznets`` returns them tidy, with ``country`` and ``year`` columns.

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
            *(pl.col(code).alias(name) for code, name in INDICATOR_NAMES.items()),
        )
        .sort("country_code", "year")
    )


def load_wb_data(cache_dir: Path, *, force_reload: bool = False) -> pl.DataFrame:
    def build() -> pl.DataFrame:
        _log.info("Downloading World Bank indicators")
        downloaded = wb.download(
            indicator=WB_INDICATORS,
            country=REQUESTED_COUNTRY_CODES,
            start=FIRST_YEAR,
            end=None,
            output_type="polars",
        )
        if not isinstance(downloaded, pl.DataFrame):
            raise TypeError(f"kuznets returned a {type(downloaded).__name__} for output_type='polars'")

        return transform_world_bank(downloaded)

    return cached(cache_dir, "world_bank", build, polars_parquet(), force=force_reload)
