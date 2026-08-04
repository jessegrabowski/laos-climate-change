import pytest

from climate_risk import load_hadcrut_data
from tests.conftest import NetworkAccessError


@pytest.fixture
def processed_only(tmp_path):
    (tmp_path / "hadcrut_temperature_processed.csv").write_text(
        "ISO,year,surface_temperature_dev\nLAO,1960-01-01,0.5\n"
    )
    return tmp_path


@pytest.mark.xfail(
    reason="the raw-download check runs before the processed-cache check, so a warm cache still downloads",
    raises=NetworkAccessError,
)
def test_processed_cache_alone_does_not_download(processed_only):
    load_hadcrut_data(processed_only)
