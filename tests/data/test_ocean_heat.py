import pandas as pd
import pytest
import requests

from climate_risk.data.ocean_heat import OCEAN_HEAT, load_ocean_heat_data, transform_ocean_heat

# Upstream names its columns date and anomaly; the loader replaces the header row.
PUBLISHED = "date,anomaly\n1960-01,0.0\n1960-07,2.0\n1961-02,10.0\n1961-08,20.0\n"


@pytest.fixture
def published(monkeypatch):
    """Serve the NCEI file without a socket, recording each request so a warm hit is observable."""
    calls = []

    class Response:
        headers = {"Content-Length": str(len(PUBLISHED))}

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            yield PUBLISHED.encode()

    def fake_get(url, **kwargs):
        calls.append(url)
        return Response()

    monkeypatch.setattr(requests, "get", fake_get)

    return calls


@pytest.fixture
def seasonal():
    return pd.DataFrame({"Date": ["1960-01", "1960-07", "1961-02", "1961-08"], "Temp": [0.0, 2.0, 10.0, 20.0]})


def test_annual_means_are_shifted_onto_the_baseline(seasonal):
    """The offset is stated literally: the published results move if it is ever retuned."""
    annual = transform_ocean_heat(seasonal)

    assert annual["Temp"].tolist() == pytest.approx([153.0, 167.0])


def test_years_are_stamped_at_their_start(seasonal):
    """The panel joins on a year-start timestamp, which resampling leaves at year-end."""
    annual = transform_ocean_heat(seasonal)

    assert annual.index.tolist() == [pd.Timestamp("1960-01-01"), pd.Timestamp("1961-01-01")]


def test_the_published_header_is_replaced(tmp_path, published):
    frame = load_ocean_heat_data(tmp_path)

    assert frame.columns.tolist() == ["Temp"]
    assert frame.index.name == "Date"


def test_a_warm_cache_does_not_reach_the_network(tmp_path, published):
    load_ocean_heat_data(tmp_path)
    load_ocean_heat_data(tmp_path)

    assert len(published) == 1


def test_the_warm_cache_is_read_with_parsed_dates(tmp_path, published):
    """Downstream reaches for `.dt.year`, which a string index cannot answer."""
    load_ocean_heat_data(tmp_path)

    assert isinstance(load_ocean_heat_data(tmp_path).index, pd.DatetimeIndex)


def test_the_processed_cache_survives_the_raw_download_being_deleted(tmp_path, published):
    """Nobody keeps the raw files. This is the test that proves fetch runs inside the builder."""
    load_ocean_heat_data(tmp_path)
    OCEAN_HEAT.path(tmp_path).unlink()

    frame = load_ocean_heat_data(tmp_path)

    assert len(published) == 1
    assert frame["Temp"].tolist() == pytest.approx([153.0, 167.0])


def test_force_reload_goes_back_to_the_source(tmp_path, published):
    load_ocean_heat_data(tmp_path)
    load_ocean_heat_data(tmp_path, force_reload=True)

    assert len(published) == 2


def test_the_raw_download_is_named_for_the_file_upstream_serves(tmp_path, published):
    """The old cache used this loader's name for processed rows; reusing it would misread them."""
    load_ocean_heat_data(tmp_path)

    assert OCEAN_HEAT.path(tmp_path).name == "ohc_levitus_climdash_seasonal.csv"
    assert (tmp_path / "ocean_heat.csv").exists()
