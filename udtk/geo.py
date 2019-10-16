import pandas as pd
import geopandas as gpd
import numpy as np
import pysal as ps
import pickle
from h3 import h3
from shapely.geometry import Polygon


def shapely_from_h3(h3_index):
    """
    This function takes a h3 index id and returns a shapely Polygon

    Parameters:
    h3_index (str):
        H3 index id
    Returns:
    shapely.Polygon : cell Polygon
    """

    return Polygon([[i[1], i[0]] for i in h3.h3_to_geo_boundary(h3_index)])


def h3_from_row(row, res, x_col, y_col):
    """
    This function takes a pandas DataFrame row with a lat and long point coordinate columns
    and resolution level and returns a h3 index for that resolution

    Parameters:
    row (pandas.Series):
        pandas DataFrame row
    res (int):
        h3 resolution level
    x_col (str):
        column name with the x coordinate
    y_col (str):
        column name with the y coordinate

    Returns:
    str : H3 index id
    """
    return h3.geo_to_h3(row[y_col], row[x_col], res=res)


def h3_df_to_gdf(df, h3_index_col):
    """
    This function takes a pandas DataFrame and a column containing h3 indexes and returns a
    geopandas GeoDataFrame

    Parameters:
    df (pandas.DataFrame):
        DataFrame with h3 indexes
    h3_index_col (str):
        column containing h3 indexes
    Returns:
    geopandas.GeoDataFrame : GeoDataFrame with the hexgrid as geometries
    """

    geoms = df[h3_index_col].map(shapely_from_h3)
    gdf = gpd.GeoDataFrame(df, geometry=geoms, crs={'init': 'epsg:4326', 'no_defs': True})
    return gdf


def h3_indexing(df, res, x_col='x', y_col='y'):
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
        df['h3_res_' + str(i)] = df.apply(h3_from_row, axis=1, args=[i, x_col, y_col])

    return df


def aggregate_h3(df, h3_index_col, aggregation_dict):
    """
    This function takes a pandas DataFrame with granular data referenced
    with a h3 index and variables to aggregate, the column containing h3 indexes and the aggregation
    method for each variable and returns a geopandas GeoDataFrame with aggregated data for each
    geometry


    Parameters:
    dt (pandas.DataFrame):
        DataFrame with granular data referenced with a h3 index and variables to aggregate
    h3_index_col (str):
        Column containing h3 indexes
    aggregation_dict (dict):
        Dictionary with column names as keys and method of agreggation as values
    Returns:
    geopandas.GeoDataFrame : GeoDataFrame with the hexgrid as geometries and aggregated data
    """

    agg_df = df.reindex(columns=[h3_index_col] + list(aggregation_dict.keys())) \
        .groupby(h3_index_col).agg(aggregation_dict).reset_index()
    h3_gdf = h3_df_to_gdf(df=agg_df, h3_index_col=h3_index_col)
    return h3_gdf


def hexgrid_from_shapefile(input_shapefile, res, output_shapefile=False):
    """
    This function takes a point data shapefile path, a h3 resolution level and a path to save the file

    Parameters:
    input_shapefile (str):
        path to the point data shapefile
    res (int):
        Single h3 resolution level from 0 to 15.
    output_shapefile (str):
        path to the final polygon data shapefile
    Returns:
    geopandas.GeoDataFrame : GeoDataFrame with the hexgrid at a given resolution as geometries
    """
    carto = gpd.read_file(input_shapefile)

    # make changes to get h3 grid
    carto = carto.to_crs(epsg=4326)
    carto['y'] = carto.geometry.y
    carto['x'] = carto.geometry.x

    # produce h3 indexis for each parcel
    carto = h3_indexing(carto, res=[res])

    # group by h3 index and get count of parcels within each cell
    carto = carto.groupby('h3_res_%i' % res).size().to_frame('n').reset_index()

    # create shapefile
    carto = h3_df_to_gdf(df=carto, h3_index_col='h3_res_%i' % res)

    carto = carto.to_crs({'init': 'epsg:3857', 'no_defs': True})

    if output_shapefile:
        carto.to_file(output_shapefile)

    return carto


def weights_matrix(grid_id_name, input_shapefile='carto/grid/grid.shp', output_pickle=False):
    """
    This function takes a h3 hexgird shapefile path, a grid id name and a output path and returns a
    pysal weights matrix

    Parameters:
    grid_id_name (str):
        column name containing the id of the cell
    input_shapefile (str):
        path to the point data shapefile
    output_shapefile (str):
        path to the final matrix picle file
    Returns:
        pysal.lib.weights : weights matrix for the hexgrid
    """
    # produce weights matrix
    w = ps.lib.weights.Queen.from_shapefile(
        input_shapefile, idVariable=grid_id_name)

    # save data
    if output_pickle:
        with open(output_pickle, 'wb') as handle:
            pickle.dump(w, handle)
    return w
