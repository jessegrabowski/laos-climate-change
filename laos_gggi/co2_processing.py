import pandas as pd
import os

def process_co2():
    
    if not os.path.isfile("../data/co2.csv"):
        url = "https://gml.noaa.gov/aftp/products/trends/co2/co2_mm_gl.csv"
        df = pd.read_csv(url, skiprows=38)
        df["day"] = 1
        df["Date"] = pd.to_datetime(dict(year=df.year, month=df.month, day=df.day))
        df = df.set_index("Date")
        df.rename(columns={"average":"co2"}, inplace=True)
        df = df[["co2"]]
        df.to_csv("../data/co2.csv")
        df_co2 = df
    
    else:
        df_co2 = pd.read_csv("../data/co2.csv", index_col=["Date"], parse_dates=True)

    return df_co2
    