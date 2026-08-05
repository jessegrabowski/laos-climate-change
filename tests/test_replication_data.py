import numpy as np
import pytest

from climate_risk.replication_data import create_replication_data


@pytest.fixture
def replication(write_full_cache):
    return create_replication_data(write_full_cache())


def exactly_one_row(replication, iso, year):
    """Rows exist for every country-year in the window; only a few carry World Bank data."""
    match = replication[(replication["ISO"] == iso) & (replication["year"] == year)]
    assert len(match) == 1
    return match.iloc[0]


def test_one_row_per_country_year(replication):
    assert not replication.duplicated(subset=["ISO", "year"]).any()
    assert sorted(replication["ISO"].unique()) == ["AAA", "BBB", "EEE"]


def test_population_is_reported_in_millions(replication):
    """The regressor is in millions; the World Bank supplies raw headcounts."""
    assert exactly_one_row(replication, "AAA", "1990")["population"] == pytest.approx(1.0)


def test_log_gdp_and_its_square_agree(replication):
    known = replication.dropna(subset=["ln_gdp_pc", "ln_population_density"])

    assert len(known) > 0
    assert (known["square_ln_gdp_pc"] == known["ln_gdp_pc"] ** 2).all()
    assert (known["ln_population_density_squared"] == known["ln_population_density"] ** 2).all()


def test_log_gdp_uses_gdp_per_capita(replication):
    assert exactly_one_row(replication, "AAA", "1990")["ln_gdp_pc"] == pytest.approx(np.log(1000.0))


def test_the_time_trend_is_decades_since_1980(replication):
    """A raw year would dwarf every other regressor; the trend is rescaled."""
    trends = replication.set_index("year")["time_period"]

    assert trends.loc["1990"].iloc[0] == pytest.approx(0.1)
    assert trends.loc["1991"].iloc[0] == pytest.approx(0.11)


def test_damage_totals_sum_the_two_classes(replication):
    both = replication.dropna(subset=["Total_Damage_Adjusted_hydro", "Total_Damage_Adjusted_clim"])

    assert len(both) > 0
    expected = both["Total_Damage_Adjusted_hydro"] + both["Total_Damage_Adjusted_clim"]
    assert (both["Total_Damage_Adjusted_all"] == expected).all()


def test_a_country_year_with_no_disasters_stays_missing(replication):
    """nan_or_sum keeps no-data distinct from no-disasters, which a zero would erase."""
    quiet = replication[replication["year"] == "1985"]

    assert len(quiet) > 0
    assert quiet["hydrological_disasters"].isna().all()
