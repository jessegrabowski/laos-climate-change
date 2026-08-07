import logging

from pathlib import Path

import pandas as pd

from kuznets import wb

from climate_risk.data.cache import cached, pandas_parquet

_log = logging.getLogger(__name__)

# Every country name the World Bank can return, its ISO code, and whether we ask for it. The rows
# it does not request are the Bank's regional and income aggregates, which are not countries.
COUNTRIES_FILE = Path(__file__).parent / "world_bank_countries.csv"


def _read_countries() -> tuple[dict[str, str], list[str]]:
    """Return the name-to-code mapping and the codes to download, read from ``COUNTRIES_FILE``."""
    table = pd.read_csv(COUNTRIES_FILE)

    return (
        dict(zip(table["country"], table["country_code"], strict=True)),
        table.loc[table["requested"], "country_code"].tolist(),
    )


COUNTRY_CODE_BY_NAME, REQUESTED_COUNTRY_CODES = _read_countries()

WB_INDICATORS = [
    "EN.POP.DNST",
    "NY.GDP.PCAP.KD",
    "SP.POP.TOTL",
    "NY.GDP.MKTP.CD",
    "AG.SRF.TOTL.K2",
]

INDICATOR_NAMES = {
    "EN.POP.DNST": "population_density",
    "NY.GDP.PCAP.KD": "gdp_per_cap",
    "SP.POP.TOTL": "Population",
    "NY.GDP.MKTP.CD": "real_gdp",
    "AG.SRF.TOTL.K2": "surface_area_km2",
}

# Earlier than any indicator's coverage, so the series starts wherever the data does.
FIRST_YEAR = 1900

# kuznets validates against a 2014-era code list that predates XKX, which this project uses on
# purpose. Warnings are errors in the suite, and the code is correct, so the check is turned off.
COUNTRY_CODE_ERRORS = "ignore"


def transform_world_bank(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Key the World Bank indicators by ISO code and year, under their readable names.

    Parameters
    ----------
    raw : DataFrame
        Indicators as ``kuznets`` returns them, indexed by ``country`` name and ``year``.

    Returns
    -------
    DataFrame
        One row per country and year, indexed by ``country_code`` and an integer ``year``.
    """
    coded = raw.reset_index().assign(country_code=lambda x: x["country"].map(COUNTRY_CODE_BY_NAME))
    matched = coded["country_code"].notna()

    unmatched = sorted(set(coded.loc[~matched, "country"]))
    if unmatched:
        _log.warning(f"Dropping {len(unmatched)} countries with no ISO code: {', '.join(unmatched)}")

    return (
        coded[matched][["country_code", "year", *WB_INDICATORS]]
        .rename(columns=INDICATOR_NAMES)
        # Upstream serves the year as a string; the cache reads it back as an integer.
        .astype({"year": int})
        .set_index(["country_code", "year"])
        .sort_index()
    )


def load_wb_data(cache_dir: Path, *, force_reload: bool = False) -> pd.DataFrame:
    def build() -> pd.DataFrame:
        _log.info("Downloading World Bank indicators")
        downloaded: pd.DataFrame = wb.download(
            indicator=WB_INDICATORS,
            country=REQUESTED_COUNTRY_CODES,
            start=FIRST_YEAR,
            end=None,
            errors=COUNTRY_CODE_ERRORS,
        )

        return transform_world_bank(downloaded)

    return cached(
        cache_dir,
        "world_bank",
        build,
        pandas_parquet(),
        force=force_reload,
    )
