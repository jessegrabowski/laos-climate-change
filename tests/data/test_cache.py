from dataclasses import replace

import geopandas as gpd
import pandas as pd
import pytest

from shapely.geometry import Point

from climate_risk.data.cache import cache_key, cached, geo_shapefile, pandas_csv


@pytest.fixture
def frame():
    return pd.DataFrame({"Date": ["1990-01-01", "1991-01-01"], "co2": [354.4, 355.6]}).set_index("Date")


@pytest.fixture
def counting_builder(frame):
    """A builder that records how often it ran, so a cache miss is observable."""
    calls = []

    def build():
        calls.append(1)
        return frame

    build.calls = calls

    return build


def test_the_builder_runs_once_across_repeated_calls(tmp_path, counting_builder):
    """The bug this replaces recomputed silently every call, for forty minutes at a time."""
    cached(tmp_path, "co2", counting_builder, pandas_csv(index_col="Date"))
    result = cached(tmp_path, "co2", counting_builder, pandas_csv(index_col="Date"))

    assert len(counting_builder.calls) == 1
    assert result.index.tolist() == ["1990-01-01", "1991-01-01"]


def test_force_rebuilds(tmp_path, counting_builder):
    cached(tmp_path, "co2", counting_builder, pandas_csv(index_col="Date"))
    cached(tmp_path, "co2", counting_builder, pandas_csv(index_col="Date"), force=True)

    assert len(counting_builder.calls) == 2


def test_different_parameters_do_not_share_an_entry(tmp_path, frame):
    """Two hardcoded filenames for one parameterised cache is what this replaces."""
    cached(tmp_path, "rivers", lambda: frame, pandas_csv(index_col="Date"), params={"ord_flow_lt": 5})
    cached(tmp_path, "rivers", lambda: frame.head(1), pandas_csv(index_col="Date"), params={"ord_flow_lt": 6})

    assert len(cached(tmp_path, "rivers", lambda: frame, pandas_csv(index_col="Date"), params={"ord_flow_lt": 5})) == 2
    assert len(cached(tmp_path, "rivers", lambda: frame, pandas_csv(index_col="Date"), params={"ord_flow_lt": 6})) == 1


def test_the_written_and_read_frames_agree(tmp_path, frame):
    """A reader that does not restore the index is the cold/warm divergence this pairing prevents."""
    written = cached(tmp_path, "co2", lambda: frame, pandas_csv(index_col="Date"))
    reloaded = cached(tmp_path, "co2", lambda: frame, pandas_csv(index_col="Date"))

    pd.testing.assert_frame_equal(written, reloaded)


def test_a_geodataframe_round_trips_through_its_sidecars(tmp_path):
    points = gpd.GeoDataFrame({"kind": ["river"], "geometry": [Point(102.5, 18.5)]}, crs="EPSG:4326")

    cached(tmp_path, "points", lambda: points, geo_shapefile())
    reloaded = cached(tmp_path, "points", lambda: points, geo_shapefile())

    assert reloaded.geometry.x.tolist() == [102.5]
    assert reloaded.crs == points.crs


def test_parameters_are_ordered_so_the_key_is_stable():
    """Callers write kwargs in whatever order reads well; the same set must find the same file."""
    assert cache_key("points", {"region": "laos", "grid_size": 400}) == cache_key(
        "points", {"grid_size": 400, "region": "laos"}
    )


def test_the_key_is_readable():
    assert cache_key("points", {"region": "laos", "grid_size": 400}) == "points__grid_size=400__region=laos"


def test_a_bare_name_needs_no_parameters():
    assert cache_key("co2") == "co2"


@pytest.mark.parametrize(
    "params",
    [{"region": "la/os"}, {"region": "la__os"}, {"region": "la=os"}, {"gr/id": 4}],
    ids=["slash", "parameter-separator", "value-separator", "in-the-name"],
)
def test_a_value_that_would_corrupt_the_filename_is_rejected(params):
    """A separator in a value makes two different parameter sets collide on one cache entry."""
    with pytest.raises(ValueError, match="must not contain"):
        cache_key("points", params)


@pytest.mark.parametrize("value", [1.5, None, ["a"], object()], ids=["float", "none", "list", "object"])
def test_a_value_that_does_not_format_stably_is_rejected(value):
    """`str()` of a float or an object is not a stable identity to key a cache on."""
    with pytest.raises(ValueError, match="string, integer or boolean"):
        cache_key("points", {"size": value})


def test_a_hyphenated_value_is_allowed():
    """Region and indicator names carry hyphens; only the separators are off limits."""
    assert cache_key("points", {"region": "south-east-asia"}) == "points__region=south-east-asia"


def test_a_write_killed_partway_does_not_poison_the_cache(tmp_path, frame):
    """A truncated file left at the destination would read back as a hit forever after."""

    def write_half_then_die(artefact, path):
        path.write_text("Date,co2\n1990-01-01,354.4")
        raise OSError("no space left on device")

    dying = replace(pandas_csv(index_col="Date"), write=write_half_then_die)

    with pytest.raises(OSError, match="no space left"):
        cached(tmp_path, "co2", lambda: frame, dying)

    assert not (tmp_path / "co2.csv").exists()
    assert len(cached(tmp_path, "co2", lambda: frame, pandas_csv(index_col="Date"))) == 2


def test_an_empty_name_is_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        cache_key("")
