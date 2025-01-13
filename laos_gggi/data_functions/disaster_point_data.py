# ruff: noqa: E402
from pyprojroot import here
import sys
import logging

from laos_gggi.data_functions.shapefiles_data_loader import load_shapefile
from laos_gggi.data_functions.emdat_processing import load_emdat_data
from laos_gggi.data_functions.rivers_damage import load_rivers_data
from laos_gggi.statistics import get_distance_to

sys.path.insert(0, str(here()))

import pandas as pd  # noqa
import geopandas as gpd  # noqa
import os  # noqa
import numpy as np  # noqa

_log = logging.getLogger(__name__)

DATA_FOLDER = "data"
FPATH_RAW = here(
    os.path.join(DATA_FOLDER, "disaster_locations_gpt_repaired_w_features.csv")
)
FPATH_FEATURES = here(
    os.path.join(DATA_FOLDER, "disaster_locations_gpt_repaired_w_features.csv")
)

SYNTHETIC_DATA_BASENAME = "synthetic_non_disasters.csv"


def load_data(fpath):
    data = pd.read_csv(fpath)
    data["geometry"] = gpd.points_from_xy(data.long, data.lat)
    data = gpd.GeoDataFrame(data, crs="EPSG:4326")

    return data


def _load_disaster_point_data():
    if os.path.exists(FPATH_FEATURES):
        data = load_data(FPATH_FEATURES)
    elif os.path.exists(FPATH_RAW):
        data = load_data(FPATH_RAW)
    else:
        raise ValueError("Go run the GPT notebook first!")

    return data


def load_disaster_point_data():
    modified_data = False

    # Load Laos shapefile
    emdat = load_emdat_data()
    data = _load_disaster_point_data()

    data = (
        data.set_index(["emdat_index"])
        .join(emdat["df_raw_filtered_adj"])
        .reset_index(drop=False)
        .rename(columns={"index": "emdat_index"})
        .set_index(["emdat_index", "location_id"])
    )

    if "distance_to_river" not in data.columns:
        rivers = load_rivers_data()

        distances = get_distance_to(
            rivers, points=data, return_columns=["ORD_FLOW", "HYRIV_ID"]
        ).rename(columns={"distance_to_closest": "distance_to_river"})
        data = data.join(distances).assign(
            distance_to_river=lambda x: x.distance_to_river / 1000
        )
        modified_data = True

    if "distance_to_coastline" not in data.columns:
        coastline = load_shapefile("coastline")
        distances = get_distance_to(
            coastline.boundary, points=data.loc[:, ["geometry"]]
        ).rename(columns={"distance_to_closest": "distance_to_coastline"})
        data = data.join(distances).assign(
            distance_to_coastline=lambda x: x.distance_to_coastline / 1000
        )
        modified_data = True

    if "is_island" not in data.columns:
        try:
            import wikipedia as wp
        except ImportError:
            raise ImportError(
                "You need to install the wikipedia package to get island data"
            )

        html = wp.page("List_of_island_countries").html().encode("UTF-8")
        island_table = (
            pd.read_html(html, skiprows=0)[0]
            .droplevel(axis=1, level=0)
            .dropna(how="all")
            .iloc[1:]
            .reset_index(drop=True)
            .assign(
                ISO_2=lambda x: x["ISO code"].str.split().str[0],
                ISO_3=lambda x: x["ISO code"].str.split().str[1].replace({"or": "GBR"}),
            )
        )
        data["is_island"] = data.ISO.isin(island_table.ISO_3)
        modified_data = True

    if modified_data:
        (
            data.drop(
                columns=emdat["df_raw_filtered_adj"].columns.tolist() + ["geometry"]
            ).to_csv(FPATH_FEATURES)
        )

    return data


