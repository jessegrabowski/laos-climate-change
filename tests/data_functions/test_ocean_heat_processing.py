import pandas as pd
import pytest

from climate_risk import load_ocean_heat_data
from climate_risk.const_vars import OCEAN_HEAT_FILENAME
from climate_risk.data_functions.ocean_heat_processing import process_ocean_heat
from tests.conftest import NetworkAccessError


@pytest.fixture
def warm_cache(tmp_path):
    (tmp_path / OCEAN_HEAT_FILENAME).write_text("Date,Temp\n1960-01-01,1.5\n1961-01-01,2.5\n")
    return tmp_path


@pytest.fixture
def monthly():
    return pd.DataFrame(
        {
            "Date": ["1960-01", "1960-07", "1961-02", "1961-08"],
            "Temp": [0.0, 2.0, 10.0, 20.0],
        }
    )


def test_force_reload_bypasses_a_warm_cache(warm_cache):
    with pytest.raises(NetworkAccessError):
        load_ocean_heat_data(warm_cache, force_reload=True)


def test_the_warm_cache_is_read_with_parsed_dates(warm_cache):
    """Downstream reaches for `.dt.year`, which a string index cannot answer."""
    assert isinstance(load_ocean_heat_data(warm_cache).index, pd.DatetimeIndex)


def test_annual_means_are_shifted_onto_the_baseline(monthly):
    """The offset is stated literally: the published results move if it is ever retuned."""
    annual = process_ocean_heat(monthly)

    assert annual["Temp"].tolist() == pytest.approx([153.0, 167.0])


def test_years_are_stamped_at_their_start(monthly):
    """The panel joins on a year-start timestamp, which resampling leaves at year-end."""
    annual = process_ocean_heat(monthly)

    assert annual.index.tolist() == [pd.Timestamp("1960-01-01"), pd.Timestamp("1961-01-01")]
