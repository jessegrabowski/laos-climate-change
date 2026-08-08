import shutil

import pandas as pd
import pytest

from climate_risk import load_shapefile
from climate_risk.data_functions.shapefiles_data_loader import (
    SHAPEFILE_MEMBERS,
    SHAPEFILE_SOURCES,
    repair_iso_codes,
)
from climate_risk.exceptions import DataValidationError, ISOCodeValidationError
from tests.conftest import toy_world, toy_world_needing_repair


def test_every_declared_source_knows_where_its_archive_unpacks():
    """A source without a member entry passes validation and then dies on a KeyError mid-load."""
    assert set(SHAPEFILE_SOURCES) == set(SHAPEFILE_MEMBERS)


def test_unknown_shapefile_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="which should be one of"):
        load_shapefile("atlantis", tmp_path)


def test_warm_cache_reads_without_downloading(write_shapefile_cache):
    """Both the download and the extract step must no-op when the cache is already populated."""
    cache_dir = write_shapefile_cache("world", toy_world())

    world = load_shapefile("world", cache_dir, repair_ISO_codes=False)

    assert len(world) == 3


def test_only_the_archive_on_disk_is_enough_to_load(write_shapefile_cache):
    """A half-populated cache is the normal state after an interrupted run; extraction must resume."""
    cache_dir = write_shapefile_cache("world", toy_world())
    # Stated literally, not derived from the loader, so a wrong layout leaves the real files in
    # place and fails here rather than agreeing with itself.
    shutil.rmtree(cache_dir / "shapefiles" / "WB_countries_Admin0_10m")

    world = load_shapefile("world", cache_dir, repair_ISO_codes=False)

    assert len(world) == 3


def test_the_repair_does_not_depend_on_how_the_caller_capitalised_it(write_shapefile_cache):
    """Every other branch lowercases `which`, so a capitalised call silently skipped the repair."""
    cache_dir = write_shapefile_cache("world", toy_world_needing_repair())

    world = load_shapefile("World", cache_dir)

    assert world.loc[world["WB_NAME"] == "France", "ISO_A3"].tolist() == ["FRA"]
    assert "-99" not in set(world["ISO_A3"])


def test_laos_reads_the_district_layer_from_a_flat_archive(write_shapefile_cache):
    """The archive unpacks flat, so reading the wrong admin level means reading a different file."""
    cache_dir = write_shapefile_cache("laos", toy_world())
    (cache_dir / "shapefiles" / "lao_admin0.shp").write_text("not a shapefile")

    laos = load_shapefile("laos", cache_dir, repair_ISO_codes=False)

    assert sorted(laos["ISO_A3"]) == ["AAA", "BBB", "CCC"]


def test_repair_supplies_the_missing_sovereign_codes():
    repaired = repair_iso_codes(toy_world_needing_repair())

    codes = dict(zip(repaired["WB_NAME"], repaired["ISO_A3"], strict=True))
    assert codes["France"] == "FRA"
    assert codes["Norway"] == "NOR"
    assert codes["Kosovo"] == "XKX"


def test_repair_drops_territories_that_would_double_count_their_owner():
    """Bonaire is labelled NLD; keeping it would give the Netherlands two geometries."""
    repaired = repair_iso_codes(toy_world_needing_repair())

    assert "Bonaire (Neth.)" not in set(repaired["WB_NAME"])
    assert "Johnston Atoll (US)" not in set(repaired["WB_NAME"])
    assert sorted(repaired["ISO_A3"]) == ["FRA", "NLD", "NOR", "NZL", "XKX"]


def test_repair_reindexes_from_zero():
    repaired = repair_iso_codes(toy_world_needing_repair())

    assert repaired.index.tolist() == list(range(len(repaired)))


def test_a_frame_without_the_naming_columns_is_an_error():
    """An upstream schema change should name the missing column, not fail on a bare KeyError."""
    with pytest.raises(DataValidationError, match="WB_NAME"):
        repair_iso_codes(toy_world())


@pytest.mark.parametrize(
    ("column", "renamed", "expected"),
    [("WB_NAME", {"Kosovo": "Republic of Kosovo"}, "Kosovo"), ("ISO_A3", {"UMI": "USA"}, "UMI")],
    ids=["by-name", "by-code"],
)
def test_a_repair_matching_nothing_is_an_error(column, renamed, expected):
    """Upstream renaming anything a repair targets must fail loudly, not silently skip it."""
    world = toy_world_needing_repair().replace({column: renamed})

    with pytest.raises(DataValidationError, match=expected):
        repair_iso_codes(world)


def test_duplicate_iso_codes_are_an_error():
    """One code per geometry is what every downstream join assumes."""
    world = toy_world_needing_repair()
    second_netherlands = world[world["WB_NAME"] == "Netherlands"].assign(WB_NAME="Netherlands (again)")
    doubled = pd.concat([world, second_netherlands], ignore_index=True)

    with pytest.raises(ISOCodeValidationError, match="NLD"):
        repair_iso_codes(doubled)
