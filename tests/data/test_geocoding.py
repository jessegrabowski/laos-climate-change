from climate_risk.data.geocoding import (
    ELSEWHERE,
    IN_ITS_PROVINCE,
    IN_THE_UNIT,
    NO_POINT,
    score_geocoder,
    unambiguous_units,
)
from climate_risk.data.place_names import read_gazetteer


def test_only_names_reaching_one_unit_become_an_answer_key(write_gadm_cache):
    """A name reaching two units cannot judge a point: whichever the geocoder picked, the other was
    available. A third of the places that resolve are ambiguous, so this is most of the workbook."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    settled = unambiguous_units([("Sanamxay", None), ("Attapu", None), ("Bokeo", None)], gazetteer)

    assert settled == {"Sanamxay": "LAO.1.1_1", "Bokeo": "LAO.2_1"}


def test_a_point_inside_the_named_unit_scores_as_placed(write_gadm_cache):
    cache_dir = write_gadm_cache()
    gazetteer = read_gazetteer("LAO", cache_dir)

    scored = score_geocoder(lambda _, __: (0.5, 0.5), "LAO", [("Sanamxay", None)], gazetteer, cache_dir)

    assert scored == [("Sanamxay", "LAO.1.1_1", IN_THE_UNIT)]


def test_a_point_in_the_right_province_but_the_wrong_district_is_told_apart(write_gadm_cache):
    """Whether a source is usable turns on this outcome. A geocoder landing in the province is
    worth aggregating upwards; one landing in the wrong province is worth nothing."""
    cache_dir = write_gadm_cache()
    gazetteer = read_gazetteer("LAO", cache_dir)

    scored = score_geocoder(lambda _, __: (1.5, 0.5), "LAO", [("Sanamxay", None)], gazetteer, cache_dir)

    assert scored == [("Sanamxay", "LAO.1.1_1", IN_ITS_PROVINCE)]


def test_a_point_in_another_province_scores_as_misplaced(write_gadm_cache):
    cache_dir = write_gadm_cache()
    gazetteer = read_gazetteer("LAO", cache_dir)

    scored = score_geocoder(lambda _, __: (3.5, 0.5), "LAO", [("Sanamxay", None)], gazetteer, cache_dir)

    assert scored == [("Sanamxay", "LAO.1.1_1", ELSEWHERE)]


def test_a_place_the_geocoder_does_not_know_is_not_counted_as_wrong(write_gadm_cache):
    """Coverage and accuracy are separate decisions — a source that answers rarely and correctly is
    worth combining with another, and folding the silences into the error rate hides that."""
    cache_dir = write_gadm_cache()
    gazetteer = read_gazetteer("LAO", cache_dir)

    scored = score_geocoder(lambda _, __: None, "LAO", [("Sanamxay", None)], gazetteer, cache_dir)

    assert scored == [("Sanamxay", "LAO.1.1_1", NO_POINT)]


def test_a_unit_that_is_already_a_province_is_judged_against_itself(write_gadm_cache):
    """Half the countries in the archive stop at adm1 or adm2, so the named unit is often the
    level-1 one and there is no coarser answer to fall back to."""
    cache_dir = write_gadm_cache()
    gazetteer = read_gazetteer("LAO", cache_dir)

    scored = score_geocoder(lambda _, __: (4.5, 0.5), "LAO", [("Bokeo", None)], gazetteer, cache_dir)

    assert scored == [("Bokeo", "LAO.2_1", IN_THE_UNIT)]


def test_a_village_is_scored_against_its_own_polygon_not_its_district(write_gadm_cache):
    """The resolver reaches adm3 and adm4, and scoring those against the district holding them
    would pass a geocoder that never resolves finer than adm2."""
    cache_dir = write_gadm_cache()
    gazetteer = read_gazetteer("LAO", cache_dir)

    scored = score_geocoder(lambda _, __: (1.5, 0.5), "LAO", [("Samakhixay", None)], gazetteer, cache_dir)

    assert scored == [("Samakhixay", "LAO.1.2_1", IN_THE_UNIT)]


def test_nothing_to_check_against_reads_back_empty(write_gadm_cache):
    """Two fifths of written places name no GADM unit, and a country can supply none at all."""
    cache_dir = write_gadm_cache()
    gazetteer = read_gazetteer("LAO", cache_dir)

    assert score_geocoder(lambda _, __: (0.5, 0.5), "LAO", [("Calabarzon", None)], gazetteer, cache_dir) == []
