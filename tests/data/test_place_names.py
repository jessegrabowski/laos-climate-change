import csv

from collections import defaultdict

import pytest

from climate_risk.data.place_names import (
    CONTAINED_BY,
    CORRECTED,
    LOCATED,
    NAME_CORRECTIONS,
    NAMED,
    Placement,
    Unit,
    match_key,
    name_shapes,
    nearest_name,
    read_gazetteer,
    read_name_corrections,
    resolve_event_places,
    resolve_place,
    successor_state,
)


@pytest.mark.parametrize(
    ("written", "published"),
    [
        ("Kalin-Aapayo province", "Kalin Aapayo"),
        ("Ron Phibun districts", "Ron Phibun"),
        ("Luzon Isl.", "Luzon"),
        ("Đà Nẵng city", "Da Nang"),
    ],
    ids=["province", "plural district", "abbreviated island", "transliterated"],
)
def test_a_written_mention_and_a_published_name_reach_the_same_key(written, published):
    """EM-DAT says what kind of unit it means and GADM does not, so the noun has to come off before
    the two can meet."""
    assert match_key(written) == match_key(published)


def test_a_name_that_is_only_a_unit_noun_reaches_nothing():
    """`districts` on its own is what a trailing separator leaves behind. Keyed on the empty string
    it would collide with every other such fragment and match whatever came first."""
    assert match_key("districts") == ""


def test_units_are_indexed_under_every_name_they_are_published_under(write_gadm_cache):
    """GADM carries a variant name for many units, and EM-DAT writes whichever it has."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert Unit("LAO.1_1", 1, None) in gazetteer.names[match_key("Attapu")]
    assert gazetteer.names[match_key("Attopeu")] == {Unit("LAO.1_1", 1, None)}, "the variant name reaches the same unit"
    assert gazetteer.names[match_key("Houei Sai")] == {Unit("LAO.2.1_1", 2, "LAO.2_1")}, "one of two piped variants"


def test_every_level_the_archive_publishes_is_indexed(write_gadm_cache):
    """A location string names provinces, districts and villages in one breath, and stopping at
    adm2 loses the finest of them: adm3 and adm4 carry a fifth of everything that resolves."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert Unit("LAO.1.1.1_1", 3, "LAO.1.1_1") in gazetteer.names[match_key("Ban Mai")]


def test_a_district_knows_the_province_holding_it(write_gadm_cache):
    """Parentage decides which of two same-named units a container selects, so it has to come from
    the row rather than from the shape of the identifier: 37 GADM rows do not nest."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert {unit.parent for unit in gazetteer.names[match_key("Houayxay")]} == {"LAO.2_1"}


def test_a_repeated_name_reaches_every_unit_that_carries_it(write_gadm_cache):
    """A name is not an identifier: Attapu is a province and, elsewhere, a district of Bokeo.
    Keeping whichever unit was read first would silently pick one and look decisive about it."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Attapu", None, gazetteer) == {"LAO.1_1", "LAO.2.2_1"}


def test_a_container_chooses_between_units_sharing_a_name(write_gadm_cache):
    """The container is what the location prose buys over a bare name match. Without it the choice
    between same-named units is a similarity threshold, which is the approach this project rejected."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Attapu", "Bokeo", gazetteer) == {"LAO.2.2_1"}, "the district inside Bokeo"


def test_a_container_naming_nothing_leaves_the_candidates_alone(write_gadm_cache):
    """The prose routinely names a region GADM does not model — `Calabarzon`, `Bicol` — and an
    unrecognised container is missing information, not evidence against the candidates."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Sanamxay", "Some Region GADM Never Heard Of", gazetteer) == {"LAO.1.1_1"}


def test_a_container_holding_none_of_the_candidates_leaves_them_alone(write_gadm_cache):
    """EM-DAT's containers are sometimes wrong or coarser than GADM's hierarchy. Dropping every
    candidate would turn a mistaken container into a lost place."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Sanamxay", "Bokeo", gazetteer) == {"LAO.1.1_1"}


def test_a_name_no_unit_carries_reaches_nothing(write_gadm_cache):
    """Two fifths of written places name no GADM unit at all, and the caller has to tell that from
    a match."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Calabarzon", None, gazetteer) == set()


def test_a_seat_named_after_its_district_resolves_to_the_district(write_gadm_cache):
    """Two thirds of ambiguous mentions are one nesting chain, not two places. The district is the
    whole of what the mention can mean, and returning the seat beside it invents a choice."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Samakhixay", None, gazetteer) == {"LAO.1.2_1"}


def test_a_container_reaches_past_the_level_directly_below_it(write_gadm_cache):
    """Prose names the province and then a village, skipping the district between them, so a
    container matched against the immediate parent alone would discard the village."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Ban Mai", "Attapu", gazetteer) == {"LAO.1.1.1_1"}


