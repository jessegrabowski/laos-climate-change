import pytest

from climate_risk import load_gpcc_data


@pytest.fixture
def processed_only(tmp_path):
    gpcc_dir = tmp_path / "gpcc"
    gpcc_dir.mkdir()
    (gpcc_dir / "gpcc_precipitations.csv").write_text("country_code,time,precip\nLAO,1981-01-01,5.0\n")
    return tmp_path


def test_warm_cache_indexes_by_country_and_time(processed_only):
    df = load_gpcc_data(processed_only)

    assert df.index.names == ["country_code", "time"]
