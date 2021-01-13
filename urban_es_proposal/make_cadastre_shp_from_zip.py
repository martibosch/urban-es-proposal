import glob
import logging
import os
import re
import shutil
import zipfile
from os import path

import click
import geopandas as gpd
import pandas as pd
import rasterio as rio
from rasterio import features, transform

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
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('dst_filepath', type=click.Path())
@click.argument('unzip_filepattern')
def main(input_filepath, dst_filepath, unzip_filepattern):
    logger = logging.getLogger(__name__)

    # unzip all zip files to temp dirs
    temp_dir = path.join(path.dirname(dst_filepath), 'temp')
    if not path.exists(temp_dir):  # and path.isdir(temp_dir):
        os.mkdir(temp_dir)
    logger.info("Created temporal directory '%s' to extract the files",
                temp_dir)

    with zipfile.ZipFile(input_filepath) as zf:
        zf.extractall(temp_dir)
    zip_filepaths = glob.glob(path.join(temp_dir, '*.zip'))
    logger.info("Extracted %d interim zips to %s", len(zip_filepaths),
                temp_dir)

    for zip_filepath in zip_filepaths:
        logger.info("Extracting files from %s matching %s", zip_filepath,
                    unzip_filepattern)
        p = re.compile(unzip_filepattern)

        with zipfile.ZipFile(zip_filepath) as zf:
            for file_info in zf.infolist():
                if p.match(file_info.filename):
                    filename = '_'.join([
                        path.splitext(path.basename(zip_filepath))[0],
                        path.basename(file_info.filename)
                    ])
                    # Trick from https://bit.ly/2KZkO9G to manipulate
                    # zipfile info and junk inner zip paths
                    file_info.filename = filename
                    zf.extract(file_info, temp_dir)

    shp_filepaths = glob.glob(path.join(temp_dir, '*.shp'), recursive=True)
    logger.info("Assembling single data frame from files: %s",
                ', '.join(shp_filepaths))
    # process 'divers' filepaths later so that the other (more specific)
    # LULC shapefiles take priority
    divers_filepaths = [
        divers_filepath for divers_filepath in shp_filepaths
        if divers_filepath.endswith('_CSDIV_S.shp')
    ]
    other_filepaths = [
        other_filepath for other_filepath in shp_filepaths
        if not other_filepath.endswith('_CSDIV_S.shp')
    ]
    # Based on https://bit.ly/2znOaIh
    cadastre_gdf = pd.concat([
        gpd.read_file(shp_filepath)
        for shp_filepath in divers_filepaths + other_filepaths
    ],
                             sort=False).pipe(gpd.GeoDataFrame)
    cadastre_gdf.crs = gpd.read_file(shp_filepaths[0]).crs
    shutil.rmtree(temp_dir)
    logger.info("deleted temporal directory '%s'", temp_dir)

    # rasterize the cadastre
    cadastre_gdf.to_file(dst_filepath)
    logger.info("dumped cadastre shapefile to %s", dst_filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=settings.DEFAULT_LOG_FMT)

    main()
