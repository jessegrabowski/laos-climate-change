import os
from os.path import exists
from urllib.request import urlretrieve
from const_vars import GPCC_URL
import xarray as xr
import geopandas as geo
import pandas as pd
import numpy as np
from zipfile import ZipFile 
import gzip
import shutil


def download_gpcc_data(output_path="../data"):
    path_to_GPCC_raw = { '1981_1990' : output_path + "/gpcc/gpcc_raw_1981_1990.nc.gz",
                       '1991_2000' : output_path + "/gpcc/gpcc_raw_1991_2000.nc.gz",
                       '2001_2010':output_path + "/gpcc/gpcc_raw_2001_2010.nc.gz" ,
                       '2011_2020':output_path + "/gpcc/gpcc_raw_2011_2020.nc.gz"}
    path_to_GPCC_unzipped = output_path + "/gpcc/gpcc_raw_1981_1990.nc"
    shapefile_unzipped_folder_world = output_path + "/shapefiles/wb_countries_admin0_10m"
    shapefile_unzipped_folder_laos = output_path + "lao_adm_ngd_20191112_shp"
    world_shapefile_path = output_path + "/shapefiles/wb_countries_admin0_10m"
    gpcc_processed_path = output_path + "/gpcc/gpcc_precipitations.csv"
    
    #Check if "data" folder exists
    if not exists(output_path):
        os.makedirs(output_path)
        
    #Check if gpcc folder exists
    if not exists(output_path + "/gpcc"):
        os.makedirs(output_path + "/gpcc")
    
    #Check if the GPCC raw data exists
    if not exists(path_to_GPCC_raw['1981_1990']):
        for x in GPCC_URL: 
            urlretrieve(GPCC_URL[x], path_to_GPCC_raw[x])
        
    #Verify if shapefiles are unzipped                
    if not exists(shapefile_unzipped_folder_world):
        with ZipFile(output_path +  "/shapefiles/wb_countries_admin0_10m.zip", 'r') as zObject:  
            zObject.extractall( path= output_path +  "/shapefiles") 
    if not exists(shapefile_unzipped_folder_laos):       
        with ZipFile(output_path +  "/shapefiles/lao_adm_ngd_20191112_shp.zip", 'r') as zObject:  
            zObject.extractall(path= output_path +  "/shapefiles") 
            
    #Verify if the gpcc files are extracted (Note:gzip.open does not support loops)
    if not exists(path_to_GPCC_unzipped):
        with gzip.open(output_path + "/gpcc/gpcc_raw_1981_1990.nc.gz", 'rb') as f_in:
            with open(output_path + "/gpcc/gpcc_raw_1981_1990.nc", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        with gzip.open(output_path + "/gpcc/gpcc_raw_1991_2000.nc.gz", 'rb') as f_in:
            with open(output_path + "/gpcc/gpcc_raw_1991_2000.nc", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        with gzip.open(output_path + "/gpcc/gpcc_raw_2001_2010.nc.gz", 'rb') as f_in:
            with open(output_path + "/gpcc/gpcc_raw_2001_2010.nc", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        with gzip.open(output_path + "/gpcc/gpcc_raw_2011_2020.nc.gz", 'rb') as f_in:
            with open(output_path + "/gpcc/gpcc_raw_2011_2020.nc", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    if not exists(gpcc_processed_path):
        # Import the world shapefile 
        world_shapefile = geo.read_file(world_shapefile_path).rename(columns = {"ISO_A3": "country_code","FORMAL_EN":"country",
                                                                                'CONTINENT': "continent", 'REGION_UN': "region" })
        #Open gpcc files, transform them to geopandas shapefile geometry and merge them with the world shapefiles
        for x in list(path_to_GPCC_raw.keys()):
            exec(f'data_{x} = xr.open_dataset(output_path + "/gpcc/gpcc_raw_" + x + ".nc")')
            exec(f'df_{x} = data_{x}["precip"].to_dataframe().reset_index()')
            exec(f'df_geo_{x} = geo.GeoDataFrame(df_{x}, geometry=geo.points_from_xy(df_{x}["lat"], df_{x}["lon"]), crs="EPSG:4326")')
            exec(f'df_geo_wshape_{x} = df_geo_{x}.sjoin(world_shapefile, how="inner", predicate="intersects")[["time", "lat", "lon", "precip","country_code", "geometry", "country", "continent", "region"]]')
            exec(f'df_geo_wshape_{x} = df_geo_wshape_{x}.set_index(["country_code", "time"])')
            
        df = pd.concat([df_geo_wshape_2011_2020, df_geo_wshape_2001_2010, df_geo_wshape_1991_2000, df_geo_wshape_1981_1990], axis=0).sort_index()
        df = df.reset_index()
        df = df.pivot_table(values= "precip", index = ["country_code", "time"], aggfunc="mean")
        df.to_csv(gpcc_processed_path)
    else:
        df = pd.read_csv(gpcc_processed_path)
    return df