import logging

from collections.abc import Mapping
from pathlib import Path

import polars as pl

from kuznets import wb

from climate_risk.data.cache import builder_fingerprint, cached, polars_parquet
from climate_risk.data.source import ApiSource

_log = logging.getLogger(__name__)

WORLD_BANK = ApiSource(
    url="https://api.worldbank.org/v2/country",
    licence="CC BY 4.0",
    citation=(
        "World Bank, World Development Indicators, https://databank.worldbank.org/source/world-development-indicators."
    ),
    retrieved="2026-09-05",
)

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

# The national accounts, prices, rates and fiscal aggregates the small open economy model is
# estimated on. KN is constant local currency, so the ratios the model forms within a country share
# one unit. The KD variant converts at a market exchange rate.
MACRO_INDICATOR_NAMES = {
    "NY.GDP.MKTP.KN": "real_gdp_lcu",
    "NE.CON.PRVT.KN": "real_consumption_lcu",
    "NE.GDI.FTOT.KN": "real_investment_lcu",
    "NE.CON.GOVT.KN": "real_government_lcu",
    "NE.EXP.GNFS.KN": "real_exports_lcu",
    "NE.IMP.GNFS.KN": "real_imports_lcu",
    # Paired with the constant-price series above, these give consumption and investment deflators,
    # which is what carries import prices when no import price index is available.
    "NE.CON.PRVT.CN": "nominal_consumption",
    "NE.GDI.FTOT.CN": "nominal_investment",
    # Model quantities are per capita.
    "SP.POP.TOTL": "population",
    "FP.CPI.TOTL": "cpi",
    "NY.GDP.DEFL.ZS": "gdp_deflator",
    "PA.NUS.FCRF": "exchange_rate",
    "FR.INR.LEND": "lending_rate",
    "FR.INR.DPST": "deposit_rate",
    "TM.TAX.MRCH.WM.AR.ZS": "import_tariff",
    "DT.DOD.DECT.CD": "external_debt",
    "BN.CAB.XOKA.GD.ZS": "current_account_gdp",
    "SL.EMP.TOTL.SP.ZS": "employment_rate",
    "GC.TAX.TOTL.GD.ZS": "tax_revenue_gdp",
    "GC.XPN.TOTL.GD.ZS": "government_expense_gdp",
}

WB_MACRO_INDICATORS = list(MACRO_INDICATOR_NAMES)

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
    # kuznets warns rather than raising when the Bank rejects a code, and omits the column entirely.
    missing = sorted(set(indicator_names) - set(raw.columns))
    if missing:
        raise ValueError(f"The World Bank returned no column for {missing}; the codes may have been retired.")

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
    """
    Download ``indicator_names`` for every requested country and cache the panel under ``name``.

    The entry is keyed on how it was built as well as on ``name``, so that editing
    ``indicator_names`` turns it over instead of reading back what an earlier set produced.
    """

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

    return cached(
        cache_dir,
        name,
        build,
        polars_parquet(),
        params={"reading": builder_fingerprint(build, indicator_names)},
        force=force_reload,
    )


def load_wb_data(cache_dir: Path, *, force_reload: bool = False) -> pl.DataFrame:
    """Return the population, area and output panel, one row per country and year."""
    return _load_indicators(cache_dir, "world_bank", INDICATOR_NAMES, force_reload=force_reload)


def load_wb_macro_data(cache_dir: Path, *, force_reload: bool = False) -> pl.DataFrame:
    """
    Return the macroeconomic panel the small open economy model is estimated on, one row per country
    and year.

    The World Bank publishes these indicators annually, and they are returned at that frequency.
    """
    return _load_indicators(
        cache_dir,
        "world_bank_macro",
        MACRO_INDICATOR_NAMES,
        force_reload=force_reload,
    )
