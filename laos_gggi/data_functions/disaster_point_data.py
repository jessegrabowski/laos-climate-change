# ruff: noqa: E402

from pyprojroot import here
import sys

from laos_gggi.data_functions.shapefiles_data_loader import load_shapefile
from laos_gggi.data_functions.emdat_processing import load_emdat_data
from laos_gggi.data_functions.rivers_damage import load_rivers_data
from laos_gggi.statistics import get_distance_to

sys.path.insert(0, str(here()))

import pandas as pd  # noqa
import geopandas as gpd  # noqa
import os  # noqa
import numpy as np  # noqa

DATA_FOLDER = "data"
FPATH_RAW = here(
    os.path.join(DATA_FOLDER, "disaster_locations_gpt_repaired_w_features.csv")
)
FPATH_FEATURES = here(
    os.path.join(DATA_FOLDER, "disaster_locations_gpt_repaired_w_features.csv")
)

FPATH_SYNTHETIC_DATA = here(os.path.join(DATA_FOLDER, "synthetic_non_disasters.csv"))


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


def load_synthetic_non_disaster_points(rng=None, force_generate=False):
    if rng is None:
        seed = sum(map(ord, "Laos GGGI Climate Adaptation"))
        rng = np.random.default_rng(seed)

    if not os.path.exists(FPATH_SYNTHETIC_DATA) or force_generate:
        world = load_shapefile("world")
        coastline = load_shapefile("coastline")
        rivers = load_rivers_data()

        data = load_disaster_point_data().dropna(subset="Region")

        # "Melt" the world into 5 regions - Americas, Europe, Asia, Afria, Oceania. This corresponds with the
        # "Regions" column from EMDAT
        simple_world = (
            world.replace({"North America": "Americas", "South America": "Americas"})
            .query('CONTINENT != "Seven seas (open ocean)"')
            .dissolve("CONTINENT")
            .loc[data.Region.unique()]
        )

        # For every region, sample a random point for each disaster observed in that region
        not_disasters = (
            simple_world.sample_points(data.groupby("Region").size().values, rng=rng)
            .explode()
            .reset_index()
            .rename(columns={"CONTINENT": "Region", "sampled_points": "geometry"})
            .set_geometry("geometry")
        )

        # Compute geospatial features for the artifical data
        iso_dicts = [
            gpd.sjoin(world.loc[[i]], not_disasters, predicate="contains")[
                ["ISO_A3", "index_right"]
            ]
            .set_index("index_right")
            .to_dict()["ISO_A3"]
            for i in world.index
        ]
        island_dict = (
            data[["ISO", "is_island"]]
            .drop_duplicates()
            .set_index("ISO")
            .to_dict()["is_island"]
        )
        not_disasters = not_disasters.join(
            pd.Series({k: v for d in iso_dicts for k, v in d.items()}, name="ISO")
        )
        not_disasters["is_island"] = not_disasters["ISO"].map(island_dict.get)

        distances = get_distance_to(
            rivers, points=not_disasters, return_columns=["ORD_FLOW", "HYRIV_ID"]
        ).rename(columns={"distance_to_closest": "distance_to_river"})
        not_disasters = not_disasters.join(distances).assign(
            distance_to_river=lambda x: x.distance_to_river / 1000
        )

        distances = get_distance_to(
            coastline.boundary, points=not_disasters, return_columns=None
        ).rename(columns={"distance_to_closest": "distance_to_coastline"})
        not_disasters = not_disasters.join(distances).assign(
            distance_to_coastline=lambda x: x.distance_to_coastline / 1000
        )

        not_disasters["long"] = not_disasters.geometry.apply(lambda x: x.x)
        not_disasters["lat"] = not_disasters.geometry.apply(lambda x: x.y)

        # Match each synthetic datapoint with a real datapoint and save the "twin" index
        # Use this to merge more features (start date, disaster class) onto the fake data
        not_disasters.sort_values(by=["Region", "ISO"], inplace=True)
        not_disasters["twin_emdat_index"] = data.index.get_level_values(0)
        not_disasters["twin_location_id"] = data.index.get_level_values(1)
        not_disasters.sort_index().drop(columns=["geometry"]).to_csv(
            FPATH_SYNTHETIC_DATA
        )

    else:
        not_disasters = pd.read_csv(FPATH_SYNTHETIC_DATA, index_col=0)
        not_disasters["geometry"] = gpd.points_from_xy(
            not_disasters.long, not_disasters.lat
        )

        # EPSG:4326 is hard-coded so we don't have to load the data if this file exists! This might cause bugs :\
        not_disasters = gpd.GeoDataFrame(not_disasters, crs="EPSG:4326")

    return not_disasters
