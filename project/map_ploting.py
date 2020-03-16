import globs
import grid
import data_processing
# from shapely.geometry import Polygon
import gmaps

gmaps.configure(api_key="xxxx")
from math import isnan


# squares_basic_data
#                (
# Points         [(41.75, 12.27), (41.75, 12.347673038839645), (41.79491515527169, 12.27), (41.79491515527169, 12.347673038839645)],
# mean           71.94553881807647, (can be nan)
# std            21.64184419891216, (can be nan)
# min            20.0,              (can be nan)
# max            127.0              (can be nan)
#                )

# squares_with_data
# [([(41.75, 12.27), (41.75, 12.347673038839645), (41.79491515527169, 12.27), (41.79491515527169, 12.347673038839645)], Captured Time   Latitude  Longitude  Value Unit  Height
# Data frame can be also empty

def create_base_map_plots(load_file, file_prefix, border, verbose=False):
    squares_basic_data, squares_with_data = data_processing.load_data_from_file(load_file, verbose=verbose)

    # need to find borders
    lat_c, lon_c = grid.calculate_center_point(border)
    radious = grid.calculate_distance(grid.calculate_center_point(squares_basic_data[0][0]),
                                      squares_basic_data[0][0][0])

    # polygons = []
    locations = []
    stds = []
    means = []
    mins = []
    maxs = []
    for pol, mean, std, min, max in squares_basic_data:
        locations.append(grid.calculate_center_point(pol))
        # polygons.append(Polygon(pol))
        stds.append(std)
        means.append(mean)
        mins.append(min)
        maxs.append(max)

    # TODO: replace nans with 0

    for fig_type, data in [("Mean", means), ("Std", stds), ("Min", mins), ("Max", maxs)]:
        save_file = globs.globals.MAP_PLOT_DIR + file_prefix + fig_type + '.html'
        if verbose:
            print("Current file is" + save_file)

        data = [0 if isnan(x) else x for x in data]
        fig = gmaps.figure(center=(lat_c, lon_c), zoom_level=13)
        heat_layer = gmaps.heatmap_layer(locations=locations, weights=data)

        fig.add_layer(heat_layer)

        # TODO Set radius properly


if __name__ == "__main__":
    create_base_map_plots(globs.cities.TOKYO_FILE, "Tokyo", globs.cities.TOKYO, True)
