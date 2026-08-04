import pytest

from climate_risk import load_rivers_data
from climate_risk.const_vars import RIVERS_SHAPEFILE_FILENAME, RIVERS_ZIP_FILENAME
from tests.conftest import toy_rivers


@pytest.fixture
def warm_cache(write_rivers_cache):
    """Both processed files, holding different rivers, plus the archive markers the loader checks."""
    cache_dir = write_rivers_cache(toy_rivers().iloc[:1])
    write_rivers_cache(toy_rivers().iloc[:2], include_medium=True)

    (cache_dir / "rivers" / RIVERS_ZIP_FILENAME).touch()
    (cache_dir / "rivers" / RIVERS_SHAPEFILE_FILENAME).touch()

    return cache_dir


def test_big_rivers_are_read_by_default(warm_cache):
    rivers = load_rivers_data(warm_cache)

    assert rivers["ORD_FLOW"].tolist() == [4]


def test_include_medium_reads_the_other_file(warm_cache):
    rivers = load_rivers_data(warm_cache, include_medium=True)

    assert rivers["ORD_FLOW"].tolist() == [4, 5]
