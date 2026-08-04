import pytest

from climate_risk import load_shapefile
from tests.conftest import toy_world


def test_unknown_shapefile_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="which should be one of"):
        load_shapefile("atlantis", tmp_path)


def test_warm_cache_reads_without_downloading(write_shapefile_cache):
    """Both the download and the extract step must no-op when the cache is already populated."""
    cache_dir = write_shapefile_cache("world", toy_world())

    world = load_shapefile("world", cache_dir, repair_ISO_codes=False)

    assert len(world) == 3


@pytest.mark.xfail(
    reason="the repair drops rows by hardcoded position, so it only accepts the upstream row ordering",
    raises=KeyError,
)
def test_repair_works_on_any_valid_world_shapefile(write_shapefile_cache):
    cache_dir = write_shapefile_cache("world", toy_world())

    load_shapefile("world", cache_dir, repair_ISO_codes=True)
