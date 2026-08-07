import itertools
import logging

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from climate_risk.data_functions.emdat_processing import load_emdat_data
from climate_risk.data_functions.rivers_damage import load_rivers_data
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile, shapefile_dir
from climate_risk.geo.crs import GEOGRAPHIC_CRS, to_km
from climate_risk.geo.distance import MIN_DISTANCE_METRES, get_distance_to
from climate_risk.geo.island_countries import ISLAND_COUNTRY_ISO3

_log = logging.getLogger(__name__)

SYNTHETIC_DATA_BASENAME = "synthetic_non_disasters.csv"

SAMPLING_STRATEGIES = ("region", "country")


def raw_points_path(cache_dir: Path) -> Path:
    return cache_dir / "disaster_locations_gpt_repaired_w_features.csv"


def features_points_path(cache_dir: Path) -> Path:
    return cache_dir / "disaster_locations_gpt_repaired_w_features.csv"


def read_cached_points(fpath: Path, index_col: int | None = None) -> pd.DataFrame:
    """Read a cached point CSV, normalising a `long` column to `lon`."""
    # Remove once no cache on disk spells it long.
    frame = pd.read_csv(fpath, index_col=index_col)

    return frame if "lon" in frame.columns else frame.rename(columns={"long": "lon"})


def load_data(fpath: Path) -> gpd.GeoDataFrame:
    data = read_cached_points(fpath)
    data["geometry"] = gpd.points_from_xy(data.lon, data.lat)
    data = gpd.GeoDataFrame(data, crs=GEOGRAPHIC_CRS)

    return data


def _load_disaster_point_data(cache_dir: Path):
    if features_points_path(cache_dir).exists():
        data = load_data(features_points_path(cache_dir))
    elif raw_points_path(cache_dir).exists():
        data = load_data(raw_points_path(cache_dir))
    else:
        raise ValueError("Go run the GPT notebook first!")

    return data


def load_disaster_point_data(cache_dir: Path):
    modified_data = False

    # Load Laos shapefile
    emdat = load_emdat_data(cache_dir)
    data = _load_disaster_point_data(cache_dir)

    data = (
        data.set_index(["emdat_index"])
        .join(emdat["df_raw_filtered_adj"])
        .reset_index(drop=False)
        .rename(columns={"index": "emdat_index"})
        .set_index(["emdat_index", "location_id"])
    )

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
        (
            data.drop(columns=[*emdat["df_raw_filtered_adj"].columns.tolist(), "geometry"]).to_csv(
                features_points_path(cache_dir)
            )
        )

    return data


