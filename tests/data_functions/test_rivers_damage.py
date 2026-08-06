import geopandas as gpd
import pandas as pd
import pytest

from shapely.geometry import LineString

from climate_risk.data_functions.rivers_damage import create_floods_rivers_damage, create_hydro_rivers_damage
from tests.conftest import emdat_event, toy_world_needing_repair

# A Laos flood whose coordinates the loader overrides from LAOS_LOCATION_DICTIONARY.
PATCHED_EVENT = "2013-0338-LAO"
PATCHED_LATITUDE = 19.5
UNPATCHED_LATITUDE = 1.25

VARIANTS = {
    "hydro": (create_hydro_rivers_damage, "Total_Damage_Hydro", "log_affected_hydro"),
    "floods": (create_floods_rivers_damage, "Total_Damage_Flood", "log_affected_floods"),
}


@pytest.fixture
def rivers_two_degrees_east():
    """A single big river offset from every event, so distances are positive and comparable."""
    return gpd.GeoDataFrame(
        {"ORD_FLOW": [4], "HYRIV_ID": [1], "geometry": [LineString([(104.0, 10.0), (104.0, 25.0)])]},
        crs="EPSG:4326",
    )


@pytest.fixture
def damage_cache(tmp_path, write_emdat_cache, write_shapefile_cache, write_rivers_cache, rivers_two_degrees_east):
    write_shapefile_cache("world", toy_world_needing_repair())
    write_rivers_cache(rivers_two_degrees_east)
    write_emdat_cache(
        [
            # Fractional coordinates, as EM-DAT supplies them: whole numbers make the column
            # integral through the workbook, and the coordinate patch then cannot write into it.
            emdat_event(
                {"ISO": "LAO", "DisNo.": "LAO-flood", "Disaster Type": "Flood", "Latitude": 18.25, "Longitude": 102.25}
            ),
            emdat_event(
                {"ISO": "LAO", "DisNo.": "LAO-storm", "Disaster Type": "Storm", "Latitude": 18.5, "Longitude": 102.5}
            ),
            emdat_event(
                {
                    "ISO": "LAO",
                    "DisNo.": "LAO-drought",
                    "Disaster Type": "Drought",
                    "Latitude": 18.75,
                    "Longitude": 102.75,
                }
            ),
            emdat_event(
                {"ISO": "LAO", "DisNo.": PATCHED_EVENT, "Disaster Type": "Flood", "Latitude": 1.25, "Longitude": 1.75}
            ),
        ]
    )
    return tmp_path


@pytest.mark.parametrize("variant", list(VARIANTS), ids=list(VARIANTS))
def test_the_cached_frame_matches_the_one_that_wrote_it(damage_cache, variant):
    """A shapefile truncates field names and coarsens dates, so the warm path has to undo both."""
    create, _, _ = VARIANTS[variant]

    cold = create(damage_cache)
    warm = create(damage_cache)

    assert list(cold.columns) == [c for c in cold.columns if c in warm.columns]
    assert set(cold.columns) == set(warm.columns)
    assert (cold.dtypes[warm.columns.tolist()] == warm.dtypes).all()


@pytest.mark.parametrize("variant", list(VARIANTS), ids=list(VARIANTS))
def test_the_totals_and_their_logs_are_suffixed_per_variant(damage_cache, variant):
    """Both variants land in the same cache directory and are told apart only by these suffixes."""
    create, total, log = VARIANTS[variant]

    damage = create(damage_cache)

    assert total in damage.columns
    assert log in damage.columns


def test_distance_to_the_nearest_river_is_in_kilometres(damage_cache):
    """The column feeds a regression in kilometres; metres would inflate it a thousandfold."""
    damage = create_floods_rivers_damage(damage_cache)

    # Both floods sit within a couple of degrees of the river, so a few hundred kilometres.
    assert damage["closest_river"].max() < 1_000


def test_only_hydrometeorological_events_reach_the_hydro_frame(damage_cache):
    """The drought is climatological, so counting it would double-count against the clim split."""
    damage = create_hydro_rivers_damage(damage_cache)

    assert len(damage) == 3


def test_only_floods_reach_the_floods_frame(damage_cache):
    damage = create_floods_rivers_damage(damage_cache)

    assert len(damage) == 2


def test_laos_flood_coordinates_are_overridden(damage_cache):
    """EM-DAT records these events against the wrong place, so the loader forces the coordinates."""
    damage = create_floods_rivers_damage(damage_cache)

    assert PATCHED_LATITUDE in set(damage["Latitude"])
    assert UNPATCHED_LATITUDE not in set(damage["Latitude"])


def test_the_year_survives_the_round_trip_as_a_timestamp(damage_cache):
    """Downstream reaches for `.dt`, which a string year cannot answer."""
    create_hydro_rivers_damage(damage_cache)
    warm = create_hydro_rivers_damage(damage_cache)

    assert isinstance(warm["year"].dtype, type(pd.Series(dtype="datetime64[us]").dtype))
    assert warm["year"].dt.year.tolist() == [1990, 1990, 1990]
