"""
example request
https://api.safecast.org/measurements.json?distance=400000&latitude=44.5&longitude=135.5
maximum to get in one request is 25 measurements!


IF distance is equal to 1 and we still have more than 25 records we need to upgrade algorithm
or try to take records on different dates
"""
import requests
import math
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
GRID_FILE_TO_SAVE = "./data/grid.npy"
ELEMENTS_TO_SAVE = ['id', 'user_id', 'value', 'unit', 'height', 'latitude', 'longitude', 'captured_at',
                    'measurement_import_id']

front_query = "https://api.safecast.org/measurements.json?"


class bcolors:
    OK = '\033[92m'
    PROGRESS = '\033[95m'
    HEADER = "\033[1;36m"
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Point:
    def __init__(self, latitude=-200.0, longitude=-200.0, points_list=[]):
        if points_list == []:
            self.latitude = latitude
            self.longitude = longitude
        else:
            # we need to do it this way because earth is wrapping and there are wiered cases because of that
            if len(points_list) == 1:
                self.latitude = points_list[0].latitude
                self.longitude = points_list[0].longitude
                return

            x = 0.0
            y = 0.0
            z = 0.0
            for p in points_list:
                radian_latitude = p.latitude * math.pi / 180
                radian_longitude = p.longitude * math.pi / 180

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
        dlon = self.longitude * math.pi / 180 - second.longitude * math.pi / 180
        dlat = self.latitude * math.pi / 180 - second.latitude * math.pi / 180

        a = math.sin(dlat / 2) ** 2 + \
            math.cos(second.latitude * math.pi / 180) * \
            math.cos(self.latitude * math.pi / 180) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        int_distance = int(EARTH_RADIUS * c) + 1
        return int_distance

    def __str__(self):
        return "##POINT##" + "\n\t#latitude: " + str(self.latitude) + "\n\t#longitude: " + str(self.longitude) + "\n"


def create_earth_grid(start, end):
    bm = Basemap(resolution='c')
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
            lon = (j / longer_longitude_perimeter) * 360
            if lon > 180:
                lon -= 360
            longitude_points.append(lon)
        longitude_points.sort()

        points_north = []
        points_south = []
        for longitude in longitude_points:
            points_north.append(Point(latitude_degree_north * 180 / math.pi, longitude))
            points_south.append(Point(latitude_degree_south * 180 / math.pi, longitude))

        squares = []
        for k in range(len(points_south)):
            tmp = [points_north[k], points_north[(k + 1) % len(points_south)], points_south[k],
                   points_south[(k + 1) % len(points_south)]]
            # checking if the square is on land

            if bm.is_land(tmp[0].longitude, tmp[0].latitude):
                squares.append(tmp)

        print(latitude_degree_south)
        grid.extend(squares)

    return grid


def create_earth_grid_basic():
    return create_earth_grid(0, MERIDIAN_LENGTH)


def create_earth_grid_split():
    steps = 8
    step = int(MERIDIAN_LENGTH / steps)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = []
        to_ret = []
        for i in range(steps):
            results.append(executor.submit(create_earth_grid, step * i, step * (i + 1)))
        for g in results:
            to_ret.extend(g.result())
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


def load_grid(percent_to_download):
    print(bcolors.HEADER + "Loading data" + bcolors.ENDC)
    arr = np.load(GRID_FILE_TO_SAVE)
    grid = []

    x, y, z = arr.shape

    if percent_to_download < 0:
        start = 0
        end = x
    else:
        step = int(x / 100)
        start = step * (percent_to_download - 1)
        if percent_to_download != 100:
            end = step * percent_to_download
        else:
            end = x

    for i in range(start, end, 1):
        square = []
        for j in range(y):
            p = Point(arr[i, j, 1], arr[i, j, 0])
            square.append(p)
        grid.append(square)
    return grid


