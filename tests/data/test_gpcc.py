import gzip
import shutil

import geopandas as gpd
import pandas as pd
import pytest
import xarray as xr

from climate_risk.data.gpcc import GPCC_PRODUCTS, _as_timestamps, load_gpcc_data, transform_gpcc
from tests.conftest import TOY_ARCHIVES, toy_gpcc_products, toy_world

# Stated literally, so a wrong cache key fails rather than agreeing with itself. The span is the
# toy manifest's, not the published one.
UNREPAIRED_CACHE = "gpcc__coverage=1981-2021__repaired_iso=False.parquet"
REPAIRED_CACHE = "gpcc__coverage=1981-2021__repaired_iso=True.parquet"


def gridded(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["time", "lat", "lon", "precip"]).assign(time=lambda x: pd.to_datetime(x["time"]))


def extracted_name(archive: str) -> str:
    return archive.removesuffix(".gz")


def test_interrupted_extraction_resumes(write_gpcc_archives, write_shapefile_cache):
    """One extracted archive once stood in for all of them, so an interrupted run never recovered."""
    cache_dir = write_gpcc_archives(extracted=[TOY_ARCHIVES[0]])
    write_shapefile_cache("world", toy_world())

    load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False)

    assert all((cache_dir / "gpcc" / extracted_name(archive)).exists() for archive in TOY_ARCHIVES)


def test_cold_run_aggregates_precipitation_by_country(write_gpcc_archives, write_shapefile_cache):
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())

    frame = load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False)

    assert frame.index.names == ["country_code", "time"]
    assert sorted(frame.index.get_level_values("country_code").unique()) == ["AAA", "BBB", "CCC"]


def test_the_cold_run_writes_the_cache_it_will_read(write_gpcc_archives, write_shapefile_cache):
    """A key spelled one way on write and another on read is the bug this replaces."""
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())

    load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False)

    assert (cache_dir / UNREPAIRED_CACHE).exists()


def test_the_monitoring_dates_are_decoded_rather_than_read_as_numbers(write_gpcc_archives, write_shapefile_cache):
    """The monitoring archives date rows as YYYYMMDD floats; taken as numbers they all land in 1970."""
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())

    frame = load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False)
    months = pd.DatetimeIndex(frame.index.get_level_values("time"))

    assert months.min() == pd.Timestamp("1981-01-01")
    assert months.max() == pd.Timestamp("2021-01-01")


def test_the_published_manifest_lists_an_archive_for_every_period_it_claims():
    """A decade or a month left off the list is a hole in the record that nothing downstream sees."""
    full_data, monitoring = GPCC_PRODUCTS

    assert len(full_data.sources) * 10 == full_data.last_year - full_data.first_year + 1
    assert len(monitoring.sources) == (monitoring.last_year - monitoring.first_year + 1) * 12


def test_the_two_products_meet_without_a_gap_or_an_overlap():
    """An overlap would total a month twice; a gap would leave a year out of the panel entirely."""
    full_data, monitoring = GPCC_PRODUCTS

    assert monitoring.first_year == full_data.last_year + 1


def test_a_time_axis_in_an_unknown_encoding_is_refused():
    """Reading an unrecognised numeric axis as-is would date the record silently, not loudly."""
    time = xr.DataArray([20210101.0], dims="time", attrs={"units": "days since 1900-01-01"})

    with pytest.raises(ValueError, match="neither a decoded datetime"):
        _as_timestamps(time)


def test_a_warm_cache_does_not_touch_the_archives(write_gpcc_archives, write_shapefile_cache):
    """The archives are gigabytes; a warm processed cache must not read or extract them."""
    cache_dir = write_gpcc_archives()
    write_shapefile_cache("world", toy_world())
    load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False)

    for archive in TOY_ARCHIVES:
        (cache_dir / "gpcc" / archive).unlink()
        (cache_dir / "gpcc" / extracted_name(archive)).unlink()

    assert not load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False).empty


def test_cells_are_averaged_per_country_and_month():
    grid = gridded(
        [
            ("1981-01-01", 0.5, 0.5, 4.0),
            ("1981-01-01", 0.75, 0.75, 6.0),
            ("1981-01-01", 0.5, 2.5, 100.0),
        ]
    )

    monthly = transform_gpcc([grid], toy_world())

    assert monthly.loc[("AAA", pd.Timestamp("1981-01-01")), "precip"] == pytest.approx(5.0)
    assert monthly.loc[("BBB", pd.Timestamp("1981-01-01")), "precip"] == pytest.approx(100.0)


def test_cells_over_the_ocean_are_dropped():
    grid = gridded([("1981-01-01", 0.5, 0.5, 4.0), ("1981-01-01", 50.0, 50.0, 999.0)])

    monthly = transform_gpcc([grid], toy_world())

    assert monthly["precip"].tolist() == [4.0]


def test_every_archive_reaches_the_result():
    """The archives are read one at a time; dropping one loses its years without an error."""
    grids = [gridded([("1981-01-01", 0.5, 0.5, 1.0)]), gridded([("1991-01-01", 0.5, 0.5, 2.0)])]

    monthly = transform_gpcc(grids, toy_world())

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
        load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False)

    monkeypatch.undo()
    assert not (cache_dir / "gpcc" / extracted_name(TOY_ARCHIVES[0])).exists()
    assert not load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False).empty


def test_the_archives_are_decompressed_before_reading(write_gpcc_archives, write_shapefile_cache):
    """The published files are gzipped NetCDF; reading one without decompressing raises."""
    cache_dir = write_gpcc_archives()
    archive = cache_dir / "gpcc" / TOY_ARCHIVES[0]

    assert gzip.decompress(archive.read_bytes())[1:4] == b"HDF"

    write_shapefile_cache("world", toy_world())
    assert not load_gpcc_data(cache_dir, products=toy_gpcc_products(), repair_ISO_codes=False).empty


def test_the_world_boundaries_decide_the_countries():
    """Passing the boundaries in is what lets this run without the 606MB shapefile."""
    grid = gridded([("1981-01-01", 0.5, 0.5, 4.0)])
    one_country = gpd.GeoDataFrame(toy_world().iloc[:1])

    monthly = transform_gpcc([grid], one_country)

    assert monthly.index.get_level_values("country_code").tolist() == ["AAA"]
