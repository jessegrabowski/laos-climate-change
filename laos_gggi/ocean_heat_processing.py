import pandas as pd
import os

def process_ocean_heat():
    
    if not os.path.isfile("../data/ncei_global_ocean_heat.csv"):
        url = "https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/DATA/basin/onemonth/ohc_levitus_climdash_monthly.csv"
        #https://www.ncei.noaa.gov/access/global-ocean-heat-content/basin_heat_data_monthly.html
        df = pd.read_csv(url, header=None)
        df.rename(columns={0:"Date",1:"Temp"}, inplace=True)
        df.Date = pd.to_datetime(df.Date)
        df = df.set_index("Date")
        df.to_csv("../data/ncei_global_ocean_heat.csv")
        df_ocean = df
        
    else:
        df_ocean = pd.read_csv("../data/ncei_global_ocean_heat.csv", index_col=["Date"], parse_dates=True)

    return df_ocean
