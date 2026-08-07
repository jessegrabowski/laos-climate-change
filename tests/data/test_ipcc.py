import pandas as pd
import pytest

from climate_risk.data.ipcc import IPCC_FILE, IPCC_SHEET, SCENARIO_COLUMNS, transform_ipcc

# The published series runs five-yearly and the projection ends in 2100. Stated literally, not
# imported, so a changed constant fails instead of moving the expectation with it.
STEP_YEARS = 5
FIRST_PROJECTED_YEAR = 2020
LAST_PROJECTED_YEAR = 2100

SCENARIOS = ["SSP1-19", "SSP1-26", "SSP2-45", "SSP3-70", "SSP5-85"]
PUBLISHED_YEARS = list(range(2015, 2106, STEP_YEARS))


@pytest.fixture
def scenarios():
    """One unit of change per five-year step, so accumulated levels are countable by hand."""
    return pd.DataFrame({"year": PUBLISHED_YEARS} | {name: [1.0] * len(PUBLISHED_YEARS) for name in SCENARIOS})


@pytest.fixture
def co2_observations():
    return pd.DataFrame(
        {"co2": [400.0] * len(PUBLISHED_YEARS)},
        index=pd.Index(pd.to_datetime([f"{year}-01-01" for year in PUBLISHED_YEARS]), name="year"),
    )


def test_the_anchor_years_take_the_observed_level(scenarios, co2_observations):
    """The published series holds changes, so the levels have to start somewhere real."""
    levels = transform_ipcc(scenarios, co2_observations)

    assert levels.loc[FIRST_PROJECTED_YEAR, "SSP1-19"] == 400.0


def test_changes_accumulate_from_the_anchor(scenarios, co2_observations):
    levels = transform_ipcc(scenarios, co2_observations)

    assert levels.loc[2025, "SSP1-19"] == pytest.approx(401.0)
    assert levels.loc[2030, "SSP1-19"] == pytest.approx(402.0)


def test_the_five_yearly_series_becomes_annual(scenarios, co2_observations):
    levels = transform_ipcc(scenarios, co2_observations)

    assert levels.index.tolist() == list(range(FIRST_PROJECTED_YEAR, LAST_PROJECTED_YEAR + 1))


def test_the_years_between_steps_are_interpolated(scenarios, co2_observations):
    """A published point every five years, so the intervening levels are straight lines."""
    levels = transform_ipcc(scenarios, co2_observations)

    assert levels.loc[2027, "SSP1-19"] == pytest.approx(401.4)


def test_the_observed_column_does_not_survive(scenarios, co2_observations):
    """`co2` is the anchor, not a scenario; leaving it in would read as a sixth pathway."""
    levels = transform_ipcc(scenarios, co2_observations)

    assert "co2" not in levels.columns


def test_the_index_is_named_so_the_cache_can_round_trip(scenarios, co2_observations):
    """`pandas_csv(index_col="year")` cannot restore an index the writer left unnamed."""
    levels = transform_ipcc(scenarios, co2_observations)

    assert levels.index.name == "year"


def test_every_scenario_is_carried_through(scenarios, co2_observations):
    levels = transform_ipcc(scenarios, co2_observations)

    assert set(SCENARIOS) <= set(levels.columns)


def test_a_missing_observation_leaves_the_level_missing(scenarios, co2_observations):
    """Anchoring on a year the observations do not cover must not invent a level."""
    without_anchor = co2_observations.drop(index=pd.Timestamp(f"{FIRST_PROJECTED_YEAR}-01-01"))

    levels = transform_ipcc(scenarios, without_anchor)

    assert pd.isna(levels.loc[FIRST_PROJECTED_YEAR, "SSP1-19"])


def test_the_vendored_workbook_carries_what_the_loader_reads():
    """The workbook ships with the package, so replacing it must not quietly change what is read."""
    published = pd.read_excel(IPCC_FILE, sheet_name=IPCC_SHEET)

    assert set(SCENARIO_COLUMNS) <= set(published.columns)
    assert published["Panel emissions - SSP1-19 - x (year)"].tolist() == list(range(2015, 2101, STEP_YEARS))
