import pandas as pd
import geopandas as gpd
import numpy as np
import pysal as ps
import pickle
from h3 import h3
from shapely.geometry import Polygon


def shapely_from_h3(h3_index):
    return Polygon([[i[1], i[0]] for i in h3.h3_to_geo_boundary(h3_index)])


def h3_from_row(row, res):
    return h3.geo_to_h3(row['y'], row['x'], res=res)


def h3_df_to_gdf(df, h3_index_col):
    geoms = df[h3_index_col].map(shapely_from_h3)
    gdf = gpd.GeoDataFrame(df, geometry=geoms, crs={'init': 'epsg:4326', 'no_defs': True})
    return gdf


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


def h3_indexing(df, res):
    """
    This function takes a table with point coordinates in latlong
    and returns the same table with h3 indexes

    Parameters:
    dt (pandas.DataFrame):
        Table with point coordinates in latlong stored in x and y
    res (list):
        List containing range of h3 resolutions from 0 to 15.
        Allows a single resolution level res = [5].
    Returns:
    dt:Table with h3 indexes for all resolutions
    """
    if len(res) == 1:
        res.append(res[0])

    for i in res:
        df['h3_res_' + str(i)] = df.apply(h3_from_row, axis=1, args=[i])

    return df


def aggregate_data(df, aggregation_col, aggregation_dict):
    agg_df = df.reindex(columns=[aggregation_col] + list(aggregation_dict.keys())) \
        .groupby(aggregation_col).agg(aggregation_dict).reset_index()
    h3_gdf = h3_df_to_gdf(df=agg_df, h3_index_col=aggregation_col)
    return h3_gdf
