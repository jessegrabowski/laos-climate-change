import pytest

from climate_risk import load_gpcc_data
from climate_risk.const_vars import GPCC_YEARS
from tests.conftest import toy_world


@pytest.fixture
def processed_only(tmp_path):
    gpcc_dir = tmp_path / "gpcc"
    gpcc_dir.mkdir()
    (gpcc_dir / "gpcc_precipitations.csv").write_text("country_code,time,precip\nLAO,1981-01-01,5.0\n")
    return tmp_path


def test_warm_cache_indexes_by_country_and_time(processed_only):
    df = load_gpcc_data(processed_only)

    assert df.index.names == ["country_code", "time"]


def test_interrupted_extraction_resumes(write_gpcc_archives, write_shapefile_cache):
    """One extracted archive once stood in for all of them, so an interrupted run never recovered."""
    cache_dir = write_gpcc_archives(extracted=[GPCC_YEARS[0]])
    write_shapefile_cache("world", toy_world())

    load_gpcc_data(cache_dir, repair_ISO_codes=False)

    assert all((cache_dir / "gpcc" / f"gpcc_raw_{year_range}.nc").exists() for year_range in GPCC_YEARS)


def test_cold_run_aggregates_precipitation_by_country(write_gpcc_archives, write_shapefile_cache):
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())

    df = load_gpcc_data(cache_dir, repair_ISO_codes=False)

    assert df.index.names == ["country_code", "time"]
    assert sorted(df.index.get_level_values("country_code").unique()) == ["AAA", "BBB", "CCC"]
