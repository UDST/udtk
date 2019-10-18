import contextily as ctx
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

import geopandas as gpd
import json
import plotly.graph_objects as go


def add_basemap(ax, zoom, url='http://tile.stamen.com/terrain/tileZ/tileX/tileY.png'):
    xmin, xmax, ymin, ymax = ax.axis('equal')
    basemap, extent = ctx.bounds2img(xmin, ymin, xmax, ymax, zoom=zoom, url=url)
    ax.imshow(basemap, extent=extent, interpolation='bilinear')
    # restore original x/y limits
    ax.axis((xmin, xmax, ymin, ymax))


def plot_h3_gdf(h3_gdf, plot_column, scheme, k):
    f, ax = plt.subplots(figsize=(8, 8))
    h3_gdf.to_crs(epsg=3857).plot(ax=ax, column=plot_column, scheme=scheme, k=k)
    add_basemap(ax, zoom=12, url=ctx.sources.ST_TONER_LITE)
    ax.set_axis_off()


def plotly_choropleth(gdf, plot_column, zmax=3000):
    grid_geojson = json.loads(gdf.to_json())
    fig = go.Figure(go.Choroplethmapbox(geojson=grid_geojson, locations=gdf.index, z=gdf[plot_column],
                                        colorscale="Viridis", zmin=0, zmax=zmax,
                                        marker_opacity=0.5, marker_line_width=0))
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=10,
                      mapbox_center={"lat": 40.7731607, "lon": -73.9752436})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


def plotly_lisa(gdf):
    colors5_mpl = {'HH': '#d7191c',
                   'LL': '#2c7bb6',
                   'LH': '#abd9e9',
                   'HL': '#fdae61',
                   'Non-significant': 'lightgrey'}
    geoj = json.loads(gdf.loc[gdf.lisa_cluster != 'Non-significant', :].copy().to_json())
    sources = [{"type": "FeatureCollection", 'features': [feat]}
               for feat in geoj['features']]
    fig = go.Figure(go.Scattermapbox(
        mode="markers",
        lon=[-73.9752436], lat=[40.7731607],
        marker={'size': 1, 'color': ["black"]})
    )
    layers = [dict(sourcetype='geojson',
                   source=sources[i],
                   below="water",
                   type='fill',
                   color=colors5_mpl[sources[i]['features'][0]['properties']['lisa_cluster']],
                   opacity=0.8
                   ) for i in range(len(sources))]
    fig.update_layout(
        mapbox={
            'style': "carto-positron",
            'center': {'lon': -73.9752436, 'lat': 40.7731607},
            'zoom': 10, 'layers': layers},
        margin={'l': 0, 'r': 0, 'b': 0, 't': 0})
    # fig.show()
    return fig


def plot_lisa(gdf):
    colors5_mpl = {'HH': '#d7191c',
                   'LL': '#2c7bb6',
                   'LH': '#abd9e9',
                   'HL': '#fdae61',
                   'Non-significant': 'lightgrey'}
    gdf = gdf.loc[gdf.lisa_cluster != 'Non-significant', :]
    unique_cluster = gdf.lisa_cluster.unique()
    unique_cluster.sort()
    hmap = ListedColormap([colors5_mpl[i] for i in unique_cluster])
    f, ax = plt.subplots(figsize=(8, 8))

    gdf.to_crs(epsg=3857).plot(ax=ax, column='lisa_cluster', legend=True, categorical=True,
                               k=2, cmap=hmap, linewidth=0.1,
                               edgecolor='white')
    add_basemap(ax, zoom=12, url=ctx.sources.ST_TONER_LITE)
    ax.set_axis_off()
