import pytest

from climate_risk import load_rivers_data
from tests.conftest import NetworkAccessError, toy_rivers


@pytest.fixture
def warm_cache(write_rivers_cache):
    """Both processed files, holding different rivers."""
    cache_dir = write_rivers_cache(toy_rivers().iloc[:1])
    write_rivers_cache(toy_rivers().iloc[:2], include_medium=True)

    return cache_dir


def test_big_rivers_are_read_by_default(warm_cache):
    rivers = load_rivers_data(warm_cache)

    assert rivers["ORD_FLOW"].tolist() == [4]


def test_include_medium_reads_the_other_file(warm_cache):
    rivers = load_rivers_data(warm_cache, include_medium=True)

    assert rivers["ORD_FLOW"].tolist() == [4, 5]


def test_processed_cache_alone_does_not_download(write_rivers_cache):
    cache_dir = write_rivers_cache(toy_rivers().iloc[:1])

    assert load_rivers_data(cache_dir)["ORD_FLOW"].tolist() == [4]


def test_cold_cache_reaches_for_the_archive(tmp_path):
    with pytest.raises(NetworkAccessError):
        load_rivers_data(tmp_path)
