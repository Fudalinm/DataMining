import grid
import globs
import pandas as pd
import pickle
from os.path import exists
from math import isnan
from os import remove
import matplotlib
import numpy as np
import os
import matplotlib.pyplot as plt
from numpy import arange


def get_data_region(city_points):
    lat1 = city_points[0][0]
    lat2 = city_points[1][0]
    lon1 = city_points[0][1]
    lon2 = city_points[1][1]
    print(
        "Loading csv file for lat: ({}) - ({}) lon: ({}) - ({}) ".format(city_points[0][0], city_points[1][0],
                                                                         city_points[0][1],
                                                                         city_points[1][1]))
    f_cross_180_longitude = False
    if lon2 < lon1:
        f_cross_180_longitude = True

    list_of_chunks = []

    chunksize = 3 * 10 ** 6
    for chunk in pd.read_csv(globs.general.DATA_BASE_FILTER_PATH_SORTED, chunksize=chunksize):
        last = chunk['Latitude'].iloc[-1]
        # first = chunk['Latitude'].iloc[1]
        if last < lat1:
            continue
        latitude_mask = (~chunk['Latitude'].isna()) & (chunk['Latitude'].between(lat1, lat2))
        latitude_filtered_data = chunk[latitude_mask]
        # Check longitude
        if f_cross_180_longitude:
            longitude_mask = (~latitude_filtered_data['Longitude'].isna()) & \
                             ((latitude_filtered_data['Longitude'].between(lon1, 180)) |
                              (latitude_filtered_data['Longitude'].between(0, lon2)))
        else:
            longitude_mask = (~latitude_filtered_data['Longitude'].isna()) & \
                             (latitude_filtered_data['Longitude'].between(lon1, lon2))

        filtered_lon_data_chunk = latitude_filtered_data[longitude_mask]

        filtered_lon_data_chunk['Captured Time'] = pd.to_datetime(filtered_lon_data_chunk['Captured Time'])
        date_mask = filtered_lon_data_chunk['Captured Time'].dt.year <= 2020
        radiation_mask = filtered_lon_data_chunk['Value'].between(0, 100000)

        # add to return data
        list_of_chunks.append(filtered_lon_data_chunk[date_mask & radiation_mask])

        if last > lat2:
            break
    # squash all DF's to one DF
    return pd.concat(list_of_chunks)


# It returns [ (s1,[d1,d2,d3,d4,...]) , .... ]
def assign_data_to_square(squares, data):
    to_ret = []
    for i in range(len(squares)):
        if i >= len(squares):
            break
        s = squares[i]
        lat1, lat2 = min(s)[0], max(s)[0]
        lon1, lon2 = min(s)[1], max(s)[1]

        curr_lat_data = data[data['Latitude'].between(lat1, lat2)]

        tmp_squares = []

        for j in range(len(squares)):
            if j >= len(squares):
                break
            s2 = squares[j]
            if lat1 == min(s2)[0] and lat2 == max(s2)[0]:
                tmp_squares.append(s2)
                squares.pop(j)

        for j in range(len(tmp_squares)):
            curr_square = tmp_squares[j]
            lon1, lon2 = min(curr_square)[1], max(curr_square)[1]
            to_ret.append((curr_square, curr_lat_data[curr_lat_data['Longitude'].between(lon1, lon2)]))

        if lat1 > lat2 or lon1 > lon2:
            print("Something is wrong in assign to square")
            print(s)
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


def proceed_region(city_points, resolution=5000, file_to_save=None, verbose=False, f_log=False):
    if verbose:
        print("Data grid creation")
    region_grid = grid.create_grid_for_surface_from_points(city_points[0], city_points[1], resolution=resolution)
    if verbose:
        print(region_grid)
        print("Data for region")
    data_region = get_data_region(city_points)
    if verbose:
        print(data_region)
        print("Assigning data for squares")
    squares_with_data = assign_data_to_square(region_grid, data_region)
    if verbose:
        print(squares_with_data)
        print("Calculating basic info")
    squares_basic_data = calculate_crucial_data(squares_with_data)
    if verbose:
        print(squares_basic_data)
        print("Approximating squares without any data")
    squares_basic_approximated = approximate_square_without_data(squares_basic_data, f_log)
    if verbose:
        print(squares_basic_approximated)
        print("Saving")

    if file_to_save is not None:
        if exists(file_to_save):
            remove(file_to_save)
        with open(file_to_save, "w+b") as fp:
            pickle.dump([squares_basic_approximated, squares_with_data], fp)


def approximate_square_without_data(square_basic_data, f_log=False):
    # data = [(s, mean, std, min, max) ,....]
    # TODO: add real approximation of squares without any data
    errors = 0
    without_data = 0
    with_data = 0
    total = len(square_basic_data)

    for s, mean, std, min, max in square_basic_data:
        if isnan(mean) or isnan(std) or isnan(min) or isnan(max):
            without_data += 1
        elif mean < 0 or std < 0 or min < 0 or max < 0:
            errors += 1
        else:
            with_data += 1
    print("Analyzing data: total_squares: {} without_data: {}, with_data: {}, errors: {}".format(total, without_data,
                                                                                                 with_data, errors))
    # THIS IS FOR REMOVING SQUARES WITHOUT DATA, REMOVE WHEN THEY WILL BE INTERPOLATED
    square_basic_data = list(filter(lambda x: not isnan(x[1]), square_basic_data))

    def simple_map(square_with_data):
        s, mean, std, min, max = square_with_data
        mean2 = 0 if isnan(mean) or mean < 0 else mean
        std2 = 0 if isnan(std) or std < 0 else std
        min2 = 0 if isnan(min) or min < 0 else min
        max2 = 0 if isnan(max) or max < 0 else max
        return s, mean2, std2, min2, max2

    square_basic_data = list(map(simple_map, square_basic_data))

    # TODO: consider using log2 on data
    # just unncoment this fragment if you want to use it :)
    if f_log:
        def log2_map(square_with_data):
            s, mean, std, min, max = square_with_data
            from math import log2
            return s, log2(mean + 1), log2(std + 1), log2(min + 1), log2(max + 1)

        square_basic_data = list(map(log2_map, square_basic_data))

    return square_basic_data


def calculate_correlation_sea_level_radiation(location=None, verbose=False):
    # location[(DOWN_LAT, LEFT_LON), (UP_LAT, RIGHT_LON)]
    if verbose:
        if location == None:
            print("Loading csv file for earth")
        else:
            print(
                "Loading csv file for lat: ({}) - ({}) lon: ({}) - ({}) ".format(location[0][0], location[1][0],
                                                                                 location[0][1],
                                                                                 location[1][1]))

    df = pd.read_csv(globs.general.DATA_FILTER_HEIGHT_PATH_SORTED, usecols=globs.general.ELEMENTS_TO_SAVE_CSV)

    if location != None:
        lat1 = location[0][0]
        lat2 = location[1][0]
        lon1 = location[0][1]
        lon2 = location[1][1]
        latitude_mask = (~df['Latitude'].isna()) & (df['Latitude'].between(lat1, lat2))
        df = df[latitude_mask]

        if lon2 < lon1:
            # long_cross
            longitude_mask = (~df['Longitude'].isna()) & \
                             ((df['Longitude'].between(lon1, 180)) |
                              (df['Longitude'].between(0, lon2)))
        else:
            longitude_mask = (~df['Longitude'].isna()) & \
                             (df['Longitude'].between(lon1, lon2))

        df = df[longitude_mask]

    # pearson correlation check only LINEAR correlation
    if verbose:
        print("DF loaded")
        print(df)
        print("Calculating Pearson Correlation")
    pearson_corr = df.corr(method='pearson')
    if verbose:
        print("Pearson Correlation")
        print(pearson_corr)
        print("Calculating spearman correlation")
    # rang Spearmana correlation shows also non_linear_correlation
    spearman_corr = df.corr(method='spearman')
    if verbose:
        print("Spearman Correlation ")
        print(spearman_corr)
    return pearson_corr, spearman_corr


def calculate_and_save_covariance_matrix(region_points, path=None, drop_height=False):
    import seaborn as sns
    df = get_data_region(region_points)
    if drop_height:
        df = df[df['Height'].notnull()]
    if path is not None:
        import os
        if not os.path.exists(path):
            os.mkdir(path)

        plt.clf()

        colormap = plt.cm.viridis
        plt.figure(figsize=(12, 12))
        plt.title('Pearson Correlation of Features', y=1.05, size=15)
        x = df.corr(method='pearson')
        print(x)
        sns.heatmap(x, linewidths=0.1, vmax=1.0,
                    square=True, cmap=colormap, linecolor='white', annot=True)
        plt.savefig(path + 'pearson.png')

        plt.clf()

        colormap = plt.cm.viridis
        plt.figure(figsize=(12, 12))
        plt.title('Spearman Correlation of Features', y=1.05, size=15)
        sns.heatmap(df.corr(method='spearman'), linewidths=0.1, vmax=1.0,
                    square=True, cmap=colormap, linecolor='white', annot=True)
        plt.savefig(path + 'spearman.png')

        plt.clf()
    pass


def load_data_from_file(file, verbose=False):
    if verbose:
        print("Loading data")
    krk = pickle.load(open(file, "rb"))
    squares_basic_data, squares_with_data = krk
    if verbose:
        print(squares_basic_data)
        print(squares_with_data)
    return squares_basic_data, squares_with_data


def find_most_popular_locations(path_to_load, path_to_save=None):
    _, squares_with_data = load_data_from_file(path_to_load)

    most_interesting_squares_with_count = count_data_in_squares(squares_with_data)

    how_many = 50
    if how_many > len(most_interesting_squares_with_count):
        how_many = len(most_interesting_squares_with_count) - 1

    most_interesting_squares_with_count = most_interesting_squares_with_count[:how_many]

    if path_to_save is not None:
        if os.path.exists(path_to_save):
            os.remove(path_to_save)
        with open(path_to_save, "w+b") as fp:
            pickle.dump([most_interesting_squares_with_count], fp)

    return most_interesting_squares_with_count


def load_most_popular_locations(most_popular_file, data_file=None, verbose=False, how_many=-1):
    if verbose:
        print("Loading data")
    squares_with_count = pickle.load(open(most_popular_file, "rb"))
    squares_with_count = squares_with_count[0]
    # squares, count = squares_with_count
    if how_many == -1:
        how_many = len(squares_with_count) - 1
    if verbose:
        print(squares_with_count[:3])
    to_ret = []
    if data_file is not None:
        _, squares_with_data = load_data_from_file(data_file, verbose=False)

        for i in range(min(len(squares_with_count), how_many)):
            current_square = squares_with_count[i][0]
            for j in range(len(squares_with_data)):
                # squares_with_data = [(s1, [d1, d2, d3, d4, ...]), ....]
                if current_square == squares_with_data[j][0]:
                    to_ret.append((current_square, squares_with_count[i][1], squares_with_data[j][1]))
                    break
    else:
        for i in range(min(len(squares_with_count), how_many)):
            to_ret.append((squares_with_count[i][0], squares_with_count[i][1], None))
    # [[square,count,[d1,d2,d3]]]
    return to_ret


# [ (s1,[d1,d2,d3,d4,...]) , .... ]
def count_data_in_squares(squares_with_data):
    to_ret = []
    for i in range(len(squares_with_data)):
        s, data = squares_with_data[i]
        count = len(data)
        if count != 0:
            to_ret.append((s, count))
    to_ret.sort(key=lambda x: x[1], reverse=True)
    return to_ret


