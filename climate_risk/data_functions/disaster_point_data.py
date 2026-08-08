import logging

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from climate_risk.config.registry import place_key, resolve_isos
from climate_risk.config.schema import Place
from climate_risk.data.cache import cached, geo_parquet
from climate_risk.data_functions.emdat_processing import load_emdat_data
from climate_risk.data_functions.rivers_damage import load_rivers_data
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile, shapefile_dir
from climate_risk.geo.crs import GEOGRAPHIC_CRS, to_km
from climate_risk.geo.distance import MIN_DISTANCE_METRES, get_distance_to
from climate_risk.geo.island_countries import ISLAND_COUNTRY_ISO3

_log = logging.getLogger(__name__)

# Every grid point is stamped with this year, so the non-disaster controls sit at one point in time.
CONTROL_YEAR = pd.Timestamp("1984-01-01")


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

    return load_data(path)


def load_disaster_point_data(cache_dir: Path):
    modified_data = False

    events = load_emdat_data(cache_dir)["df_raw_filtered_adj"].to_pandas().set_index("emdat_index")
    data = _load_disaster_point_data(cache_dir)

    data = (
        data.set_index(["emdat_index"])
        .join(events)
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
        (data.drop(columns=[*events.columns.tolist(), "geometry"]).to_csv(disaster_points_path(cache_dir)))

    return data


def load_grid_point_data(
    cache_dir: Path,
    place: Place,
    *,
    force_reload: bool = False,
    altered_shape_file: gpd.GeoDataFrame | None = None,
    include_medium_rivers: bool = True,
) -> gpd.GeoDataFrame:
    """
    Build the point grid covering a place, and cache it.

    Parameters
    ----------
    cache_dir : Path
        Directory the shapefile, river and grid caches live under.
    place : CountryConfig or RegionConfig
        The place to grid. Its ``geometry.grid_size`` sets the resolution, and the codes it resolves
        to select the geometry out of the world shapefile.
    force_reload : bool, optional
        Rebuild even when the cache is warm. Default False.
    altered_shape_file : GeoDataFrame, optional
        Geometry to grid instead of the place's own. Default None.
    include_medium_rivers : bool, optional
        Whether medium-flow rivers count towards the distance features. Default True.

    Returns
    -------
    GeoDataFrame
        One row per grid point falling on land, with distances to river and coastline.
    """
    grid_size = place.geometry.grid_size
    iso_codes = resolve_isos(place)

    def build() -> gpd.GeoDataFrame:
        _log.info("Loading shapefiles and rivers data")
        world = load_shapefile("world", cache_dir)

        if altered_shape_file is None:
            point_map = world[world["ISO_A3"].isin(iso_codes)]

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

        points["is_island"] = False

        # Kilometres, as every other frame carrying these column names reports them.
        points = points.assign(
            distance_to_river=lambda x: to_km(x.distance_to_river),
            distance_to_coastline=lambda x: to_km(x.distance_to_coastline),
        )

        floor = to_km(MIN_DISTANCE_METRES)
        points = points.assign(
            log_distance_to_river=lambda x: np.log(x.distance_to_river.clip(lower=floor)),
            log_distance_to_coastline=lambda x: np.log(x.distance_to_coastline.clip(lower=floor)),
        )

        return points

    return cached(
        shapefile_dir(cache_dir),
        "points",
        build,
        geo_parquet(),
        params={"region": place_key(place), "grid_size": grid_size},
        force=force_reload,
    )


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


# Sampling strategies, keyed by the name callers pass as `by`.
SAMPLERS = {"region": _sample_by_region, "country": _sample_by_country}
SAMPLING_STRATEGIES = tuple(SAMPLERS)


def load_synthetic_non_disaster_points(
    cache_dir: Path,
    place: Place,
    *,
    rng: np.random.Generator | None = None,
    force_generate: bool = False,
    by: str = "region",
    multiplier: int = 1,
) -> gpd.GeoDataFrame:
    """
    Sample non-disaster points to stand against the disasters a place recorded, and cache them.

    Parameters
    ----------
    cache_dir : Path
        Directory the shapefile, river and point caches live under.
    place : CountryConfig or RegionConfig
        The place to sample within. Its ``random_seed`` seeds the default generator.
    rng : numpy.random.Generator, optional
        Generator to draw with. Default None, meaning one seeded from the place.
    force_generate : bool, optional
        Resample even when the cache is warm. Default False.
    by : str, optional
        Sampling strategy, one of ``SAMPLING_STRATEGIES``. Default ``"region"``.
    multiplier : int, optional
        How many non-disasters to sample per recorded disaster. Default 1.

    Returns
    -------
    GeoDataFrame
        One row per sampled point, with distances to river and coastline and a drawn start year.
    """
    if by not in SAMPLING_STRATEGIES:
        raise ValueError(f"by should be one of {sorted(SAMPLING_STRATEGIES)}, got {by}")

    if rng is None:
        rng = np.random.default_rng(place.random_seed)

    countries = resolve_isos(place)

    def build() -> gpd.GeoDataFrame:
        world = load_shapefile("world", cache_dir)
        coastline = load_shapefile("coastline", cache_dir)
        rivers = load_rivers_data(cache_dir)

        data = load_disaster_point_data(cache_dir).dropna(subset="Region")
        data = data[data["ISO"].isin(countries)]

        _log.info(f"Sampling non-disasters by {by}")
        not_disasters = SAMPLERS[by](data, world, multiplier=multiplier, rng=rng)

        is_island_by_iso = data[["ISO", "is_island"]].drop_duplicates().set_index("ISO").to_dict()["is_island"]
        not_disasters["is_island"] = not_disasters["ISO"].map(is_island_by_iso.get)

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

        not_disasters = not_disasters.sort_values("ISO").reset_index(drop=True)
        not_disasters["Start_Year"] = rng.choice(data.Start_Year.unique(), size=not_disasters.shape[0], replace=True)

        return not_disasters

    return cached(
        cache_dir,
        "synthetic_non_disasters",
        build,
        geo_parquet(),
        params={"by": by, "times": multiplier, "list_name": place_key(place)},
        force=force_generate,
    )


def load_non_disaster_grid(
    cache_dir: Path,
    grid: gpd.GeoDataFrame | None,
    grid_name: str,
    *,
    force_generate: bool = False,
) -> gpd.GeoDataFrame:
    """
    Label a point grid with the country each point falls in, and cache it as non-disaster controls.

    Parameters
    ----------
    cache_dir : Path
        Directory the shapefile and grid caches live under.
    grid : GeoDataFrame, optional
        Points to label. Read only when the cache is cold, so a warm call may pass None.
    grid_name : str
        Name the result is cached under.
    force_generate : bool, optional
        Rebuild even when the cache is warm. Default False.

    Returns
    -------
    GeoDataFrame
        One row per point, with ``ISO``, ``is_disaster`` of zero, and ``Start_Year``.
    """

    def build() -> gpd.GeoDataFrame:
        world = load_shapefile("world", cache_dir)

        not_disasters = gpd.sjoin(grid, world[["geometry", "ISO_A3"]], how="left").rename(columns={"ISO_A3": "ISO"})
        not_disasters["is_disaster"] = 0
        not_disasters["Start_Year"] = CONTROL_YEAR

        return not_disasters

    return cached(
        cache_dir,
        "non_disaster_grid",
        build,
        geo_parquet(),
        params={"grid": grid_name},
        force=force_generate,
    )
