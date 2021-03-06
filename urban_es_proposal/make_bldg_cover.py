import logging

import click
import geopandas as gpd
import numpy as np
import rasterio as rio
from rasterio import features, transform
from skimage.util import shape

from urban_es_proposal import settings


@click.command()
@click.argument('agglom_lulc_filepath', type=click.Path(exists=True))
@click.argument('cadastre_filepath', type=click.Path(exists=True))
@click.argument('dst_filepath', type=click.Path())
@click.option('--bldg-res', default=1, required=False)
@click.option('--dst-dtype', default=None, required=False)
def main(agglom_lulc_filepath, cadastre_filepath, dst_filepath, bldg_res,
         dst_dtype):
    logger = logging.getLogger(__name__)

    # read the agglomeration extract raster
    with rio.open(agglom_lulc_filepath) as src:
        agglom_mask = src.dataset_mask()
        xres, yres = src.res
        height, width = src.shape
        west, south, east, north = src.bounds
        meta = src.meta
        nodata = src.nodata

    # get a binary layer of building pixels at 1m resolution by rasterizing
    # the cadastre
    _xres, _yres = bldg_res, bldg_res
    _west = west - (xres / 2 - _xres / 2)
    _north = north + (yres / 2 - _yres / 2)
    gdf = gpd.read_file(cadastre_filepath,
                        bbox=(_west, south - yres, east + xres, _north))
    xfactor, yfactor = int(xres // _xres), int(yres // _yres)
    bldg_shape = (height * yfactor, width * xfactor)
    bldg_transform = transform.from_origin(_west, _north, _xres, _yres)
    bldg_gser = gdf[gdf['GENRE'] == 0]['geometry']
    bldg_arr = features.rasterize(((geom, 1) for geom in bldg_gser),
                                  out_shape=bldg_shape,
                                  fill=0,
                                  transform=bldg_transform,
                                  dtype=rio.uint8)
    logger.info("rasterized cadastre from %s to shape %s and resolution %s",
                cadastre_filepath, bldg_shape, (_xres, _yres))

    # get the percentage of building cover of each pixel https://bit.ly/2oxiQ80
    block_size = xfactor * yfactor
    block_arr = shape.view_as_blocks(bldg_arr, block_shape=(yfactor, xfactor))
    bldg_cover_arr = np.sum(block_arr.reshape(block_arr.shape[0],
                                              block_arr.shape[1], -1),
                            axis=2) / block_size
    logger.info("extracted per-pixel proportion of building cover")

    # dump the building cover raster
    if dst_dtype is None:
        dst_dtype = bldg_cover_arr.dtype
    meta.update(dtype=dst_dtype)
    with rio.open(dst_filepath, 'w', **meta) as dst:
        dst.write(np.where(agglom_mask, bldg_cover_arr, nodata), 1)

    logger.info(
        "dumped raster of per-pixel proportion of building cover to %s",
        dst_filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=settings.DEFAULT_LOG_FMT)

    main()
