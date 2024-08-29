import pandas as pd
from statsmodels.tsa.stattools import adfuller
from tqdm.notebook import tqdm


# Descriptive stats function
def descriptive_stats_function(df, varlist):
    # Sum stats
    sum_stats = df.describe()
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


def make_var_names(var, n_lags, reg):
    names = [f"L1.{var}"]
    for lag in range(1, n_lags + 1):
        names.append(f"D{lag}L1.{var}")
    if reg != "n":
        names.append("Constant")
    if "t" in reg:
        names.append("Trend")

    return names


def ADF_test_summary(df, maxlag=None, autolag="BIC", missing="error"):
    if missing == "error":
        if df.isna().any().any():
            raise ValueError(
                "df has missing data; handle it or pass missing='drop' to automatically drop it."
            )

    if isinstance(df, pd.Series):
        df = df.to_frame()

    for series in df.columns:
        data = df[series].copy()
        if missing == "drop":
            data.dropna(inplace=True)

        print(series.center(110))
        print(("=" * 110))
        line = (
            "Specification"
            + " " * 15
            + "Coeff"
            + " " * 10
            + "Statistic"
            + " " * 5
            + "P-value"
            + " " * 6
            + "Lags"
            + " " * 6
            + "1%"
        )
        line += " " * 10 + "5%" + " " * 8 + "10%"
        print(line)
        print(("-" * 110))
        for i, (name, reg) in enumerate(
            zip(
                ["Constant and Trend", "Constant Only", "No Constant"], ["ct", "c", "n"]
            )
        ):
            stat, p, crit, regresult = adfuller(
                data, regression=reg, regresults=True, maxlag=maxlag, autolag=autolag
            )
            n_lag = regresult.usedlag
            gamma = regresult.resols.params[0]
            names = make_var_names(series, n_lag, reg)
            reg_coefs = pd.Series(regresult.resols.params, index=names)
            reg_tstat = pd.Series(regresult.resols.tvalues, index=names)
            reg_pvals = pd.Series(regresult.resols.pvalues, index=names)

            line = f'{name:<21}{gamma:13.3f}{stat:15.3f}{p:13.3f}{n_lag:11}{crit["1%"]:10.3f}{crit["5%"]:12.3f}{crit["10%"]:11.3f}'
            print(line)

            for coef in reg_coefs.index:
                if coef in name:
                    line = f"\t{coef:<13}{reg_coefs[coef]:13.3f}{reg_tstat[coef]:15.3f}{reg_pvals[coef]:13.3f}"
                    print(line)


def get_distance_to_rivers(rivers, points, crs="EPSG:3395"):
    ret = pd.DataFrame(
        index=points.index, columns=["closest_river", "ORD_FLOW", "HYRIV_ID"]
    )
    rivers_km = rivers.copy().to_crs(crs)
    points_km = points.copy().to_crs(crs)
    for idx, row in tqdm(points_km.iterrows(), total=points.shape[0]):
        series = rivers_km.distance(row.geometry)
        ret.loc[idx, "closest_river"] = series.min()

        index = series[series == series.min()].index[0]
        ret.loc[idx, "ORD_FLOW"] = rivers_km.loc[index]["ORD_FLOW"]
        ret.loc[idx, "HYRIV_ID"] = rivers_km.loc[index]["HYRIV_ID"]

    ret["ORD_FLOW"] = ret["ORD_FLOW"].astype("int")
    ret["closest_river"] = ret["closest_river"].astype("float")
    return ret
