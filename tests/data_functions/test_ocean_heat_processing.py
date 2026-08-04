import pytest

from climate_risk import load_ocean_heat_data
from climate_risk.const_vars import OCEAN_HEAT_FILENAME
from tests.conftest import NetworkAccessError


@pytest.fixture
def warm_cache(tmp_path):
    (tmp_path / OCEAN_HEAT_FILENAME).write_text("Date,Temp\n1960-01-01,1.5\n1961-01-01,2.5\n")
    return tmp_path


def test_force_reload_bypasses_a_warm_cache(warm_cache):
    with pytest.raises(NetworkAccessError):
        load_ocean_heat_data(warm_cache, force_reload=True)
