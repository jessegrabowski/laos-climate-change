import logging

from pathlib import Path

import pandas as pd

from kuznets import wb

from climate_risk.const_vars import COUNTRIES_ISO, ISO_DICTIONARY
from climate_risk.data.cache import cached, pandas_csv

_log = logging.getLogger(__name__)

WB_INDICATORS = [
    "EN.POP.DNST",
    "NY.GDP.PCAP.KD",
    "SP.POP.TOTL",
    "NY.GDP.MKTP.CD",
    "AG.SRF.TOTL.K2",
]

WB_RENAME_DICT = {
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
    coded = raw.reset_index().assign(country_code=lambda x: x["country"].map(ISO_DICTIONARY))
    known = coded.dropna(subset=["country_code"])

    unmatched = sorted(set(coded.loc[coded["country_code"].isna(), "country"]))
    if unmatched:
        _log.warning(f"Dropping {len(unmatched)} countries with no ISO code: {', '.join(unmatched)}")

    return (
        known[["country_code", "year", *WB_INDICATORS]]
        .rename(columns=WB_RENAME_DICT)
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
            country=COUNTRIES_ISO,
            start=FIRST_YEAR,
            end=None,
            errors=COUNTRY_CODE_ERRORS,
        )

        return transform_world_bank(downloaded)

    return cached(
        cache_dir,
        "world_bank",
        build,
        pandas_csv(index_col=["country_code", "year"]),
        force=force_reload,
    )
