from climate_risk.data.placement import available_geocoders


def test_a_gazetteer_of_settlements_is_asked_before_a_gazetteer_of_everything(write_geonames_cache, write_osm_cache):
    """GeoNames rows are populated places, so a name it knows is a settlement. Nominatim answers
    with whatever carries the name, which is worth having only where GeoNames has nothing."""
    write_geonames_cache()
    cache_dir = write_osm_cache([("bacolod", "Bacolod", 0.0, 0.0, "place", "village")], iso="PHL")

    first, _ = available_geocoders("PHL", cache_dir)

    assert first("PHL", "Bacolod") == (122.95, 10.667), "the GeoNames city, not the OSM point"


def test_a_name_geonames_has_no_row_for_reaches_the_openstreetmap_point(write_geonames_cache, write_osm_cache):
    """The whole reason for the second source: two thirds of what stays unplaced has no GeoNames
    row at all."""
    write_geonames_cache()
    cache_dir = write_osm_cache([("dzidzole", "Dzidzole", 1.23, 6.16, "place", "village")], iso="PHL")

    answers = [point for locate in available_geocoders("PHL", cache_dir) if (point := locate("PHL", "Dzidzole"))]

    assert answers == [(1.23, 6.16)]


def test_a_country_with_no_geonames_dump_still_offers_openstreetmap(write_geonames_cache, write_osm_cache):
    """GeoNames files its dumps by country and does not publish one for every country. A source
    that cannot answer has to step aside, not take the country's other points down with it."""
    write_geonames_cache(alpha2="PH", alpha3="PHL")
    cache_dir = write_osm_cache([("dzidzole", "Dzidzole", 1.23, 6.16, "place", "village")], iso="LAO")

    (only,) = available_geocoders("LAO", cache_dir)

    assert only("LAO", "Dzidzole") == (1.23, 6.16)
