import geopandas as gpd
import pandas as pd
import xarray as xr

from climate_risk.geo.crs import GEOGRAPHIC_CRS


def prediction_to_gpd_df(
    prediction_idata: xr.DataTree, variables: list[str], points: pd.DataFrame
) -> dict[str, gpd.GeoDataFrame]:
    predictions_dict = {}
    predictions_dict_geo = {}

    for variable in variables:
        # Tranform predictions to DF
        predictions_dict[variable] = (
            prediction_idata.posterior_predictive.mean(dim=("chain", "draw"))[variable].to_dataframe().reset_index()
        )
        # Merge predictions with Laos points
        predictions_dict[variable] = pd.merge(
            predictions_dict[variable],
            points,
            left_index=True,
            right_index=True,
            how="left",
        )

        # Transform into geo Data Frame
        predictions_dict_geo[variable] = gpd.GeoDataFrame(
            predictions_dict[variable],
            geometry=gpd.points_from_xy(predictions_dict[variable]["lon"], predictions_dict[variable]["lat"]),
            crs=GEOGRAPHIC_CRS,
        )

    return predictions_dict_geo
