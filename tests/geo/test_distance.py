import geopandas as gpd

from shapely.geometry import LineString

from climate_risk.geo.distance import get_distance_to


def test_distance_is_measured_in_metres_of_the_projected_crs(grid_points):
    """to_km only holds while the CRS is metric, and every caller runs the default parallel path."""
    rivers = gpd.GeoDataFrame(
        {"ORD_FLOW": [4], "HYRIV_ID": [1], "geometry": [LineString([(0, -1), (0, 2)])]}, crs="EPSG:4326"
    )

    distances = get_distance_to(rivers, points=grid_points)["distance_to_closest"]

    assert distances.iloc[0] > 10_000
    assert distances.iloc[0] < distances.iloc[1]


def test_requested_columns_come_from_the_nearest_feature(grid_points):
    far = LineString([(50, 50), (50, 51)])
    near = LineString([(0, -1), (0, 2)])
    rivers = gpd.GeoDataFrame({"ORD_FLOW": [9, 4], "HYRIV_ID": [99, 1], "geometry": [far, near]}, crs="EPSG:4326")

    nearest = get_distance_to(rivers, points=grid_points, return_columns=["ORD_FLOW", "HYRIV_ID"], n_cores=1)

    assert nearest["HYRIV_ID"].tolist() == [1, 1]
    assert nearest["ORD_FLOW"].tolist() == [4, 4]
