import pytest

from climate_risk import load_gpcc_data
from tests.conftest import NetworkAccessError


@pytest.fixture
def processed_only(tmp_path):
    """Only the processed CSV — the raw archives a cold run would have left behind are absent."""
    gpcc_dir = tmp_path / "gpcc"
    gpcc_dir.mkdir()
    (gpcc_dir / "gpcc_precipitations.csv").write_text("country_code,time,precip\nLAO,1981-01-01,5.0\n")
    return tmp_path


@pytest.mark.xfail(
    reason="the raw-archive loop runs before the processed-cache check, so a warm cache still downloads",
    raises=NetworkAccessError,
)
def test_processed_cache_alone_does_not_download(processed_only):
    load_gpcc_data(processed_only)
