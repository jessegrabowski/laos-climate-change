import numpy as np
import pandas as pd

# Lat/lon as the upstream shapefiles and gridded products supply it.
GEOGRAPHIC_CRS = "EPSG:4326"

# World Mercator. Distances measured in it come back in meters, which every caller assumes.
PROJECTED_CRS = "EPSG:3395"

METERS_PER_KM = 1000


def to_km[Distance: (float, np.ndarray, pd.Series)](meters: Distance) -> Distance:
    """
    Convert a distance measured in ``PROJECTED_CRS`` to kilometers.

    Parameters
    ----------
    meters : float, ndarray or Series
        Distance in meters.

    Returns
    -------
    distance : float, ndarray or Series
        The same distance in kilometers, matching the input type.
    """
    return meters / METERS_PER_KM
