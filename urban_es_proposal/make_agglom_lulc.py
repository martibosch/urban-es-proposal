import logging

import click
import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio import features, transform, windows

from urban_es_proposal import settings

LAUSANNE_LULC_FILE_REGEX_PATTERN = "Cadastre/(NPCS|MOVD)_CAD_TPR_(BATHS|" \
                           "CSBOIS|CSDIV|CSDUR|CSEAU|CSVERT)_S.*"

# ugly hardcoded values extracted from the Swiss GMB agglomeration boundaries
WEST, SOUTH, EAST, NORTH = (2512518, 1146825, 2558887, 1177123)

# ugly hardcoded CRS to avoid issues with pyproj versions
CRS = 'epsg:2056'

# lulc column in Vaud's cadastre shapefile
CADASTRE_LULC_COLUMN = 'GENRE'


def _lausanne_reclassify(value, dst_nodata):
    if value < 0:
        return dst_nodata
    if value >= 9:
        return value - 1
    else:
        return value


def rasterize_cadastre(cadastre_gdf, dst_res, dst_nodata, dst_dtype):
    cadastre_ser = cadastre_gdf[CADASTRE_LULC_COLUMN].apply(
        _lausanne_reclassify, args=(dst_nodata, ))
    cadastre_transform = transform.from_origin(WEST + dst_res // 2,
                                               NORTH - dst_res // 2, dst_res,
                                               dst_res)
    cadastre_shape = ((NORTH - SOUTH) // dst_res, (EAST - WEST) // dst_res)
    cadastre_arr = features.rasterize(
        ((geom, value)
         for geom, value in zip(cadastre_gdf['geometry'], cadastre_ser)),
        out_shape=cadastre_shape,
        fill=dst_nodata,
        transform=cadastre_transform,
        dtype=dst_dtype)

    return cadastre_arr, cadastre_transform


@click.command()
@click.argument('cadastre_shp_filepath', type=click.Path(exists=True))
@click.argument('agglom_extent_filepath', type=click.Path(exists=True))
@click.argument('dst_filepath', type=click.Path())
@click.option('--dst-res', type=int, default=10, required=False)
@click.option('--dst-nodata', type=int, default=255, required=False)
@click.option('--dst-dtype', default='uint8', required=False)
def main(cadastre_shp_filepath, agglom_extent_filepath, dst_filepath, dst_res,
         dst_nodata, dst_dtype):
    logger = logging.getLogger(__name__)

    cadastre_gdf = gpd.read_file(cadastre_shp_filepath,
                                 bbox=(WEST, SOUTH, EAST, NORTH))

    # rasterize the cadastre
    cadastre_arr, cadastre_transform = rasterize_cadastre(
        cadastre_gdf, dst_res, dst_nodata, dst_dtype)
    logger.info("rasterized cadastre vector LULC dataset to shape %s",
                str(cadastre_arr.shape))

    # TODO; crop it to the extent
    agglom_extent_geom_nodata = 0
    agglom_extent_geom = gpd.read_file(
        agglom_extent_filepath)['geometry'].iloc[:1]
    agglom_extent_mask = features.rasterize(agglom_extent_geom,
                                            out_shape=cadastre_arr.shape,
                                            fill=agglom_extent_geom_nodata,
                                            transform=cadastre_transform)
    # get window and transform of valid data points, i.e., the computed extent
    extent_window = windows.get_data_window(agglom_extent_mask,
                                            nodata=agglom_extent_geom_nodata)
    extent_transform = windows.transform(extent_window, cadastre_transform)
    dst_arr = np.where(agglom_extent_mask, cadastre_arr,
                       dst_nodata)[windows.window_index(extent_window)]
    # dump it
    with rio.open(
            dst_filepath,
            'w',
            driver='GTiff',
            width=extent_window.width,
            height=extent_window.height,
            count=1,
            crs=CRS,  # cadastre_gdf.crs
            transform=extent_transform,
            dtype=dst_dtype,
            nodata=dst_nodata) as dst:
        dst.write(dst_arr, 1)
    logger.info("dumped rasterized dataset to %s", dst_filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=settings.DEFAULT_LOG_FMT)

    main()
