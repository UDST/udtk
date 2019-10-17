
import yaml
import pickle
import json

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

import pysal as ps
from pysal.explore.esda.moran import Moran
from pysal.explore.esda.moran import Moran_Local
from pysal.viz.splot.esda import plot_moran
from pysal.viz.splot.esda import moran_scatterplot
from pysal.viz.splot.esda import lisa_cluster

from sklearn.cluster import DBSCAN


def get_lisa(path, indicator, w, grid_id):
    '''
    This function takes a year and a variable
    and returns the all the quadrants for local moran analysis
    ...
    Args:

    '''
    carto = gpd.read_file(path)

    moran = Moran(carto[indicator].values, w)
    moran_loc = Moran_Local(carto[indicator].values, w, transformation="r",
                            permutations=99)

    carto['significant'] = moran_loc.p_sim < 0.05
    carto['quadrant'] = moran_loc.q

    return {'gdf': carto,
            'moran': moran,
            'value': moran.I,
            'significance': moran.p_sim,
            'local': moran_loc}


def select_quadrant(gdf, qval, significant=True):
    '''
    This function returns...
    ...
    Args:

    '''
    quadrant = gdf.loc[(gdf['quadrant'] == qval) & (gdf['significant'] == significant)]

    list_q = list(quadrant.centroid.map(lambda g: [g.x, g.y]))
    X_q = np.array(list_q)

    return {'quadrant_gdf': quadrant,
            'quadrant_array': X_q}


def cluster_labels(eps, min_samples, quadrant_array):
    '''
    This function returns...
    ...
    Args:

    '''
    clustering_quadrant = DBSCAN(eps=eps, min_samples=min_samples).fit(quadrant_array)
    return clustering_quadrant.labels_


def make_convex_cluster(geodt, grid_id, nbour):
    '''
    This function takes a geopandas GeoDataFrame
    and creates a convex hull from not isolated poligons
    '''
    w_points = ps.lib.weights.Queen.from_dataframe(geodt, idVariable=grid_id)
    geodt['no_island'] = [sum(w_points[i].values()) >=
                          nbour for i in geodt[grid_id]]

    convex = geodt[geodt.no_island].copy()
    convex = convex.dissolve('k')
    convex.geometry = convex.convex_hull
    return convex.geometry.iloc[0]


def build_clusters(gdf, indicator, grid_id, nbour):
    '''
    This function returns...
    ...
    Args:

    '''
    # remove outliers and stores each % cell value of total indicator
    gdf = gdf.loc[gdf.k >= 0, :]
    gdf[indicator + '_p'] = gdf[indicator] / gdf[indicator].sum()

    # create a convex hull from clusters
    clusters = gdf.reindex(columns=['k', grid_id, 'geometry']).groupby('k') \
        .agg(make_convex_cluster, grid_id, nbour).drop(grid_id, axis=1)

    clusters = gpd.GeoDataFrame(clusters, geometry=clusters.geometry) \
        .reset_index()

    return {'indicator': gdf,
            'clusters': clusters}


def cluster_processing(clusters, carto, quadrant_gdf, year, indicator, cmap):
    '''
    This function returns...
    ...
    Args:
    ----
    clusters: gdf
    quadrant_gdf: gdf (with a 'k' value)

    '''
    # create points from cluster centroid
    cluster_points = clusters.copy()
    cluster_points.geometry = clusters.geometry.centroid

    # create a table with grouped data
    table_cluster = (quadrant_gdf.reindex(columns=['k', indicator + '_p'])
                     .groupby('k').sum() * 100).reset_index()

    clusters = clusters.merge(table_cluster, on='k')
    clusters = clusters.sort_values(indicator + '_p')

    # rename clusters based on aggregated data
    clusters['k_ordered'] = range(len(clusters))
    cluster_points = cluster_points.merge(table_cluster, on='k')
    cluster_points = cluster_points.sort_values(indicator + '_p')
    cluster_points['k_ordered'] = range(len(cluster_points))
    cluster_points.index = cluster_points.k_ordered

    # set cooridantes reference system and change to wgs84 latlong
    cluster_points.crs = carto.crs
    clusters.crs = carto.crs
    cluster_points = cluster_points.to_crs(epsg=4326)
    clusters = clusters.to_crs(epsg=4326)

    # create color palette
    cm = plt.get_cmap(cmap)
    colores = cm(np.linspace(0, 1, len(clusters)))
    scl = list(map(lambda x: 'rgba(%s,%s,%s,1)' % (x[0] * 255, x[1] * 255, x[2] * 255),
                   colores))
    clusters['color'] = scl
    cluster_points['text_point'] = [str(round(i, 1)) + '% of ' + indicator
                                    for i in cluster_points[indicator + '_p']]

    # add year and variable as columns to long format
    clusters['year'] = year
    clusters['indicator'] = indicator
    clusters = clusters.reindex(columns=['k_ordered', 'geometry',
                                         'year', 'indicator', indicator + '_p', 'color'])
    clusters.columns = ['k_ordered', 'geometry',
                        'year', 'indicator', 'value', 'color']
    cluster_points['year'] = year
    cluster_points['indicator'] = indicator
    cluster_points = cluster_points.reindex(columns=[
        'k_ordered', 'geometry', 'year',
        'indicator', indicator + '_p', 'text_point'])

    cluster_points.columns = ['k_ordered', 'geometry', 'year',
                              'indicator', 'value', 'text_point']
    cluster_points['color'] = scl

    return {'cluster_polygons': clusters,
            'cluster_points': cluster_points}