def load_grid_point_data(
    region="laos", grid_size=400, iso_list: list = None, force_reload: bool = False
):
    if region not in ["laos", "sea", "custom"]:
        raise ValueError(f"Unknown grid: {region}")

    if region == "custom" and iso_list is None:
        raise ValueError("Must provide an iso_list for custom region")

    fname = f"{region}_points_{grid_size}.shp"
    folder_path = here(os.path.join(DATA_FOLDER, "shapefiles", fname))

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    fpath = os.path.join(folder_path, f"{fname}.shp")

    if os.path.exists(fpath) and not force_reload:
        _log.info(f"Loading data found at {fpath}")
        points = gpd.read_file(fpath)
        points = points.rename(
            columns={
                "distance_t": "distance_to_river",
                "distance_1": "distance_to_coastline",
                "log_distan": "log_distance_to_river",
                "log_dist_1": "log_distance_to_coastline",
            }
        )

    elif not os.path.exists(fpath) or force_reload:
        _log.info("Loading shapefiles and rivers data")
        world = load_shapefile("world")

        if region == "sea":
            iso_list = [
                "MMR",  # Myanmar
                "THA",  # Thailand
                "LAO",  # Laos
                "KHM",  # Cambodia
                "VNM",  # Vietnam
                "IDN",  # Indonesia
                "MYS",  # Malaysia
                "SGP",  # Singapore
                "PHL",  # Philippines
                "BRN",  # Brunei
                "TLS",  # Timor-Leste
            ]
        elif region == "laos":
            iso_list = ["LAO"]  #  noqa

        point_map = world.query("ISO_A3 in @iso_list")

        rivers = load_rivers_data()
        coastline = load_shapefile("coastline")

        _log.info("Computing point grid and features")
        lon_min, lat_min, lon_max, lat_max = point_map.dissolve().bounds.values.ravel()
        lon_grid = np.linspace(lon_min, lon_max, grid_size)
        lat_grid = np.linspace(lat_min, lat_max, grid_size)

        grid = np.column_stack([x.ravel() for x in np.meshgrid(lon_grid, lat_grid)])
        grid = gpd.GeoSeries(gpd.points_from_xy(*grid.T), crs="EPSG:4326")
        grid = gpd.GeoDataFrame({"geometry": grid})

        points = grid.overlay(point_map, how="intersection").geometry
        points = points.to_frame().assign(
            lon=lambda x: x.geometry.x, lat=lambda x: x.geometry.y
        )

        # Obtain distance with rivers
        distances_rivers = get_distance_to(
            rivers,
            points=points,
            return_columns=["ORD_FLOW", "HYRIV_ID"],
            name="rivers",
        ).rename(columns={"distance_to_closest": "distance_to_river"})

        points = pd.merge(
            points, distances_rivers, left_index=True, right_index=True, how="left"
        )

        # Obtain sea distance with coastlines
        distances_coastlines = get_distance_to(
            coastline.boundary, points=points, return_columns=None, name="coastline"
        ).rename(columns={"distance_to_closest": "distance_to_coastline"})

        points = pd.merge(
            points, distances_coastlines, left_index=True, right_index=True, how="left"
        )

        # Assign is_island column
        points["is_island"] = False

        # Create log of distances
        points = points.assign(
            log_distance_to_river=lambda x: np.log(x.distance_to_river)
        )
        points = points.assign(
            log_distance_to_coastline=lambda x: np.log(x.distance_to_coastline)
        )

        points.to_file(fpath)

    return points


def _sample_by_region(data, world, multiplier=1, rng=None):
    if rng is None:
        rng = np.random.default_rng()

    # "Melt" the world into 5 regions - Americas, Europe, Asia, Afria, Oceania. This corresponds with the
    # "Regions" column from EMDAT
    simple_world = (
        world.replace({"North America": "Americas", "South America": "Americas"})
        .query('CONTINENT != "Seven seas (open ocean)"')
        .dissolve("CONTINENT")
        .loc[data.Region.unique()]
    )
    disasters_per_region = data.groupby("Region").size().values * multiplier

    # For every region, sample a random point for each disaster observed in that region
    not_disasters = (
        simple_world.sample_points(disasters_per_region, rng=rng)
        .explode()
        .reset_index()
        .rename(columns={"CONTINENT": "Region", "sampled_points": "geometry"})
        .set_geometry("geometry")
    )

    not_disasters["ISO"] = (
        gpd.sjoin(world, not_disasters, predicate="contains")
        .sort_values(by="index_right")
        .ISO_A3.values
    )

    return not_disasters