def load_grid_point_data(
    cache_dir: Path,
    *,
    region="laos",
    grid_size=400,
    iso_list: list | None = None,
    force_reload: bool = False,
    file_reg_name: str | None = None,
    altered_shape_file=None,
    include_medium_rivers: bool = True,
):
    if region not in ["laos", "sea", "custom"]:
        raise ValueError(f"Unknown grid: {region}")

    if region == "custom" and iso_list is None:
        raise ValueError("Must provide an iso_list for custom region")

    if (region == "custom") and file_reg_name is None:
        raise ValueError("Please provide a file_reg_name for the custom region")

    if (region == "laos") or (region == "sea"):
        file_reg_name = region

    fname = f"{file_reg_name}_points_{grid_size}.shp"
    folder_path = shapefile_dir(cache_dir) / fname

    if not folder_path.exists():
        folder_path.mkdir(parents=True)

    fpath = folder_path / f"{fname}.shp"

    if fpath.exists() and not force_reload:
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

    elif not fpath.exists() or force_reload:
        _log.info("Loading shapefiles and rivers data")
        world = load_shapefile("world", cache_dir)

        if region == "sea":
            iso_list = [
                "MMR",  # Myanmar
                "THA",  # Thailand
                "LAO",  # Laos
                "KHM",  # Cambodia
                "VNM",  # Vietnam
                "IDN",  # Indonesia
                "MYS",  # Malaysia
                # "SGP",  # Singapore
                "PHL",  # Philippines
                # "BRN",  # Brunei
                "TLS",  # Timor-Leste
            ]
        elif region == "laos":
            iso_list = ["LAO"]

        if altered_shape_file is None:
            point_map = world.query("ISO_A3 in @iso_list")

        else:
            point_map = altered_shape_file

        rivers = load_rivers_data(cache_dir, include_medium=include_medium_rivers)
        coastline = load_shapefile("coastline", cache_dir)

        _log.info("Computing point grid and features")
        lon_min, lat_min, lon_max, lat_max = point_map.dissolve().bounds.values.ravel()
        lon_grid = np.linspace(lon_min, lon_max, grid_size)
        lat_grid = np.linspace(lat_min, lat_max, grid_size)

        grid = np.column_stack([x.ravel() for x in np.meshgrid(lon_grid, lat_grid)])
        grid = gpd.GeoSeries(gpd.points_from_xy(*grid.T), crs=GEOGRAPHIC_CRS)
        grid = gpd.GeoDataFrame({"geometry": grid})

        points = grid.overlay(point_map, how="intersection").geometry
        points = points.to_frame().assign(lon=lambda x: x.geometry.x, lat=lambda x: x.geometry.y)

        # Obtain distance with rivers
        distances_rivers = get_distance_to(
            rivers,
            points=points,
            return_columns=["ORD_FLOW", "HYRIV_ID"],
            name="rivers",
        ).rename(columns={"distance_to_closest": "distance_to_river"})

        points = pd.merge(points, distances_rivers, left_index=True, right_index=True, how="left")

        # Obtain sea distance with coastlines
        distances_coastlines = get_distance_to(
            coastline.boundary, points=points, return_columns=None, name="coastline"
        ).rename(columns={"distance_to_closest": "distance_to_coastline"})

        points = pd.merge(points, distances_coastlines, left_index=True, right_index=True, how="left")

        # Assign is_island column
        points["is_island"] = False

        # Create log of distances
        points = points.assign(
            log_distance_to_river=lambda x: np.log(x.distance_to_river.clip(lower=MIN_DISTANCE_METRES)),
            log_distance_to_coastline=lambda x: np.log(x.distance_to_coastline.clip(lower=MIN_DISTANCE_METRES)),
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
        gpd.sjoin(world, not_disasters, predicate="contains").sort_values(by="index_right").ISO_A3.values
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

    world_subset = world.query("ISO_A3 in @data.ISO.unique()").set_index("ISO_A3").sort_index()
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


def make_synthetic_data_fpath(cache_dir: Path, by: str, multipler: int, list_name: str) -> Path:
    basename = Path(SYNTHETIC_DATA_BASENAME)
    fname = f"{basename.stem}_{by}_times_{multipler}_{list_name}{basename.suffix}"

    return cache_dir / fname


def load_synthetic_non_disaster_points(
    cache_dir: Path,
    countries,
    list_name: str,
    *,
    rng=None,
    force_generate=False,
    by="region",
    multiplier=1,
):
    if by not in SAMPLING_STRATEGIES:
        raise ValueError(f"by should be one of {sorted(SAMPLING_STRATEGIES)}, got {by}")

    if rng is None:
        seed = sum(map(ord, "Laos GGGI Climate Adaptation"))
        rng = np.random.default_rng(seed)

    fpath = make_synthetic_data_fpath(cache_dir, by, multiplier, list_name)

    if not fpath.exists() or force_generate:
        world = load_shapefile("world", cache_dir)
        coastline = load_shapefile("coastline", cache_dir)
        rivers = load_rivers_data(cache_dir)

        data = load_disaster_point_data(cache_dir).dropna(subset="Region").query("ISO in @countries")

        if by == "region":
            _log.info("Sampling non-disasters by region")
            not_disasters = _sample_by_region(data, world, multiplier=multiplier, rng=rng)
        elif by == "country":
            _log.info("Sampling non-disasters by country")
            not_disasters = _sample_by_country(data, world, multiplier=multiplier, rng=rng)
        island_dict = data[["ISO", "is_island"]].drop_duplicates().set_index("ISO").to_dict()["is_island"]
        not_disasters["is_island"] = not_disasters["ISO"].map(island_dict.get)

        distances = get_distance_to(
            rivers,
            points=not_disasters,
            return_columns=["ORD_FLOW", "HYRIV_ID"],
            name="rivers",
        ).rename(columns={"distance_to_closest": "distance_to_river"})
        not_disasters = not_disasters.join(distances).assign(distance_to_river=lambda x: to_km(x.distance_to_river))

        distances = get_distance_to(
            coastline.boundary,
            points=not_disasters,
            return_columns=None,
            name="coastline",
        ).rename(columns={"distance_to_closest": "distance_to_coastline"})
        not_disasters = not_disasters.join(distances).assign(
            distance_to_coastline=lambda x: to_km(x.distance_to_coastline)
        )

        not_disasters["lon"] = not_disasters.geometry.apply(lambda x: x.x)
        not_disasters["lat"] = not_disasters.geometry.apply(lambda x: x.y)

        not_disasters.sort_values(by=["ISO"], inplace=True)
        not_disasters["Start_Year"] = np.random.choice(
            data.Start_Year.unique(), size=not_disasters.shape[0], replace=True
        )
        not_disasters.reset_index(inplace=True, drop=True)

        not_disasters.sort_index().drop(columns=["geometry"]).to_csv(fpath)

    else:
        _log.info(f"Loading data found at {fpath}")
        not_disasters = read_cached_points(fpath, index_col=0)
        not_disasters["geometry"] = gpd.points_from_xy(not_disasters.lon, not_disasters.lat)
        not_disasters["Start_Year"] = pd.to_datetime(not_disasters["Start_Year"])

        # The cache stores bare lat/lon columns, so the CRS is asserted rather than read back.
        not_disasters = gpd.GeoDataFrame(not_disasters, crs=GEOGRAPHIC_CRS)

    return not_disasters


def load_non_disaster_grid(
    cache_dir: Path,
    grid: gpd.GeoDataFrame | None,
    grid_name: str,
    *,
    force_generate: bool = False,
    three_dimensioal_grid: bool = False,
):
    fpath = cache_dir / grid_name

    if not fpath.exists() or force_generate:
        world = load_shapefile("world", cache_dir)

        # We merge the grid with the world shapefile to get the ISO
        not_disasters = gpd.sjoin(
            grid,
            world[["geometry", "ISO_A3"]],
            how="left",
        ).rename(columns={"ISO_A3": "ISO"})
        not_disasters["is_disaster"] = 0

        if three_dimensioal_grid:
            # Obtain years and ISOs
            years = load_disaster_point_data(cache_dir)["Start_Year"].unique()
            country_ISOs = not_disasters["ISO"].unique()

            # Create the Cartesian product of the two arrays
            combinations = list(itertools.product(years, country_ISOs))
            combinations_df = pd.DataFrame(combinations, columns=["Start_Date", "ISO"]).sort_values("ISO")

            # Merge files and create not_disasters_grid
            not_disasters = pd.merge(
                not_disasters,
                combinations_df,
                left_on="ISO",
                right_on="ISO",
                how="left",
            ).rename(columns={"Start_Date": "Start_Year"})

        else:
            not_disasters = not_disasters.rename(columns={"Start_Date": "Start_Year"})
            not_disasters["Start_Year"] = "1984-01-01"
            not_disasters["Start_Year"] = pd.to_datetime(not_disasters["Start_Year"])

        # Save file
        not_disasters.to_csv(fpath)

    if fpath.exists():
        not_disasters = read_cached_points(fpath, index_col=0)

    return not_disasters
