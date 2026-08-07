import pandas as pd
import pytest

from climate_risk.data.hadcrut import load_hadcrut_data, transform_hadcrut
from tests.conftest import toy_world

# The panel starts in 1960; the gridded record reaches back much further.
FIRST_PANEL_YEAR = 1959

# The cache key is stated literally, so a wrong one fails rather than agreeing with itself.
REPAIRED_CACHE = "hadcrut__repaired_iso=True.parquet"


def gridded(rows) -> pd.DataFrame:
    """Gridded anomalies as xarray hands them over, one row per cell and timestamp."""
    return pd.DataFrame(rows, columns=["time", "latitude", "longitude", "tas_mean"]).assign(
        time=lambda x: pd.to_datetime(x["time"])
    )


@pytest.fixture
def processed_only(tmp_path):
    pd.DataFrame(
        {"surface_temperature_dev": [0.5]},
        index=pd.MultiIndex.from_arrays([["LAO"], pd.to_datetime(["1960-01-01"])], names=["ISO", "year"]),
    ).to_parquet(tmp_path / REPAIRED_CACHE)

    return tmp_path


def test_warm_cache_indexes_by_iso_and_parsed_year(processed_only):
    """Downstream joins on a datetime year; a string index silently fails to match."""
    frame = load_hadcrut_data(processed_only)

    assert frame.index.names == ["ISO", "year"]
    assert isinstance(frame.index.get_level_values("year"), pd.DatetimeIndex)


def test_cells_are_averaged_per_country_and_year():
    """Many grid cells fall in one country, and the panel wants one number per country-year."""
    temperatures = gridded(
        [
            ("1990-01-01", 0.5, 0.5, 1.0),
            ("1990-06-01", 0.5, 0.5, 3.0),
            ("1990-01-01", 0.5, 2.5, 10.0),
        ]
    )

    annual = transform_hadcrut(temperatures, toy_world())

    assert annual.loc[("AAA", pd.Timestamp("1990-01-01")), "surface_temperature_dev"] == pytest.approx(2.0)
    assert annual.loc[("BBB", pd.Timestamp("1990-01-01")), "surface_temperature_dev"] == pytest.approx(10.0)


def test_cells_outside_every_country_are_dropped():
    """The grid covers ocean, which belongs to no country and would otherwise average in."""
    temperatures = gridded([("1990-01-01", 0.5, 0.5, 1.0), ("1990-01-01", 50.0, 50.0, 99.0)])

    annual = transform_hadcrut(temperatures, toy_world())

    assert annual["surface_temperature_dev"].tolist() == [1.0]


def test_years_before_the_panel_are_dropped():
    temperatures = gridded([("1950-01-01", 0.5, 0.5, 1.0), ("1990-01-01", 0.5, 0.5, 2.0)])

    annual = transform_hadcrut(temperatures, toy_world())

    assert pd.DatetimeIndex(annual.index.get_level_values("year")).year.tolist() == [1990]


def test_the_boundary_year_is_excluded_but_the_next_is_kept():
    """The comparison is exclusive, and off by one here adds a sparse year to the panel."""
    temperatures = gridded(
        [(f"{FIRST_PANEL_YEAR}-01-01", 0.5, 0.5, 1.0), (f"{FIRST_PANEL_YEAR + 1}-01-01", 0.5, 0.5, 2.0)]
    )

    annual = transform_hadcrut(temperatures, toy_world())

    assert pd.DatetimeIndex(annual.index.get_level_values("year")).year.tolist() == [FIRST_PANEL_YEAR + 1]


def test_repairing_iso_codes_gets_its_own_cache_entry(tmp_path):
    """Repairing changes which countries appear, so one entry cannot serve both settings."""
    pd.DataFrame(
        {"surface_temperature_dev": [0.5]},
        index=pd.MultiIndex.from_arrays([["LAO"], pd.to_datetime(["1960-01-01"])], names=["ISO", "year"]),
    ).to_parquet(tmp_path / REPAIRED_CACHE)

    assert load_hadcrut_data(tmp_path).index.get_level_values("ISO").tolist() == ["LAO"]
    assert not (tmp_path / "hadcrut__repaired_iso=False.parquet").exists()