def _sample_by_country(data, world, multiplier=1, rng=None):
    if rng is None:
        rng = np.random.default_rng()

    simple_world = (
        world.replace({"North America": "Americas", "South America": "Americas"})
        .query('CONTINENT != "Seven seas (open ocean)"')
        .dissolve("CONTINENT")
        .loc[data.Region.unique()]
    )

    world_subset = (
        world.query("ISO_A3 in @data.ISO.unique()").set_index("ISO_A3").sort_index()
    )
    disasters_per_country = data.groupby("ISO").size().sort_index() * multiplier

    not_disasters = (
        world_subset.sample_points(disasters_per_country, rng=rng)
        .explode()
        .reset_index()
        .rename(columns={"ISO_A3": "ISO", "sampled_points": "geometry"})
        .set_geometry("geometry")
    )

    not_disasters = not_disasters.join(
        gpd.sjoin(simple_world.reset_index(), not_disasters, predicate="contains")
        .sort_values(by="index_right")
        .set_index("index_right")
        .CONTINENT
    )

    return not_disasters.rename(columns={"CONTINENT": "Region"})


def make_synthetic_data_fpath(by, multipler):
    name, ext = os.path.splitext(SYNTHETIC_DATA_BASENAME)
    fname = f"{name}_{by}_times_{multipler}{ext}"

    return here(os.path.join(DATA_FOLDER, fname))


def load_synthetic_non_disaster_points(
    rng=None, force_generate=False, by="region", multiplier=1
):
    if rng is None:
        seed = sum(map(ord, "Laos GGGI Climate Adaptation"))
        rng = np.random.default_rng(seed)

    fpath = make_synthetic_data_fpath(by, multiplier)

    if not os.path.exists(fpath) or force_generate:
        world = load_shapefile("world")
        coastline = load_shapefile("coastline")
        rivers = load_rivers_data()

        data = load_disaster_point_data().dropna(subset="Region")

        if by == "region":
            _log.info("Sampling non-disasters by region")
            not_disasters = _sample_by_region(
                data, world, multiplier=multiplier, rng=rng
            )
        elif by == "country":
            _log.info("Sampling non-disasters by country")
            not_disasters = _sample_by_country(
                data, world, multiplier=multiplier, rng=rng
            )
        else:
            raise ValueError(f"Unknown value for `by`: {by}")

        _log.info("Adding geospatial features to synthetic data")

        island_dict = (
            data[["ISO", "is_island"]]
            .drop_duplicates()
            .set_index("ISO")
            .to_dict()["is_island"]
        )
        not_disasters["is_island"] = not_disasters["ISO"].map(island_dict.get)

        distances = get_distance_to(
            rivers,
            points=not_disasters,
            return_columns=["ORD_FLOW", "HYRIV_ID"],
            name="rivers",
        ).rename(columns={"distance_to_closest": "distance_to_river"})
        not_disasters = not_disasters.join(distances).assign(
            distance_to_river=lambda x: x.distance_to_river / 1000
        )

        distances = get_distance_to(
            coastline.boundary,
            points=not_disasters,
            return_columns=None,
            name="coastline",
        ).rename(columns={"distance_to_closest": "distance_to_coastline"})
        not_disasters = not_disasters.join(distances).assign(
            distance_to_coastline=lambda x: x.distance_to_coastline / 1000
        )

        not_disasters["long"] = not_disasters.geometry.apply(lambda x: x.x)
        not_disasters["lat"] = not_disasters.geometry.apply(lambda x: x.y)

        not_disasters.sort_values(by=["ISO"], inplace=True)
        not_disasters["Start_Year"] = np.random.choice(
            data.Start_Year.unique(), size=not_disasters.shape[0], replace=True
        )
        not_disasters.reset_index(inplace=True, drop=True)

        not_disasters.sort_index().drop(columns=["geometry"]).to_csv(fpath)

    else:
        _log.info(f"Loading data found at {fpath}")
        not_disasters = pd.read_csv(fpath, index_col=0)
        not_disasters["geometry"] = gpd.points_from_xy(
            not_disasters.long, not_disasters.lat
        )
        not_disasters["Start_Year"] = pd.to_datetime(not_disasters["Start_Year"])

        # EPSG:4326 is hard-coded so we don't have to load the data if this file exists! This might cause bugs :\
        not_disasters = gpd.GeoDataFrame(not_disasters, crs="EPSG:4326")

    return not_disasters
