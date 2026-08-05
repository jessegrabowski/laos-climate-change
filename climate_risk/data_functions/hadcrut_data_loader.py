import logging

from pathlib import Path
from urllib.request import urlretrieve

import geopandas as geo
import pandas as pd
import xarray as xr

from climate_risk.const_vars import HADCRUT_URL
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile

_log = logging.getLogger(__name__)


def load_hadcrut_data(cache_dir: Path, *, force_reload: bool = False, repair_ISO_codes: bool = True) -> pd.DataFrame:
    hadcrut_raw_path = cache_dir / "hadcrut_temperature_raw.nc"
    hadcrut_processed_path = cache_dir / "hadcrut_temperature_processed.csv"

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Verify if the hadcrut processed file exists
    if not hadcrut_processed_path.exists() or force_reload:
        # The raw archive is only needed to build the processed file.
        if not hadcrut_raw_path.exists():
            _log.info("Downloading HADCRUT data")
            urlretrieve(HADCRUT_URL, hadcrut_raw_path)

        _log.info("Loading  HADCRUT raw data")
        data = xr.open_dataset(hadcrut_raw_path)
        df = data["tas_mean"].to_dataframe().reset_index()

        # Import the world shapefile
        _log.info("Loading world shapefile as GeoDataFrame")
        world_shapefile = load_shapefile(
            "world", cache_dir, force_reload=force_reload, repair_ISO_codes=repair_ISO_codes
        ).rename(
            columns={
                "ISO_A3": "country_code",
                "FORMAL_EN": "country",
                "CONTINENT": "continent",
                "REGION_UN": "region",
            }
        )
        _log.info("Merging HADCRUT data with world shapefile using Lat/Lon (EPSG:4326 coordinates)")

        df_geo = geo.GeoDataFrame(
            df,
            geometry=geo.points_from_xy(df["longitude"], df["latitude"]),
            crs="EPSG:4326",
        )

        cols_to_use = [
            "time",
            "latitude",
            "longitude",
            "realization",
            "tas_mean",
            "country_code",
            "geometry",
            "country",
            "continent",
            "region",
        ]

        result_df = df_geo.sjoin(world_shapefile, how="inner", predicate="intersects")[cols_to_use].rename(
            columns={"tas_mean": "surface_temperature_dev"}
        )

        result_df["year"] = pd.to_datetime(result_df["time"].dt.year, format="%Y")

        result_df = (
            result_df.pivot_table(
                values="surface_temperature_dev",
                index=["country_code", "year"],
                aggfunc="mean",
            )
            .reset_index()
            .rename(columns={"country_code": "ISO"})
            .query("year >1959")
            .set_index(["ISO", "year"])
        )

        _log.info(f"Saving processed GPCC data to {hadcrut_processed_path}")
        result_df.to_csv(hadcrut_processed_path)
    else:
        # Caches exist with the year written both bare and as an ISO date, so no format is given.
        result_df = (
            pd.read_csv(hadcrut_processed_path)
            .assign(year=lambda x: pd.to_datetime(x["year"]))
            .set_index(["ISO", "year"])
        )

    return result_df
