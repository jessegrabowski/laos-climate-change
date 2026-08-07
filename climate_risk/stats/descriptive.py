import pandas as pd


def descriptive_stats_function(df: pd.DataFrame, varlist: list[str]) -> pd.DataFrame:
    summary = df[varlist].describe()
    kurtosis = pd.Series({column: df[column].kurt() for column in varlist})
    skewness = pd.Series({column: df[column].skew() for column in varlist})

    return pd.concat(
        [
            summary,
            kurtosis.to_frame().rename(columns={0: "kurtosis"}).transpose(),
            skewness.to_frame().rename(columns={0: "skewness"}).transpose(),
        ]
    )
