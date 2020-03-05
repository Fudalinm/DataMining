"""
example request
https://api.safecast.org/measurements.json?distance=400000&latitude=44.5&longitude=135.5
maximum to get in one request is 25 measurements!


IF distance is equal to 1 and we still have more than 25 records we need to upgrade algorithm
or try to take records on different dates
"""
import requests
import math
import itertools
import csv
import os
import numpy as np
from mpl_toolkits.basemap import Basemap
import concurrent.futures

# all constances are in meters
EQUATOR_LENGTH = int(40076000)  # this is start because we try to capture whole earth in one query
ONE_DEGREE_LATITUDE = 111321
MERIDIAN_LENGTH = int(ONE_DEGREE_LATITUDE * 180)
EARTH_RADIUS = 6374000.0

MAX_IN_SINGLE_QUERY = 25

LOG_FILE_PATH = "./logs"
PROPER_DATA_FILE = "./actual_data.csv"
NOT_VALID_DATA_FILE = "./to_much.csv"
GRID_FILE_TO_SAVE = "./grid.npy"
ELEMENTS_TO_SAVE = ['id', 'user_id', 'value', 'unit', 'height', 'latitude', 'longitude', 'captured_at',
                    'measurement_import_id']

front_query = "https://api.safecast.org/measurements.json?"


