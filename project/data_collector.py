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
# import time

START_LATITUDE = 0  # stopien ma stala wartosc dlugosci
START_LONGITUDE = 0
HALF_EQUATOR_KM = int(40076000 / 2)  # this is start because we try to capture whole earth in one query
MAX_IN_SINGLE_QUERY = 25
EARTH_RADIUS = 6374000.0

LOG_FILE_PATH = "./logs"
PROPER_DATA_FILE = "./actual_data.csv"
NOT_VALID_DATA_FILE = "./to_much.csv"
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


def send_request(centre, distance):
    if centre.latitude > 90 or centre.latitude < -90 or centre.longitude > 180 or centre.longitude < -180:
        return

    req_url = front_query + "distance=" + str(distance) + "&latitude=" + str(centre.latitude) + "&longitude=" \
              + str(centre.longitude)

    response = requests.get(req_url).json()

    if response == []:
        print(req_url)
        print(response)

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


def save_to_file(file_path, data):
    # print(data)
    # TODO: filtering unnecesery fields
    for d in data:
        keys_to_remove = []
        for k in d.keys():
            if k not in ELEMENTS_TO_SAVE:
                keys_to_remove.append(k)
        for to_remove in keys_to_remove:
            d.pop(to_remove)

    # print(data)

    with open(file_path, "a", newline="") as f:
        cw = csv.DictWriter(f, ELEMENTS_TO_SAVE, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        cw.writerows(data)


def capture_data_fragment(points):
    # print("*****")
    # for p in points:
    #     print(str(p))
    # time.sleep(1)

    centre = Point(points_list=points)
    distance = centre.distance(points[0])
    json_data = send_request(centre=centre, distance=distance)

    # print("****")
    # TODO: if distance is equal 1 we should split through time

    if len(json_data) == MAX_IN_SINGLE_QUERY:
        with open(LOG_FILE_PATH, "a+") as f:
            f.write("MANY data in: latitude: {}, longitude: {}, distance: {}\n".format(centre.latitude, centre.longitude,
                                                                                      distance))

        save_to_file(NOT_VALID_DATA_FILE, json_data)
        for subset in itertools.combinations(points, 2):
            tmp_list = list(subset)
            tmp_list.append(centre)
            capture_data_fragment(tmp_list)

    elif len(json_data) == 0:
        # TODO: log about fragment without any records
        with open(LOG_FILE_PATH, "a+") as f:
            f.write("No data in: latitude: {}, longitude: {}, distance: {}\n".format(centre.latitude, centre.longitude,
                                                                                    distance))
    else:
        save_to_file(PROPER_DATA_FILE, json_data)


def capture_whole_data():
    init_files()

    # Whole earth
    # end = Point(0.0, 180.0)
    # centre = Point(0.0, 0.0)
    #
    # north = Point(90.0, 0.0)
    # south = Point(-90.0, 0.0)
    #
    # centre_half_east = Point(0.0, 90.0)
    # centre_half_west = Point(0.0, -90.0)
    #
    # for cord1 in [end, centre]:
    #     for cord2 in [north, south]:
    #         for cord3 in [centre_half_west, centre_half_east]:
    #             # print("********************")
    #             cords = [cord1, cord2, cord3]
    #             # centre = Point(points_list=cords)
    #             # print("CORDS:")
    #             # for c in cords:
    #             #     print(c)
    #             # print("CENTRE:")
    #             # print(str(centre))
    #             capture_data_fragment(cords)

    # Rome
    north = Point(43, 12.4964)
    south = Point(41, 12.4964)
    west = Point(41.9028, 11)
    east = Point(41.9028, 14)
    cords = [north, south, east, west]
    capture_data_fragment(cords)


if __name__ == "__main__":
    capture_whole_data()
