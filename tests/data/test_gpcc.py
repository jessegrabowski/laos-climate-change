import gzip
import shutil

import geopandas as gpd
import pandas as pd
import pytest

from climate_risk.data.gpcc import load_gpcc_data, transform_gpcc
from tests.conftest import GPCC_DECADES, gpcc_archive_name, toy_world

# Stated literally, so a wrong cache key fails rather than agreeing with itself.
UNREPAIRED_CACHE = "gpcc__coverage=1981-2020__repaired_iso=False.parquet"
REPAIRED_CACHE = "gpcc__coverage=1981-2020__repaired_iso=True.parquet"


def gridded(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["time", "lat", "lon", "precip"]).assign(time=lambda x: pd.to_datetime(x["time"]))


def extracted_name(decade: str) -> str:
    return gpcc_archive_name(decade).removesuffix(".gz")


def test_interrupted_extraction_resumes(write_gpcc_archives, write_shapefile_cache):
    """One extracted archive once stood in for all of them, so an interrupted run never recovered."""
    cache_dir = write_gpcc_archives(extracted=[GPCC_DECADES[0]])
    write_shapefile_cache("world", toy_world())

    load_gpcc_data(cache_dir, repair_ISO_codes=False)

    assert all((cache_dir / "gpcc" / extracted_name(decade)).exists() for decade in GPCC_DECADES)


def test_cold_run_aggregates_precipitation_by_country(write_gpcc_archives, write_shapefile_cache):
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())

    frame = load_gpcc_data(cache_dir, repair_ISO_codes=False)

    assert frame.index.names == ["country_code", "time"]
    assert sorted(frame.index.get_level_values("country_code").unique()) == ["AAA", "BBB", "CCC"]


def test_the_cold_run_writes_the_cache_it_will_read(write_gpcc_archives, write_shapefile_cache):
    """A key spelled one way on write and another on read is the bug this replaces."""
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())

    load_gpcc_data(cache_dir, repair_ISO_codes=False)

    assert (cache_dir / UNREPAIRED_CACHE).exists()


def test_a_warm_cache_does_not_touch_the_archives(write_gpcc_archives, write_shapefile_cache):
    """The archives are gigabytes; a warm processed cache must not read or extract them."""
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())
    load_gpcc_data(cache_dir, repair_ISO_codes=False)

    for decade in GPCC_DECADES:
        (cache_dir / "gpcc" / gpcc_archive_name(decade)).unlink()
        (cache_dir / "gpcc" / extracted_name(decade)).unlink()

    assert not load_gpcc_data(cache_dir, repair_ISO_codes=False).empty


def test_cells_are_averaged_per_country_and_month():
    decade = gridded(
        [
            ("1981-01-01", 0.5, 0.5, 4.0),
            ("1981-01-01", 0.75, 0.75, 6.0),
            ("1981-01-01", 0.5, 2.5, 100.0),
        ]
    )

    monthly = transform_gpcc([decade], toy_world())

    assert monthly.loc[("AAA", pd.Timestamp("1981-01-01")), "precip"] == pytest.approx(5.0)
    assert monthly.loc[("BBB", pd.Timestamp("1981-01-01")), "precip"] == pytest.approx(100.0)


def test_cells_over_the_ocean_are_dropped():
    decade = gridded([("1981-01-01", 0.5, 0.5, 4.0), ("1981-01-01", 50.0, 50.0, 999.0)])

    monthly = transform_gpcc([decade], toy_world())

    assert monthly["precip"].tolist() == [4.0]


def test_every_decade_reaches_the_result():
    """The decades are read one at a time; dropping one loses ten years without an error."""
    decades = [gridded([("1981-01-01", 0.5, 0.5, 1.0)]), gridded([("1991-01-01", 0.5, 0.5, 2.0)])]

    monthly = transform_gpcc(decades, toy_world())

    assert pd.DatetimeIndex(monthly.index.get_level_values("time")).year.tolist() == [1981, 1991]


def test_an_interrupted_extraction_leaves_nothing_to_trust(write_gpcc_archives, write_shapefile_cache, monkeypatch):
    """A truncated .nc would satisfy the exists() check and be read as complete on every later run."""
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())

    def die_partway(source, target, length=0):
        target.write(b"\x89HDF truncated")
        raise OSError("no space left on device")

    monkeypatch.setattr(shutil, "copyfileobj", die_partway)
    with pytest.raises(OSError, match="no space left"):
        load_gpcc_data(cache_dir, repair_ISO_codes=False)

    monkeypatch.undo()
    assert not (cache_dir / "gpcc" / extracted_name(GPCC_DECADES[0])).exists()
    assert not load_gpcc_data(cache_dir, repair_ISO_codes=False).empty


def test_the_archives_are_decompressed_before_reading(write_gpcc_archives, write_shapefile_cache):
    """The published files are gzipped NetCDF; reading one without decompressing raises."""
    cache_dir = write_gpcc_archives()
    archive = cache_dir / "gpcc" / gpcc_archive_name(GPCC_DECADES[0])

    assert gzip.decompress(archive.read_bytes())[1:4] == b"HDF"

    write_shapefile_cache("world", toy_world())
    assert not load_gpcc_data(cache_dir, repair_ISO_codes=False).empty


def test_the_world_boundaries_decide_the_countries():
    """Passing the boundaries in is what lets this run without the 606MB shapefile."""
    decade = gridded([("1981-01-01", 0.5, 0.5, 4.0)])
    one_country = gpd.GeoDataFrame(toy_world().iloc[:1])

    monthly = transform_gpcc([decade], one_country)

    assert monthly.index.get_level_values("country_code").tolist() == ["AAA"]
