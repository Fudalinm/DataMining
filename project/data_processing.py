import grid
import globs
import pandas as pd
import numpy as np


def get_data_region(city_points):
    lat1 = city_points[0][0]
    lat2 = city_points[1][0]
    lon1 = city_points[0][1]
    lon2 = city_points[1][1]
    f_cross_180_longitude = False
    if lon2 < lon1:
        f_cross_180_longitude = True

    list_of_chunks = []

    chunksize = 10 ** 6
    for chunk in pd.read_csv(globs.globals.DATA_BASE_FILTER_PATH_SORTED, chunksize=chunksize):
        last = chunk[-1]
        latitude_mask = False if chunk['Latitude'].isna() else lat2 < chunk['Latitude'] < lat1
        latitude_filtered_data = chunk[latitude_mask]
        # Check longitude
        if f_cross_180_longitude:
            longitude_mask = False if latitude_filtered_data['Longitude'].isna() else (lon1 < latitude_filtered_data['Longitude'] < 180 or 0 < latitude_filtered_data['Longitude'] < lon2)
        else:
            longitude_mask = False if latitude_filtered_data['Longitude'].isna() else lon1 < latitude_filtered_data['Longitude'] < lon2
        filtered_data_chunk = latitude_filtered_data[longitude_mask]
        # add to return data
        list_of_chunks.append(filtered_data_chunk)

        if last['Latitude'] < lat2:
            break
    # squash all DF's to one DF
    return pd.concat(list_of_chunks)


# It returns [ (s1,[d1,d2,d3,d4,...]) , .... ]
def assign_data_to_square(squares,data):
    to_ret = []
    for s in squares:
        lat1 = s[0][0]
        lat2 = s[3][0]
        lon1 = s[0][1]
        lon2 = s[3][1]
        square_mask = ( lat1 < data['Latitude'] < lat2 ) and ( lon1 < data['Longitude'] < lon2)
        to_ret.append((s,data[square_mask]))
    return to_ret

def calculate_crucial_data(square_with_data):
    to_ret = []
    for s,d in square_with_data:
        mean = d['Value'].mean()
        std = d['Value'].std()
        min = d['Value'].min()
        max = d['Value'].max()

        to_ret.append((s,mean,std,min,max))
    return to_ret

def proceed_region(city_points, resolution=5000):
    # TODO: Create grid for region
    region_grid = grid.create_grid_for_surface_from_points(city_points[0], city_points[1], resolution=resolution)
    # TODO: Load whole data for this region
    data_region = get_data_region(city_points)
    # TODO: Assign data to appropriate square
    squares_with_data = assign_data_to_square(region_grid,data_region)
    # TODO: Calculate mean, standard deviation, mean, min, max
    squares_basic_data = calculate_crucial_data(squares_with_data)
    # TODO: Create/Save heat map for this region

    # TODO: Maybe some prediction based on the height in this model or some future years?


if __name__ == "__main__":