class Point:
    def __init__(self, latitude=-200.0, longitude=-200.0, points_list=[]):
        if points_list == []:
            self.latitude = latitude
            self.longitude = longitude
        else:
            if len(points_list) == 1:
                self.latitude = points_list[0].latitude
                self.longitude = points_list[0].longitude
                return

            for subset in itertools.combinations(points_list, 3):
                if (subset[0].latitude == subset[1].latitude == subset[2].latitude) \
                        or (subset[0].longitude == subset[1].longitude == subset[2].longitude):
                    self.longitude = -200
                    self.latitude = -200

            x = 0.0
            y = 0.0
            z = 0.0
            for p in points_list:
                radian_latitude = math.radians(p.latitude)
                radian_longitude = math.radians(p.longitude)

                x += math.cos(radian_latitude) * math.cos(radian_longitude)
                y += math.cos(radian_latitude) * math.sin(radian_longitude)
                z += math.sin(radian_latitude)

            total = len(points_list)

            x = x / total
            y = y / total
            z = z / total

            central_longitude = math.atan2(y, x)
            central_square_root = math.sqrt(x * x + y * y)
            central_latitude = math.atan2(z, central_square_root)

            self.latitude = central_latitude * 180 / math.pi
            self.longitude = central_longitude * 180 / math.pi
            return

    def distance(self, second):
        dlon = math.radians(self.longitude) - math.radians(second.longitude)
        dlat = math.radians(self.latitude) - math.radians(second.latitude)

        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(second.latitude)) * math.cos(
            math.radians(self.latitude)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        int_distance = int(EARTH_RADIUS * c) + 1
        return int_distance

    def __str__(self):
        return "##POINT##" + "\n\t#latitude: " + str(self.latitude) + "\n\t#longitude: " + str(self.longitude) + "\n"


def create_earth_grid(start, end):
    print("x")
    bm = Basemap(resolution='c')
    print("d")
    grid = []
    for i in range(start, end, 5000):
        latitude_degree_north = (-(i / MERIDIAN_LENGTH) * 180 + 90) * (math.pi / 180)
        latitude_degree_south = (-((i + 5000) / MERIDIAN_LENGTH) * 180 + 90) * (math.pi / 180)

        longitude_degree_length_north = (math.cos(latitude_degree_north) * EQUATOR_LENGTH) / 360
        longitude_degree_length_south = (math.cos(latitude_degree_south) * EQUATOR_LENGTH) / 360

        if longitude_degree_length_north > longitude_degree_length_south:
            longer_longitude_degree = longitude_degree_length_north
        else:
            longer_longitude_degree = longitude_degree_length_south

        longer_longitude_perimeter = longer_longitude_degree * 360

        longitude_points = []

        for j in range(0, int(longer_longitude_perimeter), 5000):
            longitude_points.append((j / longer_longitude_perimeter) * 360)

        points_north = []
        points_south = []
        for longitude in longitude_points:
            points_north.append(Point(latitude_degree_north, longitude))
            points_south.append(Point(latitude_degree_south, longitude))

        squares = []
        for k in range(len(points_south)):
            tmp = [points_north[k], points_north[(k + 1) % len(points_south)], points_south[k],
                   points_south[(k + 1) % len(points_south)]]
            # checking if the square is on land

            if bm.is_land(tmp[0].longitude, tmp[0].latitude):
                squares.append(tmp)

        grid.extend(squares)
        print(latitude_degree_south)

    return grid


def create_earth_grid_basic():
    return create_earth_grid(0, MERIDIAN_LENGTH)


def create_earth_grid_split():
    with concurrent.futures.ProcessPoolExecutor() as executor:
        step = int(MERIDIAN_LENGTH / 4)
        g0 = executor.submit(create_earth_grid, step * 0, step * 1)
        g1 = executor.submit(create_earth_grid, step * 1, step * 2)
        g2 = executor.submit(create_earth_grid, step * 2, step * 3)
        g3 = executor.submit(create_earth_grid, step * 3, step * 4)

        to_ret = []
        to_ret.extend(g0.result())
        to_ret.extend(g1.result())
        to_ret.extend(g2.result())
        to_ret.extend(g3.result())
        return to_ret


def save_grid(grid):
    # grid = [ [p1,p2,p3,p4] , ....]
    arr_to_save = np.empty(shape=(len(grid), 4, 2))
    for square_index in range(len(grid)):
        square = grid[square_index]
        for i in range(len(square)):
            arr_to_save[square_index, i, 0] = square[i].longitude
            arr_to_save[square_index, i, 1] = square[i].latitude
    np.save(GRID_FILE_TO_SAVE, arr_to_save)


def load_grid():
    arr = np.load(GRID_FILE_TO_SAVE)
    grid = []

    x, y, z = arr.shape
    for i in range(x):
        square = []
        for j in range(y):
            p = Point(arr[i, j, 1], arr[i, j, 0])
            square.append(p)
        grid.append(square)
    return grid


def send_request(centre, distance):
    if centre.latitude > 90 or centre.latitude < -90 or centre.longitude > 180 or centre.longitude < -180:
        return

    to_ret = []
    page = 1
    while True:
        req_url = front_query + "distance=" + str(distance) + "&latitude=" + str(centre.latitude) + "&longitude=" \
                  + str(centre.longitude) + "&page=" + str(page)
        response = requests.get(req_url).json()
        page += 1
        to_ret.extend(response)
        if len(response) != MAX_IN_SINGLE_QUERY:
            return to_ret


def init_files():
    if os.path.exists(LOG_FILE_PATH):
        os.remove(LOG_FILE_PATH)
    for path in [PROPER_DATA_FILE, NOT_VALID_DATA_FILE]:
        if os.path.exists(path):
            os.remove(path)
        with open(path, "w+", newline="") as f:
            cw = csv.DictWriter(f, ELEMENTS_TO_SAVE, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            cw.writeheader()


def save_to_file(file_path, log_file, data, centre, distance):
    # TODO: filtering unnecesery fields
    for d in data:
        keys_to_remove = []
        for k in d.keys():
            if k not in ELEMENTS_TO_SAVE:
                keys_to_remove.append(k)
        for to_remove in keys_to_remove:
            d.pop(to_remove)

    with open(file_path, "a", newline="") as f:
        cw = csv.DictWriter(f, ELEMENTS_TO_SAVE, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        cw.writerows(data)

    if len(data) == 0:
        with open(log_file, "a+") as f:
            f.write("No data in: latitude: {}, longitude: {}, distance: {}\n".format(centre.latitude, centre.longitude,
                                                                                     distance))
    else:
        with open(log_file, "a+") as f:
            f.write(
                "MANY data in: latitude: {}, longitude: {}, distance: {}, data_count\n".format(centre.latitude,
                                                                                               centre.longitude,
                                                                                               distance, len(data)))

def capture_data_fragment(points):
    centre = Point(points_list=points)
    distance = centre.distance(points[0])
    json_data = send_request(centre=centre, distance=distance)

    save_to_file(PROPER_DATA_FILE, LOG_FILE_PATH, json_data, centre, distance)


def create_save_grid():
    # grid = create_earth_grid_basic()
    grid = create_earth_grid_split()
    save_grid(grid)
    print(len(grid))


def capture_whole_data(grid):
    init_files()
    for square in grid:
        capture_data_fragment(square)


if __name__ == "__main__":
    # capture_whole_data()
    create_save_grid()
    # grid = load_grid()
    # print(len(grid))
