import grid
import globs
import data_preproccesing
import data_processing

if __name__ == "__main__":
    # Preprocessing
    print("Data pre processing phase. It will take more then a while")
    data_preproccesing.filter_whole_data(globs.globals.DATA_PATH, globs.globals.DATA_BASE_FILTER_PATH, globs.globals.ELEMENTS_TO_SAVE_CSV)
    data_preproccesing.filter_height(globs.globals.DATA_BASE_FILTER_PATH, globs.globals.DATA_FILTER_HEIGHT_PATH, globs.globals.ELEMENTS_TO_SAVE_CSV)
    data_preproccesing.sort_data(globs.globals.DATA_BASE_FILTER_PATH, globs.globals.DATA_BASE_FILTER_PATH_SORTED)
    data_preproccesing.sort_data(globs.globals.DATA_FILTER_HEIGHT_PATH, globs.globals.DATA_FILTER_HEIGHT_PATH_SORTED)
    
    # Data processing
    print("Data processing phase it will be much faster")
    data_processing.proceed_region(globs.cities.ROME, file_to_save=globs.cities.ROME_FILE)
    data_processing.proceed_region(globs.cities.TOKYO, file_to_save=globs.cities.TOKYO_FILE)
    data_processing.proceed_region(globs.cities.KRAKOW, file_to_save=globs.cities.KRAKOW_FILE)
    data_processing.proceed_region(globs.cities.CZARNOBYL, file_to_save=globs.cities.CZARNOBYL_FILE)
