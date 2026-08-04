import pytest

from climate_risk.data_functions.disaster_point_data import make_synthetic_data_fpath


@pytest.mark.xfail(
    reason="the extension already carries its dot, so the name gains a stray underscore and never hits cache",
    raises=AssertionError,
)
def test_synthetic_filename_is_a_plain_csv(tmp_path):
    fpath = make_synthetic_data_fpath(tmp_path, "region", 1, "sea")

    assert fpath.name == "synthetic_non_disasters_region_times_1_sea.csv"


def test_synthetic_filename_varies_with_every_input(tmp_path):
    """A collision here silently serves one region's synthetic points for another."""
    names = {
        make_synthetic_data_fpath(tmp_path, by, multiplier, list_name).name
        for by in ("region", "country")
        for multiplier in (1, 2)
        for list_name in ("sea", "lao")
    }

    assert len(names) == 8
