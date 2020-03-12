import pandas as pd
import os
import globs


def filter_whole_data(path_to_load, path_to_save, columns_to_save):
    df_iter = pd.read_csv(path_to_load, chunksize=500000, iterator=True, usecols=columns_to_save)
    # f = open(path_to_save, "w+")
    # TODO: write header to csv

    if os.path.exists(path_to_save):
        os.remove(path_to_save)

    for iter_num, chunk in enumerate(df_iter, 1):
        cpm_mask = chunk['Unit'] == "cpm"
        only_cpm_csv = chunk[cpm_mask]
        # print(only_cpm_csv)
        only_cpm_csv.to_csv(path_to_save, mode='a', header=iter_num == 1, index=False)


def filter_height(path_to_load, path_to_save, columns_to_save):
    df_iter = pd.read_csv(path_to_load, chunksize=1000000, iterator=True, usecols=columns_to_save)

    if os.path.exists(path_to_save):
        os.remove(path_to_save)

    for iter_num, chunk in enumerate(df_iter, 1):
        # print(chunk['Height'])
        height_mask = ~chunk['Height'].isna()
        # print(height_mask)
        only_height_csv = chunk[height_mask]
        only_height_csv.to_csv(path_to_save, mode='a', header=iter_num == 1, index=False)


def sort_data(path_to_file, columns):
    df = pd.read_csv(path_to_file)
    df.sort_values(axis=0, ascending=True, by=columns, inplace=True)
    df.to_csv(path_to_file + 'sorted', header=True, index=False)


if __name__ == "__main__":
    # filter_whole_data(globs.globals.DATA_PATH, globs.globals.DATA_BASE_FILTER_PATH,
    #                   globs.globals.ELEMENTS_TO_SAVE_CSV)
    # filter_height(globs.globals.DATA_BASE_FILTER_PATH, globs.globals.DATA_FILTER_HEIGHT_PATH,
    #               globs.globals.ELEMENTS_TO_SAVE_CSV)
    # sort_data("./data/measurementsNoHeightFiltered.csv", 'Latitude')
    # sort_data(DATA_BASE_FILTER_PATH)
    print("Hello data_preproc")