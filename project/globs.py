class bcolors:
    OK = '\033[92m'
    PROGRESS = '\033[95m'
    HEADER = "\033[1;36m"
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# This class is messy but concept radically changed ;c
class general:
    DATA_PATH = "./data/measurements.csv"
    DATA_BASE_FILTER_PATH = "./data/measurementsFiltered.csv"
    DATA_BASE_FILTER_PATH_SORTED = "./data/measurementsFilteredSorted.csv"
    DATA_FILTER_HEIGHT_PATH_SORTED = "./data/measurementsHeightFilteredSorted.csv"
    DATA_FLIGHTS = './data/flights.csv'
    MEASUREMENTS_IN_MONTH = './data/measurementsInMonth.csv'
    ELEMENTS_TO_SAVE_CSV = ['Latitude', 'Longitude', 'Value', 'Unit', 'Height', 'Captured Time']

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


class plots:
    GENERAL_PLOTS_PATH = './data/plots/_general/'
    DISTRIBUTION_PATH = GENERAL_PLOTS_PATH + 'distribution'
    VALUE_DISTRIBUTION_PLOT_PATH = DISTRIBUTION_PATH + 'ValueDistributionPlot.png'
    VALUE_DISTRIBUTION_BUCKETS_PATH = DISTRIBUTION_PATH + 'ValueBucketList'
    HEIGHT_DISTRIBUTION_PATH = DISTRIBUTION_PATH + 'Height.png'


# location[(DOWN_LAT, LEFT_LON), (UP_LAT, RIGHT_LON)]
class cities:
    PROCESSED_DATA_DIR = './data/processed/'
    MAP_PLOT_DIR = './data/plots/'

    ROME = [(41.75, 12.27), (42.05, 12.73)]
    ROME_FILE = PROCESSED_DATA_DIR + "Rome"
    ROME_MAP_DIR = MAP_PLOT_DIR + "Rome/"

    TOKYO = [(35.49, 139.45), (35.87, 139.95)]
    TOKYO_FILE = PROCESSED_DATA_DIR + "Tokyo"
    TOKYO_MAP_DIR = MAP_PLOT_DIR + "Tokyo/"

    KRAKOW = [(49.94, 19.7), (50.16, 20.35)]
    KRAKOW_FILE = PROCESSED_DATA_DIR + "Krakow"
    KRAKOW_MAP_DIR = MAP_PLOT_DIR + "Krakow/"

    CZARNOBYL = [(51.24, 30.1), (51.31, 30.34)]
    CZARNOBYL_FILE = PROCESSED_DATA_DIR + "Czarnobyl"
    CZARNOBYL_MAP_DIR = MAP_PLOT_DIR + "Czarnobyl/"


"""
    EUROPE = [(37, -8), (58, 32)] <- left down corrner coordinates of Europe and up right coordinetes of europe (sequance is important)
    EUROPE_FILE = PROCESSED_DATA_DIR + 'Europe' <- file containing data for europe squares with complete data and crucial data like mean or std
    EUROPE_MAP_DIR = MAP_PLOT_DIR + 'Europe/' <- directory to create maps of radiation of particiular region
    EUROPE_MOST_POPULAR = MOST_POPULAR_DIR + 'Europe' <- directory to save top most popular (usully 50) squares of particiular region
"""


class regions:
    PROCESSED_DATA_DIR = './data/processed/'
    MAP_PLOT_DIR = './data/plots/'
    MOST_POPULAR_DIR = './data/mostPopular/'

    EUROPE = [(37, -8), (58, 32)]
    EUROPE_FILE = PROCESSED_DATA_DIR + 'Europe'
    EUROPE_MAP_DIR = MAP_PLOT_DIR + 'Europe/'
    EUROPE_MOST_POPULAR = MOST_POPULAR_DIR + 'Europe'

    AFRIKA_N = [(6, -17), (35, 47)]
    AFRIKA_N_FILE = PROCESSED_DATA_DIR + 'AfrikaN'
    AFRIKA_N_MAP_DIR = MAP_PLOT_DIR + 'AfrikaN/'
    AFRIKA_N_MOST_POPULAR = MOST_POPULAR_DIR + 'AfrikaN'

    AFRIKA_S = [(-33, 11), (6, 50)]
    AFRIKA_S_FILE = PROCESSED_DATA_DIR + 'AfrikaS'
    AFRIKA_S_MAP_DIR = MAP_PLOT_DIR + 'AfrikaS/'
    AFRIKA_S_MOST_POPULAR = MOST_POPULAR_DIR + 'AfrikaS'

    ASIA_N = [(53, 34), (76, 178)]
    ASIA_N_FILE = PROCESSED_DATA_DIR + 'AsiaN'
    ASIA_N_MAP_DIR = MAP_PLOT_DIR + 'AsiaN/'
    ASIA_N_MOST_POPULAR = MOST_POPULAR_DIR + 'AsiaN'

    ASIA_S = [(8, 51), (50, 146)]
    ASIA_S_FILE = PROCESSED_DATA_DIR + 'AsiaS'
    ASIA_S_MAP_DIR = MAP_PLOT_DIR + 'AsiaS/'
    ASIA_S_MOST_POPULAR = MOST_POPULAR_DIR + 'AsiaS'

    POLAND = [(48.9, 14.9), (54.5, 24.2)]
    POLAND_FILE = PROCESSED_DATA_DIR + 'Poland'
    POLAND_MAP_DIR = MAP_PLOT_DIR + 'Poland/'
    POLAND_MOST_POPULAR = MOST_POPULAR_DIR + 'Poland'

    USA = [(26, -126), (49, -65)]
    USA_FILE = PROCESSED_DATA_DIR + 'USA'
    USA_MAP_DIR = MAP_PLOT_DIR + 'USA/'
    USA_MOST_POPULAR = MOST_POPULAR_DIR + 'USA'

    CZECH = [(48.5, 12), (51, 19)]
    CZECH_FILE = PROCESSED_DATA_DIR + 'Czech'
    CZECH_MAP_DIR = MAP_PLOT_DIR + 'Czech/'
    CZECH_MOST_POPULAR = MOST_POPULAR_DIR + 'Czech'

    JAPAN = [(30, 128), (46, 147)]
    JAPAN_FILE = PROCESSED_DATA_DIR + 'Japan'
    JAPAN_MAP_DIR = MAP_PLOT_DIR + 'Japan/'
    JAPAN_MOST_POPULAR = MOST_POPULAR_DIR + 'Japan'
