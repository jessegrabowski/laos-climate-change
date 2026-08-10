import pandas as pd

from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller


def stl_deviation(series: pd.Series, period: int = 3) -> pd.Series:
    """
    Return what is left of a series once its STL trend is removed.

    Parameters
    ----------
    series : Series
        The series to detrend, indexed by time.
    period : int, optional
        Periodicity of the seasonal component, in observations. Default 3.

    Returns
    -------
    Series
        The series minus its trend, on the same index.
    """
    trend = pd.Series(STL(series, period=period).fit().trend, index=series.index)

    return series - trend


def make_var_names(var: str, n_lags: int, reg: str) -> list[str]:
    names = [f"L1.{var}"]
    for lag in range(1, n_lags + 1):
        names.append(f"D{lag}L1.{var}")
    if reg != "n":
        names.append("Constant")
    if "t" in reg:
        names.append("Trend")

    return names


def adf_test_summary(
    df: pd.DataFrame | pd.Series,
    maxlag: int | None = None,
    autolag: str = "BIC",
    missing: str = "error",
) -> None:
    if missing == "error":
        if df.isna().any().any():
            raise ValueError("df has missing data; handle it or pass missing='drop' to automatically drop it.")

    if isinstance(df, pd.Series):
        df = df.to_frame()

    for series in df.columns:
        data = df[series].copy()
        if missing == "drop":
            data.dropna(inplace=True)

        print(series.center(110))
        print("=" * 110)
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
        print("-" * 110)
        for _i, (name, reg) in enumerate(
            zip(["Constant and Trend", "Constant Only", "No Constant"], ["ct", "c", "n"], strict=False)
        ):
            stat, p, crit, regresult = adfuller(data, regression=reg, regresults=True, maxlag=maxlag, autolag=autolag)
            n_lag = regresult.usedlag
            gamma = regresult.resols.params[0]
            names = make_var_names(series, n_lag, reg)
            reg_coefs = pd.Series(regresult.resols.params, index=names)
            reg_tstat = pd.Series(regresult.resols.tvalues, index=names)
            reg_pvals = pd.Series(regresult.resols.pvalues, index=names)

            line = f"{name:<21}{gamma:13.3f}{stat:15.3f}{p:13.3f}{n_lag:11}{crit['1%']:10.3f}{crit['5%']:12.3f}{crit['10%']:11.3f}"
            print(line)

            for coef in reg_coefs.index:
                if coef in name:
                    line = f"\t{coef:<13}{reg_coefs[coef]:13.3f}{reg_tstat[coef]:15.3f}{reg_pvals[coef]:13.3f}"
                    print(line)
