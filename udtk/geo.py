import pandas as pd
import geopandas as gpd
import numpy as np
import pysal as ps
import pickle
from h3 import h3
from shapely.geometry import Polygon


def shapely_from_h3(h3_index):
    return Polygon([[i[1], i[0]] for i in h3.h3_to_geo_boundary(h3_index)])

# we can split this function for loading csv or shape and turn into a table with x and y cols
# the use a single function to turn this table into hexgrid


def hexgrid_from_shapefile(input_shapefile, output_shapefile, res):
    carto = gpd.read_file(input_shapefile)

    # make changes to get h3 grid
    carto = carto.to_crs(epsg=4326)
    carto['y'] = carto.geometry.y
    carto['x'] = carto.geometry.x
    carto['h3_index'] = carto.apply(lambda geom: h3.geo_to_h3(geom.y, geom.x, res), axis=1)
    carto = carto.groupby('h3_index').size().to_frame('n').reset_index()

    # create shapefile
    geoms = carto['h3_index'].map(shapely_from_h3)
    carto = gpd.GeoDataFrame(carto, geometry=geoms, crs={'init': 'epsg:4326', 'no_defs': True})
    carto = carto.to_crs({'init': 'epsg:3857', 'no_defs': True})
    carto.to_file(output_shapefile)
    return carto


def weights_matrix(grid_id_name, input_shapefile='carto/grid/grid.shp', output_pickle='data/w.pickle'):
    # produce weights matrix
    w = ps.lib.weights.Queen.from_shapefile(
        input_shapefile, idVariable=grid_id_name)

    # save data
    with open(output_pickle, 'wb') as handle:
        pickle.dump(w, handle)
    return w
