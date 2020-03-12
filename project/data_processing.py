import grid
import globs
import pandas as pd
import pickle
from os.path import exists
from os import remove
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
        last = chunk['Latitude'].iloc[-1]
        # latitude_mask = False if chunk['Latitude'].isna() else lat2 <= chunk['Latitude'] <= lat1
        # latitude_mask = ('Latitude'].isna()) & (chunk['Latitude'].between(lat2,lat1))
        latitude_mask = (~chunk['Latitude'].isna()) & (chunk['Latitude'].between(lat2, lat1))
        latitude_filtered_data = chunk[latitude_mask]
        # Check longitude
        if f_cross_180_longitude:
            longitude_mask = (~latitude_filtered_data['Longitude'].isna()) & \
                             ((latitude_filtered_data['Longitude'].between(lon1, 180)) |
                              (latitude_filtered_data['Longitude'].between(0, lon2)))
        else:
            longitude_mask = (~latitude_filtered_data['Longitude'].isna()) & \
                             (latitude_filtered_data['Longitude'].between(lon1, lon2))

        filtered_data_chunk = latitude_filtered_data[longitude_mask]
        # add to return data
        list_of_chunks.append(filtered_data_chunk)

        if last > lat1:
            break
    # squash all DF's to one DF
    return pd.concat(list_of_chunks)


# It returns [ (s1,[d1,d2,d3,d4,...]) , .... ]
def assign_data_to_square(squares, data):
    to_ret = []
    for s in squares:
        lat1 = s[0][0]
        lat2 = s[3][0]
        lon1 = s[0][1]
        lon2 = s[3][1]
        square_mask = (data['Latitude'].between(lat1,lat2)) & (data['Longitude'].between(lon1,lon2))
        to_ret.append((s, data[square_mask]))
    return to_ret


def calculate_crucial_data(square_with_data):
    to_ret = []
    for s, d in square_with_data:
        mean = d['Value'].mean()
        std = d['Value'].std()
        min = d['Value'].min()
        max = d['Value'].max()

        to_ret.append((s, mean, std, min, max))
    return to_ret


def proceed_region(city_points, resolution=5000, file_to_save=False):
    # TODO: Create grid for region
    region_grid = grid.create_grid_for_surface_from_points(city_points[0], city_points[1], resolution=resolution)
    # TODO: Load whole data for this region
    data_region = get_data_region(city_points)
    # TODO: Assign data to appropriate square
    squares_with_data = assign_data_to_square(region_grid, data_region)
    # TODO: Calculate mean, standard deviation, mean, min, max
    squares_basic_data = calculate_crucial_data(squares_with_data)
    # TODO: Save data collected
    if file_to_save:
        if exists(file_to_save):
            remove(file_to_save)
        with open(file_to_save, "w+b") as fp:
            pickle.dump([squares_basic_data, squares_with_data], fp)
    # TODO: Create/Save heat map for this region
    # TODO: Maybe some prediction based on the height in this model or some future years?


if __name__ == "__main__":
    proceed_region(globs.cities.ROME, file_to_save=globs.cities.ROME_FILE)
    proceed_region(globs.cities.TOKYO, file_to_save=globs.cities.TOKYO_FILE)
    proceed_region(globs.cities.KRAKOW, file_to_save=globs.cities.KRAKOW_FILE)
    proceed_region(globs.cities.CZARNOBYL, file_to_save=globs.cities.CZARNOBYL_FILE)