def test_an_unambiguous_place_narrows_the_ambiguous_ones_beside_it(write_gadm_cache):
    """An event's places share a footprint. Resolving each alone throws that away and leaves
    Attapu split between a province and a district in the province the event is plainly in."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_event_places([("Houayxay", None), ("Attapu", None)], gazetteer) == [
        Placement({"LAO.2.1_1"}, NAMED),
        Placement({"LAO.2.2_1"}, NAMED),
    ]


def test_an_event_pinning_nothing_leaves_its_places_alone(write_gadm_cache):
    """Half the ambiguous mentions sit in events where nothing resolves uniquely, and narrowing
    against an empty envelope would drop every candidate."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_event_places([("Attapu", None), ("Calabarzon", None)], gazetteer) == [
        Placement({"LAO.1_1", "LAO.2.2_1"}, NAMED),
        Placement(set(), NAMED),
    ]


def test_a_country_the_archive_does_not_cover_reads_back_empty(write_gadm_cache):
    """EM-DAT codes states GADM never modeled — Serbia and Montenegro, the USSR — and a caller
    walking every ISO in the workbook reaches them."""
    gazetteer = read_gazetteer("SCG", write_gadm_cache())

    assert gazetteer.names == {}
    assert resolve_place("Beograd", None, gazetteer) == set()


def test_a_unit_the_archive_nests_inside_itself_is_read_as_containing_nothing(write_gadm_cache):
    """GADM writes an unnamed Ukrainian unit as `?` at two levels, which reads as its own container
    and makes every walk over parentage non-terminating. The reader is where that has to stop."""
    gazetteer = read_gazetteer("UKR", write_gadm_cache())

    assert gazetteer.parent_of["?"] is None
    assert gazetteer.ancestry("?") == {"?"}


@pytest.mark.parametrize(
    ("written", "published"),
    [
        ("Bengkulu area", "Bengkulu"),
        ("Cagayan Prov.", "Cagayan"),
        ("City of Bandung", "Bandung"),
        ("Near Villavicencio", "Villavicencio"),
        ("Coast of Zamboanga", "Zamboanga"),
    ],
    ids=["area", "abbreviated province", "city of", "near", "coast of"],
)
def test_a_decorated_mention_reaches_the_published_name(written, published):
    """A fifth of the names nothing matches are a published name with a word like this attached."""
    assert match_key(written) == match_key(published)


def test_a_conjunction_reaches_both_places_it_joins(write_gadm_cache):
    """EM-DAT writes a run of provinces joined by `and`, and refusing to split leaves every one of
    them unplaced."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Sanamxay and Samakhixay", None, gazetteer) == {"LAO.1.1_1", "LAO.1.2_1"}


def test_a_unit_whose_own_name_carries_a_conjunction_survives(write_gadm_cache):
    """Splitting `Newfoundland and Labrador` destroys the province it names, so the whole string
    has to be tried before its parts."""
    gazetteer = read_gazetteer("CAN", write_gadm_cache())

    assert resolve_place("Newfoundland and Labrador", None, gazetteer) == {"CAN.5_1"}


def test_a_conjunction_keeps_whichever_parts_name_something(write_gadm_cache):
    """EM-DAT joins a place it spelled well to one it spelled badly. Discarding both because one
    failed throws away geography the prose plainly gives."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Nowhere At All and Sanamxay", None, gazetteer) == {"LAO.1.1_1"}


def test_a_place_named_between_two_others_is_in_neither(write_gadm_cache):
    """`Between Java and Bali` is a stretch of sea named by its shores. Splitting it puts the event
    on whichever shore resolves, which is a coastline away from where it happened."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_place("Between Bokeo and Sanamxay", None, gazetteer) == set()


def test_a_place_naming_nothing_falls_back_to_the_container_it_was_written_in(write_gadm_cache):
    """A third of the events still unplaced name a container that resolves — `Pesisir Selaten (West
    Sumatra province)` gives the province even where the district is unrecognisable."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_event_places([("Nowhere At All", "Bokeo")], gazetteer) == [Placement({"LAO.2_1"}, CONTAINED_BY)]


def test_a_container_standing_in_for_a_place_is_marked_as_coarser(write_gadm_cache):
    """The province is not what the prose named, and a caller aggregating footprints has to be able
    to tell a district it asked for from the province it settled for."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    named, fallen_back = resolve_event_places([("Sanamxay", None), ("Nowhere At All", "Bokeo")], gazetteer)

    assert (named.how, fallen_back.how) == (NAMED, CONTAINED_BY)


def test_a_container_standing_in_for_a_place_is_narrowed_like_any_other(write_gadm_cache):
    """`Attapu` names a province and a district elsewhere. Falling back to it without the narrowing
    a named place gets would hand back both, when the event has already pinned which one."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    _, fallen_back = resolve_event_places([("Houayxay", None), ("Nowhere At All", "Attapu")], gazetteer)

    assert fallen_back == Placement({"LAO.2.2_1"}, CONTAINED_BY), "the district inside the pinned province"


def test_a_unit_below_a_province_names_the_province_as_its_outermost(write_gadm_cache):
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert gazetteer.top_container("LAO.1.1.1_1") == "LAO.1_1"


def test_the_outermost_container_of_the_placeholder_unit_is_itself(write_gadm_cache):
    """Walking outwards from a unit the archive nests inside itself must still reach a top."""
    gazetteer = read_gazetteer("UKR", write_gadm_cache())

    assert gazetteer.top_container("?") == "?"


def test_a_point_is_preferred_to_the_container_a_place_was_written_in(write_gadm_cache):
    """The container claims every unit inside it. A point names one, so it wins wherever it exists:
    over half the places that fall back to a container have one."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    (placed,) = resolve_event_places([("Nowhere At All", "Bokeo")], gazetteer, located={"Nowhere At All": "LAO.2.1_1"})

    assert placed == Placement({"LAO.2.1_1"}, LOCATED), "the district, not the whole of Bokeo"


def test_a_place_its_own_name_reaches_ignores_the_point_offered_for_it(write_gadm_cache):
    """A name GADM publishes is better evidence than a coordinate somebody geocoded from it."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    (placed,) = resolve_event_places([("Sanamxay", None)], gazetteer, located={"Sanamxay": "LAO.2.1_1"})

    assert placed == Placement({"LAO.1.1_1"}, NAMED)


def test_a_misspelling_reaches_the_name_it_misspells(write_gadm_cache):
    """Misspellings are the largest thing left that no gazetteer places: `Barrranquilla`,
    `Marizales`, `Santa Rose de Cabal`."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert nearest_name("Sanamxai", gazetteer, name_shapes(gazetteer)) == "sanamxay"


def test_a_name_equally_close_to_two_published_names_reaches_neither(write_gadm_cache):
    """Two names one edit away is not a near miss, it is a choice. `Bocolod` sits one edit from
    both Bacolod the city and Boclod the barangay, and picking either looks equally confident."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert nearest_name("Attopu", gazetteer, name_shapes(gazetteer)) is None, "one edit from both Attapu and Attopeu"


def test_a_name_too_short_to_misspell_is_refused(write_gadm_cache):
    """One edit in a five-letter name changes too much of it to call the rest a match."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert nearest_name("Bokea", gazetteer, name_shapes(gazetteer)) is None


def test_a_physical_feature_is_never_taken_for_a_unit_it_resembles(write_gadm_cache):
    """A bay is not an administrative unit however close its name sits to one. Units named after a
    feature still match exactly; only the approximate lookup refuses them."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert nearest_name("Nambok", gazetteer, name_shapes(gazetteer)) == "nambak", (
        "the same unit is reachable by a plain misspelling"
    )
    assert nearest_name("Nam Bay", gazetteer, name_shapes(gazetteer)) is None


def test_a_name_that_already_matches_is_not_approximated(write_gadm_cache):
    """An exact match is the answer, and offering a near one beside it would let a misspelling of
    some other place override a name GADM publishes."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert nearest_name("Sanamxay", gazetteer, name_shapes(gazetteer)) is None


def test_a_name_two_edits_away_is_not_a_misspelling_of_it(write_gadm_cache):
    """One slip is a misspelling. At two, `Sanamxay` and a different district are equally far, and
    the match is a guess dressed as a correction."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert nearest_name("Sanamxii", gazetteer, name_shapes(gazetteer)) is None


def test_a_checked_misspelling_reaches_the_unit_it_stands_for(write_gadm_cache):
    """Approximate matching proposes corrections; only the ones written into the table are applied."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())._replace(corrections={"sanamxai": "sanamxay"})

    assert resolve_event_places([("Sanamxai", None)], gazetteer) == [Placement({"LAO.1.1_1"}, CORRECTED)]


def test_a_misspelling_nobody_checked_is_left_unplaced(write_gadm_cache):
    """One edit from a published name is a proposal, not a correction: `Lynmouth` sits one edit from
    Lynemouth, four hundred miles away."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())

    assert resolve_event_places([("Sanamxai", None)], gazetteer) == [Placement(set(), NAMED)]


def test_a_container_is_preferred_to_a_checked_misspelling(write_gadm_cache):
    """The container is coarse but certain. A wrong district is worse for a damage estimate than a
    correct province."""
    gazetteer = read_gazetteer("LAO", write_gadm_cache())._replace(corrections={"sanamxai": "sanamxay"})

    (placed,) = resolve_event_places([("Sanamxai", "Bokeo")], gazetteer)

    assert placed == Placement({"LAO.2_1"}, CONTAINED_BY)


def test_a_correction_is_read_only_for_the_country_that_declares_it(write_gadm_cache, tmp_path):
    """The same written name means different places in different countries, and a table keyed only
    on the name would carry one country's correction into every other."""
    table = tmp_path / "corrections.csv"
    table.write_text("iso,written,corrected\nLAO,Sanamxai,sanamxay\nZMB,Sanamxai,kabwe\n", encoding="utf-8")

    assert read_name_corrections("LAO", path=table) == {"sanamxai": "sanamxay"}


def test_a_correction_the_table_leaves_blank_is_not_applied(write_gadm_cache, tmp_path):
    """A row can record that a candidate was checked and rejected; that is not a correction."""
    table = tmp_path / "corrections.csv"
    table.write_text("iso,written,corrected\nLAO,Lynmouth,\n", encoding="utf-8")

    assert read_name_corrections("LAO", path=table) == {}


def test_no_country_corrects_one_name_to_two_different_units(write_gadm_cache):
    """`Badakhstan` and `Badakhstan province` reduce to one key, which is fine while they agree.
    Two rows disagreeing would resolve on file order, and the table is curated by hand."""
    targets: dict[tuple[str, str], set[str]] = defaultdict(set)
    with NAME_CORRECTIONS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            targets[(row["iso"], match_key(row["written"]))].add(row["corrected"])

    conflicting = {key: sorted(published) for key, published in targets.items() if len(published) > 1}

    assert not conflicting, f"one name corrected two ways: {sorted(conflicting.items())[:5]}"


def test_a_state_with_one_successor_needs_no_evidence(write_gadm_cache):
    """East and West Germany both became Germany, so their events need no disambiguating at all."""
    assert successor_state([], "DFR", write_gadm_cache()) == "DEU"


def test_the_successor_holding_the_places_takes_the_event(write_gadm_cache):
    """A Czechoslovak flood naming Prague is Czech. EM-DAT files 417 events under states GADM no
    longer models, and the location text is the only thing that says where they happened."""
    cache_dir = write_gadm_cache()

    assert successor_state([("Praha", None)], "CSK", cache_dir) == "CZE"
    assert successor_state([("Bratislavsky", None)], "CSK", cache_dir) == "SVK"


def test_a_name_both_successors_publish_settles_nothing(write_gadm_cache):
    """Czechia and Slovakia both have a Nové Město. Taking whichever was read first would put the
    event in a country on alphabetical order alone."""
    assert successor_state([("Nove Mesto", None)], "CSK", write_gadm_cache()) is None


def test_the_only_successor_in_the_archive_still_has_to_place_something(write_gadm_cache):
    """Being the sole candidate is not evidence. Assigning the event to the largest successor would
    put every Soviet flood in Russia by default."""
    assert successor_state([("Nowhere At All", None)], "YUG", write_gadm_cache()) is None


def test_a_state_whose_successors_place_nothing_stays_unplaced(write_gadm_cache):
    assert successor_state([("Nowhere At All", None)], "CSK", write_gadm_cache()) is None


def test_a_country_that_still_exists_has_no_successor(write_gadm_cache):
    """The mapping covers dissolved states only; anything else is read from its own gazetteer."""
    assert successor_state([("Sanamxay", None)], "LAO", write_gadm_cache()) is None


def test_a_gazetteer_covers_the_territory_its_country_administers(write_gadm_cache):
    """Fifty-five Indian and twenty-nine Pakistani events name places in Kashmir, which GADM holds
    at the right coordinates under a code neither country's own gazetteer reads."""
    gazetteer = read_gazetteer("IND", write_gadm_cache())

    assert resolve_place("Srinagar", None, gazetteer) == {"Z01.1.1_1"}
    assert resolve_place("Kochi", None, gazetteer) == {"IND.1.1_1"}