def send_request_one_square(centre, distance):
    if centre.latitude > 90 or centre.latitude < -90 or centre.longitude > 180 or centre.longitude < -180:
        return
    to_ret = []
    page = 1
    while True:
        req_url = front_query + "distance=" + str(distance) + "&latitude=" + str(centre.latitude) + "&longitude=" \
                  + str(centre.longitude) + "&page=" + str(page)
        response = send_single_request(centre, distance, page)
        page += 1
        to_ret.extend(response)
        if len(response) != MAX_IN_SINGLE_QUERY:
            color = bcolors.OK
            if len(to_ret) <= 0:
                color = bcolors.WARNING
            print(color + "LINK: " + bcolors.ENDC + req_url + "\n")
            return to_ret
        else:
            if page > 100:
                to_ret.extend(send_request_multitude_data(centre, distance, pages_paralel=40, start_page=page))
                print(bcolors.OK + "MULTITUDE LINK: " + bcolors.ENDC + req_url + "\n")
                return to_ret


def send_request_multitude_data(centre, distance, pages_paralel=40, start_page=121):
    # 30 pages at the same time
    to_ret = []
    f_end = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=pages_paralel) as executor:
        while True:
            futures = []
            for x in range(start_page, start_page + pages_paralel, 1):
                futures.append(executor.submit(send_single_request(centre, distance, x)))
            concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
            for f in futures:
                to_extend = f.result()
                to_ret.extend(to_extend)
                if len(to_extend) < MAX_IN_SINGLE_QUERY:
                    f_end = True
            start_page += pages_paralel
            if f_end:
                return to_ret


def send_single_request(centre, distance, page):
    req_url = front_query + "distance=" + str(distance) + "&latitude=" + str(centre.latitude) + "&longitude=" \
              + str(centre.longitude) + "&page=" + str(page)
    try:
        response = requests.get(req_url, timeout=5).json()
    except Exception as e:
        try:
            response = requests.get(req_url, timeout=5).json()
        except Exception as ex:
            with open(LOG_FILE_PATH, "a+") as f:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                f.write("!!!\nError while downloading data in: "
                        "latitude: {}, longitude: {}, distance: {}, exception: {}\n!!\n".format(
                    centre.latitude, centre.longitude, distance, str(template.format(type(ex).__name__, ex.args))))
            response = []
    return response


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
                "MANY data in: latitude: {}, longitude: {}, distance: {}, data_count: {}\n".format(centre.latitude,
                                                                                                   centre.longitude,
                                                                                                   distance, len(data)))


def capture_data_fragment(points):
    centre = Point(points_list=points)
    distance = centre.distance(points[0])
    json_data = send_request_one_square(centre=centre, distance=distance)
    save_to_file(PROPER_DATA_FILE, LOG_FILE_PATH, json_data, centre, distance)


def create_save_grid():
    # grid = create_earth_grid_basic()
    grid = create_earth_grid_split()
    save_grid(grid)
    print(len(grid))


def capture_whole_data(grid, threads_number):
    print(bcolors.HEADER + "Capturing data" + bcolors.ENDC)
    queries_count = len(grid)
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads_number) as executor:
        for t in range(0, len(grid), 1):
            if len(futures) < threads_number:
                futures.append(executor.submit(capture_data_fragment, grid[t]))
            else:
                concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)

                futures_ended = []
                for fi in range(len(futures)):
                    if futures[fi].done():
                        futures_ended.append(futures[fi])
                futures = [f for f in futures if f not in futures_ended]

                # check which futures completed
                # remove completed
                # add as much as i can
                for j in range(t, threads_number, 1):
                    futures.append(executor.submit(capture_data_fragment, grid[j]))
                    t += 1
            print(bcolors.PROGRESS + "Completed {}%".format((t * 100) / queries_count) + bcolors.ENDC)
        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
    return


def run(percent_to_download=-1):
    global PROPER_DATA_FILE
    global LOG_FILE_PATH
    global PROPER_DATA_FILE
    global NOT_VALID_DATA_FILE
    global DATA_DIR

    DATA_DIR = "./data/"
    PROPER_DATA_FILE = DATA_DIR + "actual_data{}.csv".format(percent_to_download)
    LOG_FILE_PATH = DATA_DIR + "logs{}".format(percent_to_download)
    PROPER_DATA_FILE = DATA_DIR + "actual_data{}.csv".format(percent_to_download)
    NOT_VALID_DATA_FILE = DATA_DIR + "to_much{}.csv".format(percent_to_download)

    init_files()
    # init grid
    if not os.path.exists(GRID_FILE_TO_SAVE):
        create_save_grid()
    grid = load_grid(percent_to_download)
    # capturing data
    capture_whole_data(grid, 300)


if __name__ == "__main__":
    for p in range(13, 20, 1):
        run(p)
