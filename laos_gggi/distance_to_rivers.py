import pandas as pd
from tqdm.notebook import tqdm
import numpy as np


def get_distance_to_rivers(rivers, points):
    ret = pd.Series(np.nan, index=points.index, name="closest_river")
    rivers_km = rivers.copy().to_crs("EPSG:3395")
    points_km = points.copy().to_crs("EPSG:3395")
    for idx, row in tqdm(points_km.iterrows(), total=points.shape[0]):
        ret.loc[idx] = rivers_km.distance(row.geometry).min()
    return ret
