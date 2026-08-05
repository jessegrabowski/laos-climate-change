import pandas as pd
import pytest

from climate_risk import load_hadcrut_data


@pytest.fixture(params=["1960", "1960-01-01"], ids=["bare-year", "iso-date"])
def processed_only(request, tmp_path):
    """Caches written by different versions hold the year both ways; both must reload."""
    (tmp_path / "hadcrut_temperature_processed.csv").write_text(
        f"ISO,year,surface_temperature_dev\nLAO,{request.param},0.5\n"
    )
    return tmp_path


def test_warm_cache_indexes_by_iso_and_parsed_year(processed_only):
    """Downstream joins on a datetime year; a string index silently fails to match."""
    df = load_hadcrut_data(processed_only)

    assert df.index.names == ["ISO", "year"]
    assert isinstance(df.index.get_level_values("year"), pd.DatetimeIndex)
