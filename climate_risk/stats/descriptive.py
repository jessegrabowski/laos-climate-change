import numpy as np
import pandas as pd


def nan_or_sum(x):
    if np.isnan(x).all():
        return np.nan
    return np.nansum(x)


# Descriptive stats function
def descriptive_stats_function(df, varlist):
    # Sum stats
    sum_stats = df[varlist].describe()
    # Kurtosis
    kurtosis = pd.Series()
    for x in varlist:
        kurtosis[str(x)] = df[str(x)].kurt()
    kurtosis = kurtosis.to_frame().rename(columns={0: "kurtosis"}).transpose()

    # Skewness
    skewness = pd.Series()
    for x in varlist:
        skewness[str(x)] = df[str(x)].skew()
    skewness = skewness.to_frame().rename(columns={0: "skewness"}).transpose()
    # Concat
    sum_stats = pd.concat([sum_stats, kurtosis, skewness])

    return sum_stats


# Augmented Dickey Fuller function

# First define make_var_names function to obtain the complete results of the ADF test
