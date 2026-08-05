import gzip
import logging
import shutil

from pathlib import Path
from urllib.request import urlretrieve

import geopandas as geo
import pandas as pd
import xarray as xr

from climate_risk.const_vars import GPCC_YEARS, MAKE_GPCC_URL
from climate_risk.data_functions.shapefiles_data_loader import load_shapefile

_log = logging.getLogger(__name__)


def load_gpcc_data(cache_dir: Path, *, force_reload: bool = False, repair_ISO_codes: bool = True) -> pd.DataFrame:
    gpcc_path = cache_dir / "gpcc"

    def path_to_GPCC(years: str, extracted: bool = False) -> Path:
        fname = f"gpcc_raw_{years}.nc"
        fname += ".gz" if not extracted else ""
        return gpcc_path / fname

    gpcc_processed_path = gpcc_path / "gpcc_precipitations.csv"

    gpcc_path.mkdir(parents=True, exist_ok=True)

    if not gpcc_processed_path.exists() or force_reload:
        # The raw archives are only needed to build the processed file.
        for year_range in GPCC_YEARS:
            if not path_to_GPCC(year_range).exists():
                _log.info(f"Downloading GPCC data for {' - '.join(year_range.split('_'))}")
                urlretrieve(MAKE_GPCC_URL(year_range), path_to_GPCC(year_range, extracted=False))

        for year_range in GPCC_YEARS:
            if path_to_GPCC(year_range, extracted=True).exists():
                continue
            with (
                gzip.open(path_to_GPCC(year_range, extracted=False), "rb") as f_in,
                open(path_to_GPCC(year_range, extracted=True), "wb") as f_out,
            ):
                _log.info(f"Extracting GPCC data for {' - '.join(year_range.split('_'))}")
                shutil.copyfileobj(f_in, f_out)

        # Import the world shapefile
        _log.info("Loading world shapefile as GeoDataFrame")
        world_shapefile = load_shapefile(
            "world", cache_dir, force_reload=False, repair_ISO_codes=repair_ISO_codes
        ).rename(
            columns={
                "ISO_A3": "country_code",
                "FORMAL_EN": "country",
                "CONTINENT": "continent",
                "REGION_UN": "region",
            }
        )

        # Open gpcc files, transform them to geopandas shapefile geometry and merge them with the world shapefiles
        result_df = pd.DataFrame()
        for year_range in list(GPCC_YEARS):
            str_range = " - ".join(year_range.split("_"))

            data = xr.open_dataset(path_to_GPCC(year_range, extracted=True))
            df = data["precip"].to_dataframe().reset_index()
            _log.info(f"Merging {str_range} GPCC data with world shapefile using Lat/Lon (EPSG:4326 coordinates)")
            df_geo = geo.GeoDataFrame(df, geometry=geo.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
            df_geo_wshape = df_geo.sjoin(world_shapefile, how="inner", predicate="intersects")[
                [
                    "time",
                    "lat",
                    "lon",
                    "precip",
                    "country_code",
                    "geometry",
                    "country",
                    "continent",
                    "region",
                ]
            ]
            result_df = pd.concat([result_df, df_geo_wshape], axis=0)

        result_df = result_df.pivot_table(values="precip", index=["country_code", "time"], aggfunc="mean")
        _log.info(f"Saving processed GPCC data to {gpcc_processed_path}")
        result_df.to_csv(gpcc_processed_path)
    else:
        result_df = pd.read_csv(gpcc_processed_path).set_index(["country_code", "time"])

    return result_df
