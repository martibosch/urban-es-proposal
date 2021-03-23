import logging

import click
import numpy as np
import rasterio as rio
import swiss_uhi_utils as suhi

from urban_es_proposal import settings

ORIG_LULC_CODES = [
    0,  # building
    1,  # road
    2,  # sidewalk
    3,  # traffic island
    7,  # other impervious
    11,  # garden
]


@click.command()
@click.argument('lulc_filepath', type=click.Path(exists=True))
@click.argument('biophysical_table_filepath', type=click.Path(exists=True))
@click.argument('dst_filepath', type=click.Path())
@click.option('--shade-threshold', default=0.75)
@click.option('--dst-dtype', default='uint8')
def main(lulc_filepath, biophysical_table_filepath, dst_filepath,
         shade_threshold, dst_dtype):
    logger = logging.getLogger(__name__)

    sg = suhi.ScenarioGenerator(lulc_filepath,
                                biophysical_table_filepath,
                                orig_lulc_codes=ORIG_LULC_CODES)
    shape = sg.lulc_arr.shape
    arr = np.zeros(shape, dtype=dst_dtype)
    arr[np.unravel_index(
        sg.get_candidate_pixels_df(shade_threshold, 1).index, shape)] = 1

    dst_meta = sg.lulc_meta.copy()
    dst_meta.update(dtype=dst_dtype)
    with rio.open(dst_filepath, 'w', **dst_meta) as dst:
        dst.write(arr, 1)
    logger.info("dumped candidate pixel raster to %s", dst_filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=settings.DEFAULT_LOG_FMT)

    main()
