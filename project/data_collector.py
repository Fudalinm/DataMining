"""
example request
https://api.safecast.org/measurements.json?distance=400000&latitude=44.5&longitude=135.5
maximum to get in one request is 25 measurements!


IF distance is equal to 1 and we still have more than 25 records we need to upgrade algorithm
or try to take records on different dates
"""
import requests
import csv
import os
import concurrent.futures
import globs
import grid



def send_request_one_square(centre, distance):
    if centre.latitude > 90 or centre.latitude < -90 or centre.longitude > 180 or centre.longitude < -180:
        return
    to_ret = []
    page = 1
    while True:
        req_url = globs.globals.front_query + "distance=" + str(distance) + "&latitude=" + str(
            centre.latitude) + "&longitude=" \
                  + str(centre.longitude) + "&page=" + str(page)
        response = send_single_request(centre, distance, page)
        page += 1
        to_ret.extend(response)
        if len(response) != globs.globals.MAX_IN_SINGLE_QUERY:
            color = globs.bcolors.OK
            if len(to_ret) <= 0:
                color = globs.bcolors.WARNING
            print(color + "LINK: " + globs.bcolors.ENDC + req_url + "\n")
            return to_ret
        else:
            if page > 60:
                to_ret.extend(send_request_multitude_data(centre, distance, pages_paralel=40, start_page=page))
                print(globs.bcolors.OK + "MULTITUDE LINK: " + globs.bcolors.ENDC + req_url + "\n")
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
                if len(to_extend) < globs.globals.MAX_IN_SINGLE_QUERY:
                    f_end = True
            start_page += pages_paralel
            if f_end:
                return to_ret


def send_single_request(centre, distance, page):
    req_url = globs.globals.front_query + "distance=" + str(distance) + "&latitude=" + str(
        centre.latitude) + "&longitude=" \
              + str(centre.longitude) + "&page=" + str(page)
    try:
        response = requests.get(req_url, timeout=5).json()
    except Exception as e:
        try:
            response = requests.get(req_url, timeout=5).json()
        except Exception as ex:
            with open(globs.globals.LOG_FILE_PATH, "a+") as f:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                f.write("!!!\nError while downloading data in: "
                        "latitude: {}, longitude: {}, distance: {}, exception: {}\n!!\n".format(
                    centre.latitude, centre.longitude, distance, str(template.format(type(ex).__name__, ex.args))))
            response = []
    return response


def init_files():
    if os.path.exists(globs.globals.LOG_FILE_PATH):
        os.remove(globs.globals.LOG_FILE_PATH)
    for path in [globs.globals.PROPER_DATA_FILE, globs.globals.NOT_VALID_DATA_FILE]:
        if os.path.exists(path):
            os.remove(path)
        with open(path, "w+", newline="") as f:
            cw = csv.DictWriter(f, globs.globals.ELEMENTS_TO_SAVE_API, delimiter=',', quotechar='|',
                                quoting=csv.QUOTE_MINIMAL)
            cw.writeheader()


def save_to_file(file_path, log_file, data, centre, distance):
    for d in data:
        keys_to_remove = []
        for k in d.keys():
            if k not in globs.globals.ELEMENTS_TO_SAVE_API:
                keys_to_remove.append(k)
        for to_remove in keys_to_remove:
            d.pop(to_remove)

    with open(file_path, "a", newline="") as f:
        cw = csv.DictWriter(f, globs.globals.ELEMENTS_TO_SAVE_API, delimiter=',', quotechar='|',
                            quoting=csv.QUOTE_MINIMAL)
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
    centre = grid.Point(points_list=points)
    distance = centre.distance(points[0])
    json_data = send_request_one_square(centre=centre, distance=distance)
    save_to_file(globs.globals.PROPER_DATA_FILE, globs.globals.LOG_FILE_PATH, json_data, centre, distance)


def capture_whole_data(grid, threads_number):
    print(globs.bcolors.HEADER + "Capturing data" + globs.bcolors.ENDC)
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
            print(globs.bcolors.PROGRESS + "Completed {}%".format((t * 100) / queries_count) + globs.bcolors.ENDC)
        concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
    return


def run(percent_to_download=-1):
    globs.globals.DATA_DIR = "./data/"
    globs.globals.PROPER_DATA_FILE = globs.globals.DATA_DIR + "actual_data{}.csv".format(percent_to_download)
    globs.globals.LOG_FILE_PATH = globs.globals.DATA_DIR + "logs{}".format(percent_to_download)
    globs.globals.PROPER_DATA_FILE = globs.globals.DATA_DIR + "actual_data{}.csv".format(percent_to_download)
    globs.globals.NOT_VALID_DATA_FILE = globs.globals.DATA_DIR + "to_much{}.csv".format(percent_to_download)

    init_files()
    # init grid
    if not os.path.exists(globs.globals.GRID_FILE_TO_SAVE):
        grid.create_save_grid()
    g_tmp = grid.load_grid(percent_to_download)
    # capturing data
    capture_whole_data(g_tmp, 300)



if __name__ == "__main__":
    # for p in range(16, 25, 1):
    #     run(p)
    print("Hello data_collector")

