import contextily as ctx
import matplotlib.pyplot as plt


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