def calculate_correlation_example():
    # location[(DOWN_LAT, LEFT_LON), (UP_LAT, RIGHT_LON)]
    # calculating correlation height and radiation for regions and plot results
    correlation_list = []
    print("Correlation for Europe")
    pearson, spearman = calculate_correlation_sea_level_radiation(location=globs.regions.EUROPE, verbose=True)
    correlation_list.append(['Europe', pearson['Value']['Height'], spearman['Value']['Height']])

    print("Correlation for Czech")
    pearson, spearman = calculate_correlation_sea_level_radiation(location=globs.regions.CZECH, verbose=True)
    correlation_list.append(['Czech', pearson['Value']['Height'], spearman['Value']['Height']])

    print("Correlation for USA")
    pearson, spearman = calculate_correlation_sea_level_radiation(location=globs.regions.USA, verbose=True)
    correlation_list.append(['USA', pearson['Value']['Height'], spearman['Value']['Height']])

    print("Correlation for Japan")
    pearson, spearman = calculate_correlation_sea_level_radiation(location=globs.regions.JAPAN, verbose=True)
    correlation_list.append(['Japan', pearson['Value']['Height'], spearman['Value']['Height']])

    print("Correlation for Earth")
    pearson, spearman = calculate_correlation_sea_level_radiation(verbose=True)
    correlation_list.append(['Earth', pearson['Value']['Height'], spearman['Value']['Height']])

    for i in range(len(correlation_list)):
        correlation_list[i][1] = 0 if isnan(correlation_list[i][1]) else correlation_list[i][1]
        correlation_list[i][2] = 0 if isnan(correlation_list[i][2]) else correlation_list[i][2]

    place = [x[0] for x in correlation_list]
    pearson = [x[1] for x in correlation_list]
    spearman = [x[2] for x in correlation_list]

    width = 0.4
    fig, ax = plt.subplots()
    x = arange(len(place))
    bar_pearson = ax.bar(x - width / 2, pearson, width, label='Pearson')
    bar_spearman = ax.bar(x + width / 2, spearman, width, label='Spearman')

    ax.set_ylabel('Correlation level')
    ax.set_title('Correlation height with radiation values')
    ax.set_xticks(x)
    ax.set_xticklabels(place)
    ax.legend()

    fig.tight_layout()

    plt.show()


def dump_readable(file):
    squares_basic_data, squares_with_data = load_data_from_file(file, verbose=True)

    with open(file + 'Readable', "w+") as fp:
        fp.write("square,mean,std,max\n")
        for tmp in squares_basic_data:
            s, mean, std, min, max = tmp
            fp.write("{};{};{};{};{}\n".format(str(s), mean, std, min, max))
        fp.write("Raw data for each square\n")
        for tmp in squares_with_data:
            s, d = tmp
            fp.write("{}\n".format(str(s)))
            fp.write(d.to_csv(sep=";"))


if __name__ == "__main__":
    # proceed_region(globs.cities.ROME, file_to_save=globs.cities.ROME_FILE, verbose=True)
    # proceed_region(globs.cities.TOKYO, file_to_save=globs.cities.TOKYO_FILE, verbose=True)
    # proceed_region(globs.cities.KRAKOW, file_to_save=globs.cities.KRAKOW_FILE, verbose=True)
    # proceed_region(globs.cities.CZARNOBYL, file_to_save=globs.cities.CZARNOBYL_FILE, verbose=True)

    # load_data_from_file(globs.cities.ROME_FILE, verbose=True)
    # load_data_from_file(globs.cities.TOKYO_FILE, verbose=True)
    # load_data_from_file(globs.cities.KRAKOW_FILE, verbose=True)
    # load_data_from_file(globs.cities.CZARNOBYL_FILE, verbose=True)
    #

    # calculate_correlation_example()

    # proceed_region(globs.cities.ROME, file_to_save=globs.cities.ROME_FILE, verbose=True, resolution=3000)
    # load_data_from_file(globs.cities.ROME_FILE, verbose=True)
    dump_readable(globs.cities.ROME_FILE)
