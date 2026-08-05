import pytest

from climate_risk import load_synthetic_non_disaster_points
from climate_risk.data_functions.disaster_point_data import make_synthetic_data_fpath


def test_synthetic_filename_is_a_plain_csv(tmp_path):
    fpath = make_synthetic_data_fpath(tmp_path, "region", 1, "sea")

    assert fpath.name == "synthetic_non_disasters_region_times_1_sea.csv"


def test_unknown_sampling_strategy_is_rejected(tmp_path):
    """An unknown `by` once fell through both branches and failed on an unbound name."""
    with pytest.raises(ValueError, match="by should be one of"):
        load_synthetic_non_disaster_points(tmp_path, ["LAO"], "sea", by="continent")
