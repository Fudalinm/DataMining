class bcolors:
    OK = '\033[92m'
    PROGRESS = '\033[95m'
    HEADER = "\033[1;36m"
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class globals:
    DATA_PATH = "./data/measurements.csv"
    DATA_BASE_FILTER_PATH = "./data/measurementsFiltered.csv"
    DATA_BASE_FILTER_PATH_SORTED = "./data/measurementsFilteredSorted.csv"
    DATA_FILTER_HEIGHT_PATH = "./data/measurementsHeightFiltered.csv"
    DATA_FILTER_HEIGHT_PATH_SORTED = "./data/measurementsHeightFilteredSorted.csv"
    ELEMENTS_TO_SAVE_CSV = ['Latitude', 'Longitude', 'Value', 'Unit', 'Height', 'Captured Time']

    MAP_PLOT_DIR = "./data/mapPlots/"
    MAPS_PLOT_MIN_DIR = MAP_PLOT_DIR + "min/"
    MAPS_PLOT_MAX_DIR = MAP_PLOT_DIR + "max/"
    MAPS_PLOT_MEAN_DIR = MAP_PLOT_DIR + "mean/"
    MAPS_PLOT_STD_DIR = MAP_PLOT_DIR + "std/"

    # all constances are in meters
    EQUATOR_LENGTH = int(40076000)  # this is start because we try to capture whole earth in one query
    ONE_DEGREE_LATITUDE = 111321
    MERIDIAN_LENGTH = int(ONE_DEGREE_LATITUDE * 180)
    EARTH_RADIUS = 6374000.0
    MAX_IN_SINGLE_QUERY = 25

    DATA_DIR_API = "./data/api/"
    LOG_FILE_PATH_API = "./logs"
    PROPER_DATA_FILE_API = "./actual_data.csv"
    NOT_VALID_DATA_FILE_API = "./to_much.csv"
    GRID_FILE_TO_SAVE_API = "./data/grid.npy"
    ELEMENTS_TO_SAVE_API = ['id', 'user_id', 'value', 'unit', 'height', 'latitude', 'longitude', 'captured_at',
                            'measurement_import_id']
    FRONT_QUERY_API = "https://api.safecast.org/measurements.json?"


class cities:
    ROME = [(41.75, 12.27), (42.05, 12.73)]
    ROME_FILE = "./data/processed/Rome"
    TOKYO = [(35.49, 139.45), (35.87, 139.95)]
    TOKYO_FILE = "./data/processed/Tokyo"
    KRAKOW = [(49.94, 19.7), (50.16, 20.35)]
    KRAKOW_FILE = "./data/processed/Krakow"
    CZARNOBYL = [(51.24, 30.1), (51.31, 30.34)]
    CZARNOBYL_FILE = "./data/processed/Czarnobyl"
