import contextily as ctx
import matplotlib.pyplot as plt
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


def plotly_viz(gdf, plot_column, zmax=3000):
    grid_geojson = json.loads(gdf.to_json())
    fig = go.Figure(go.Choroplethmapbox(geojson=grid_geojson, locations=gdf.index, z=gdf[plot_column],
                                        colorscale="Viridis", zmin=0, zmax=zmax,
                                        marker_opacity=0.5, marker_line_width=0))
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_zoom=10,
                      mapbox_center={"lat": 40.7731607, "lon": -73.9752436})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig
