import pandas as pd

from sklearn.preprocessing import StandardScaler as Standardize


def standardize(df: pd.DataFrame, columns: list[str], transformer_fitted=None):
    if transformer_fitted is None:
        transformer_fitted = Standardize().fit(df[columns])

    columns_stand = [x + "__standardized" for x in columns]
    df_stand = pd.DataFrame(transformer_fitted.transform(df[columns]), columns=columns_stand, index=df.index)
    df_stand = pd.concat([df, df_stand], axis=1)

    return transformer_fitted, df_stand
