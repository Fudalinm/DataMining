import globs
import numpy as np
import math
import concurrent
from mpl_toolkits.basemap import Basemap


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

        int_distance = int(globs.globals.EARTH_RADIUS * c) + 1
        return int_distance

    def __str__(self):
        return "##POINT##" + "\n\t#latitude: " + str(self.latitude) + "\n\t#longitude: " + str(self.longitude) + "\n"


def create_earth_grid(start, end):
    bm = Basemap(resolution='c')
    grid = []
    for i in range(start, end, 5000):
        latitude_degree_north = (-(i / globs.globals.MERIDIAN_LENGTH) * 180 + 90) * (math.pi / 180)
        latitude_degree_south = (-((i + 5000) / globs.globals.MERIDIAN_LENGTH) * 180 + 90) * (math.pi / 180)

        longitude_degree_length_north = (math.cos(latitude_degree_north) * globs.globals.EQUATOR_LENGTH) / 360
        longitude_degree_length_south = (math.cos(latitude_degree_south) * globs.globals.EQUATOR_LENGTH) / 360

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
    return create_earth_grid(0, globs.globals.MERIDIAN_LENGTH)


def create_earth_grid_split():
    steps = 8
    step = int(globs.globals.MERIDIAN_LENGTH / steps)
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
    np.save(globs.globals.GRID_FILE_TO_SAVE_API, arr_to_save)


def load_grid(percent_to_download):
    print(globs.bcolors.HEADER + "Loading data" + globs.bcolors.ENDC)
    arr = np.load(globs.globals.GRID_FILE_TO_SAVE_API)
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


def create_save_grid():
    # grid = create_earth_grid_basic()
    grid = create_earth_grid_split()
    save_grid(grid)
    print(len(grid))


"""
TODO: it wont work if crossing the 180 degree lon
                            NORTH
             (lat1,lon1) --------------- (lat1,lon2)
             |                                  |
             |                                  |
    WEST     |                                  |     EAST
             |                                  |
             |                                  |
             (lat2,lon1)----------------- (lat2,lon2)
                            SOUTH
"""


def create_grid_for_surface(lat1, lon1, lat2, lon2, resolution=5000.0):
    grid = []

    if lon1 > lon2:
        grid.extend(create_grid_for_surface(lat1, lon1, lat2, 180))
        grid.extend(create_grid_for_surface(lat1, 0, lat2, lon2))
        return grid

    degree_step = resolution / globs.globals.ONE_DEGREE_LATITUDE
    for latitude_degree_north in np.arange(lat1, lat2 + degree_step, degree_step):
        latitude_degree_south = latitude_degree_north + degree_step

        longitude_degree_length_north = (math.cos(latitude_degree_north) * globs.globals.EQUATOR_LENGTH) / 360
        longitude_degree_length_south = (math.cos(latitude_degree_south) * globs.globals.EQUATOR_LENGTH) / 360

        if longitude_degree_length_north > longitude_degree_length_south:
            longer_longitude_degree = longitude_degree_length_north
        else:
            longer_longitude_degree = longitude_degree_length_south
        longer_longitude_perimeter = abs(longer_longitude_degree * 360)

        longitude_step = (resolution * 360) / longer_longitude_perimeter
        longitude_points = []

        for longitude in np.arange(lon1, lon2 + longitude_step, longitude_step):

            if longitude > 180:
                longitude -= 360
            longitude_points.append(longitude)

        longitude_points.sort()

        squares = []
        for k in range(len(longitude_points)):
            squares.append([(latitude_degree_north, longitude_points[k]),  # A
                            (latitude_degree_north, longitude_points[(k + 1) % len(longitude_points)]),  # B
                            (latitude_degree_south, longitude_points[k]),  # C
                            (latitude_degree_south, longitude_points[(k + 1) % len(longitude_points)])])  # D
        grid.extend(squares)
    return grid


# Order is very important
# we dont use p3 and p4 because we dont need to, we always assume that we make rectangle
def create_grid_for_surface_from_points(p1, p2, resolution=5000):
    return create_grid_for_surface(p1[0], p1[1], p2[0], p2[1], resolution=resolution)


def calculate_center_point(points_list):
    if len(points_list) == 1:
        return points_list[0][0], points_list[0][1]

    x = 0.0
    y = 0.0
    z = 0.0
    for p in points_list:
        radian_latitude = p[0] * math.pi / 180
        radian_longitude = p[1] * math.pi / 180

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

    return central_latitude * 180 / math.pi, central_longitude * 180 / math.pi


def calculate_distance(p1, p2):
    dlon = p1[1] * math.pi / 180 - p2[1] * math.pi / 180
    dlat = p1[0] * math.pi / 180 - p2[0] * math.pi / 180

    a = math.sin(dlat / 2) ** 2 + \
        math.cos(p2[0] * math.pi / 180) * \
        math.cos(p1[0] * math.pi / 180) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return int(globs.globals.EARTH_RADIUS * c) + 1


if __name__ == "__main__":
    print(create_grid_for_surface_from_points(globs.cities.TOKYO[0], globs.cities.TOKYO[1]))
    print(create_grid_for_surface_from_points(globs.cities.ROME[0], globs.cities.ROME[1]))
    print(create_grid_for_surface_from_points(globs.cities.CZARNOBYL[0], globs.cities.CZARNOBYL[1]))
    print(create_grid_for_surface_from_points(globs.cities.KRAKOW[0], globs.cities.KRAKOW[1]))

    # g = create_grid_for_surface(12.27, 12.73, 42.05, 41.75)
    # g = create_grid_for_surface_from_points((41.75, 12.27), (42.05, 12.73))
    # print(g)
    # for square in g:
    #     print("##########")
    #     print(square)
