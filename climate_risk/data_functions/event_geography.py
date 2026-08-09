from pathlib import Path

import geopandas as gpd
import pandas as pd

from climate_risk.config.schema import EventFilters
from climate_risk.data_functions.emdat_processing import event_filter, load_emdat_events
from climate_risk.data_functions.rivers_damage import load_rivers_data
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile
from climate_risk.geo.crs import GEOGRAPHIC_CRS, to_km
from climate_risk.geo.distance import get_distance_to
from climate_risk.geo.island_countries import ISLAND_COUNTRY_ISO3

# The geocoded points join to the workbook on the event id. A row number does not survive a
# re-download: EM-DAT inserts historical records, so position moves and the join goes silently wrong.
EVENT_KEY = "DisNo."


def disaster_points_path(cache_dir: Path) -> Path:
    return cache_dir / "disaster_locations_gpt_repaired_w_features.csv"


def read_cached_points(fpath: Path) -> pd.DataFrame:
    """Read a cached point CSV, normalising a `long` column to `lon`."""
    # Remove once no cache on disk spells it long.
    frame = pd.read_csv(fpath)

    return frame if "lon" in frame.columns else frame.rename(columns={"long": "lon"})


def load_data(fpath: Path) -> gpd.GeoDataFrame:
    data = read_cached_points(fpath)
    data["geometry"] = gpd.points_from_xy(data.lon, data.lat)
    data = gpd.GeoDataFrame(data, crs=GEOGRAPHIC_CRS)

    return data


def _load_disaster_point_data(cache_dir: Path) -> gpd.GeoDataFrame:
    path = disaster_points_path(cache_dir)
    if not path.exists():
        raise ValueError(f"No geocoded disaster locations at {path}. Go run the GPT notebook first!")

    data = load_data(path)
    if EVENT_KEY not in data.columns:
        raise ValueError(
            f"`{path}` has no `{EVENT_KEY}` column, so it is keyed on the workbook's row order. "
            "Row numbers do not survive a re-download — EM-DAT inserts historical records, which "
            "moves every later row and silently attaches each point to the wrong event. Re-key the "
            "file against the workbook vintage it was built from before loading it."
        )

    # The workbook row number a file written before the re-key still carries. It identifies nothing
    # across downloads, and it collides with the same column on the workbook side.
    return data.drop(columns="emdat_index", errors="ignore")


def load_disaster_point_data(cache_dir: Path) -> gpd.GeoDataFrame:
    """
    Read the geocoded disaster points and attach the EM-DAT event each one belongs to.

    Distance features absent from the file are computed and written back into it.

    Parameters
    ----------
    cache_dir : Path
        Directory holding the geocoded point file and the EM-DAT workbook.

    Returns
    -------
    GeoDataFrame
        One row per event-location, indexed by ``DisNo.`` and ``location_id``.

    Raises
    ------
    ValueError
        If the point file is absent, or is keyed on row order rather than on ``DisNo.``.
    """
    modified_data = False

    events = load_emdat_events(cache_dir).filter(event_filter(EventFilters())).to_pandas().set_index(EVENT_KEY)
    data = _load_disaster_point_data(cache_dir)

    data = data.set_index([EVENT_KEY]).join(events).reset_index(drop=False).set_index([EVENT_KEY, "location_id"])

    if "distance_to_river" not in data.columns:
        rivers = load_rivers_data(cache_dir)

        distances = get_distance_to(rivers, points=data, return_columns=["ORD_FLOW", "HYRIV_ID"]).rename(
            columns={"distance_to_closest": "distance_to_river"}
        )
        data = data.join(distances).assign(distance_to_river=lambda x: to_km(x.distance_to_river))
        modified_data = True

    if "distance_to_coastline" not in data.columns:
        coastline = load_shapefile("coastline", cache_dir)
        distances = get_distance_to(coastline.boundary, points=data.loc[:, ["geometry"]]).rename(
            columns={"distance_to_closest": "distance_to_coastline"}
        )
        data = data.join(distances).assign(distance_to_coastline=lambda x: to_km(x.distance_to_coastline))
        modified_data = True

    if "is_island" not in data.columns:
        data["is_island"] = data.ISO.isin(ISLAND_COUNTRY_ISO3)
        modified_data = True

    if modified_data:
        (data.drop(columns=[*events.columns.tolist(), "geometry"]).to_csv(disaster_points_path(cache_dir)))

    return data
