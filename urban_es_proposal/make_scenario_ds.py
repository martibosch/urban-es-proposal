import json
import logging
import tempfile
import warnings
from os import path

import click
import dask
import invest_ucm_calibration as iuc
import numpy as np
import pandas as pd
import pygeoprocessing
import rasterio as rio
import xarray as xr
from dask import diagnostics
from lausanne_greening_scenarios.scenarios import utils as scenario_utils
from rasterio import transform

from urban_es_proposal import settings


class ScenarioGenerator(scenario_utils.ScenarioGenerator):
    def generate_lulc_arr(self, change_num, priority_arr=None):
        if change_num == 0:
            return self.lulc_arr.copy()
        elif change_num >= len(self.change_df):
            pixels_to_change_df = self.change_df
        else:
            if priority_arr is not None:
                # prioritize the pixels according to the raster values
                pixels_to_change_df = self.change_df.loc[self.change_df.index[
                    priority_arr.flatten()[
                        self.change_df.index].argsort()[::-1]]][:change_num]
            else:
                pixels_to_change_df = self.change_df.sample(n=change_num)
        # now build the new LULC array and change the pixels
        new_lulc_arr = self.lulc_arr.copy()
        for next_code, next_code_df in pixels_to_change_df.groupby(
                'next_code'):
            new_lulc_arr.ravel()[next_code_df.index] = next_code

        return new_lulc_arr

    def generate_scenario_lulc_da(self,
                                  change_nums,
                                  scenario_runs=None,
                                  priority_arr=None):

        # prepare the xarray data array
        coords = {'change_num': change_nums, **self.coords}
        dims = ['change_num']
        dst_dtype = self.lulc_meta['dtype']
        if scenario_runs is not None:
            coords['scenario_run'] = scenario_runs
            dims += ['scenario_run']
        dims += ['y', 'x']
        scenario_lulc_da = xr.DataArray(
            dims=dims,
            coords=coords,
            attrs=dict(nodata=int(self.lulc_meta['nodata']),
                       pyproj_srs=f'epsg:{self.lulc_meta["crs"].to_epsg()}'))

        def _repeat(arr):
            if scenario_runs is not None:
                arr = np.array([arr for scenario_run in scenario_runs],
                               dtype=dst_dtype)
            return arr

        # generate the arrays
        if change_nums[0] == 0:
            scenario_lulc_da.loc[dict(change_num=0)] = _repeat(self.lulc_arr)
            change_nums = change_nums[1:]

        if scenario_runs is not None:
            data = [[
                self.generate_lulc_arr(change_num, priority_arr=priority_arr)
                for scenario_run in scenario_runs
            ] for change_num in change_nums]
        else:
            data = [
                self.generate_lulc_arr(change_num, priority_arr=priority_arr)
                for change_num in change_nums
            ]
        scenario_lulc_da.loc[dict(change_num=change_nums)] = np.array(
            data, dtype=dst_dtype)

        # return the data array
        return scenario_lulc_da.astype(dst_dtype)


def simulate_scenario_t_da(scenario_lulc_da,
                           biophysical_table_filepath,
                           ref_et_raster_filepath,
                           t_ref,
                           uhi_max,
                           ucm_params,
                           dst_t_dtype='float32',
                           rio_meta=None,
                           cc_method='factors'):
    if rio_meta is None:
        x = scenario_lulc_da['x'].values
        y = scenario_lulc_da['y'].values
        west = x[0]
        north = y[0]
        # TODO: does the method to get the transform work for all grids, i.e.,
        # regardless of whether the origin is in the upper left or lower left?
        rio_meta = dict(driver='GTiff',
                        dtype=scenario_lulc_da.dtype,
                        nodata=scenario_lulc_da.attrs['nodata'],
                        width=len(x),
                        height=len(y),
                        count=1,
                        crs=scenario_lulc_da.attrs['pyproj_srs'],
                        transform=transform.from_origin(
                            west, north, x[1] - west, north - y[1]))

    # define the function here so that the fixed arguments are curried
    def _t_from_lulc(lulc_arr):
        with tempfile.TemporaryDirectory() as tmp_dir:
            lulc_raster_filepath = path.join(tmp_dir, 'lulc.tif')
            with rio.open(lulc_raster_filepath, 'w', **rio_meta) as dst:
                dst.write(lulc_arr, 1)
            ucm_wrapper = iuc.UCMWrapper(lulc_raster_filepath,
                                         biophysical_table_filepath,
                                         cc_method,
                                         ref_et_raster_filepath,
                                         t_ref,
                                         uhi_max,
                                         extra_ucm_args=ucm_params,
                                         workspace_dir=tmp_dir)
            return ucm_wrapper.predict_t_arr(0)

    scenario_t_da = xr.DataArray(
        dims=scenario_lulc_da.dims,
        coords=scenario_lulc_da.coords,
        attrs=dict(nodata=np.nan,
                   pyproj_srs=scenario_lulc_da.attrs['pyproj_srs']))

    change_nums = scenario_t_da['change_num'].values
    scenario_runs = scenario_t_da.coords.get('scenario_run', None)

    def _simulate_and_repeat(change_num):
        # simulate once and repeat it for all scenario runs
        lulc_da = scenario_lulc_da.sel(change_num=change_num)
        if scenario_runs is not None:
            t_arr = _t_from_lulc(lulc_da.isel(scenario_run=0))
            t_arr = np.array(
                [t_arr for scenario_run in scenario_t_da['scenario_run']],
                dtype=dst_t_dtype)
        else:
            t_arr = _t_from_lulc(lulc_da)
        return t_arr

    if change_nums[0] == 0:
        scenario_t_da.loc[dict(change_num=0)] = _simulate_and_repeat(0)
        change_nums = change_nums[1:]

    scenario_dims = scenario_lulc_da.dims[:-2]
    stacked_da = scenario_lulc_da.sel(change_num=change_nums).stack(
        scenario=scenario_dims).transpose('scenario', 'y', 'x')
    with diagnostics.ProgressBar():
        scenario_t_da.loc[dict(change_num=change_nums)] = xr.DataArray(
            np.array(
                dask.compute(*[
                    dask.delayed(_t_from_lulc)(_scenario_lulc_da)
                    for _scenario_lulc_da in stacked_da
                ],
                             scheduler='processes')).astype(dst_t_dtype),
            dims=stacked_da.dims,
            coords={dim: stacked_da.coords[dim]
                    for dim in stacked_da.dims},
            attrs=dict(dtype=dst_t_dtype)).unstack(dim='scenario').transpose(
                *scenario_dims, 'y', 'x')
    # replace nodata values - UCM/InVEST uses minus infinity, so we can use
    # temperatures lower than the absolute zero as a reference threshold which
    # (physically) makes sense
    return scenario_t_da.where(scenario_t_da > -273.15, np.nan)


@click.command()
@click.argument('lulc_raster_filepath', type=click.Path(exists=True))
@click.argument('biophysical_table_filepath', type=click.Path(exists=True))
@click.argument('ref_et_raster_filepath', type=click.Path(exists=True))
@click.argument('station_t_filepath', type=click.Path(exists=True))
@click.argument('calibrated_params_filepath', type=click.Path(exists=True))
@click.argument('dst_filepath', type=click.Path())
@click.option('--change-num-step', default=5000, required=False)
@click.option('--change-num-min', default=0, required=False)
@click.option('--change-num-max', default=100000, required=False)
@click.option('--vulnerable-pop-filepath',
              type=click.Path(exists=True),
              required=False)
@click.option('--num-scenario-runs', type=int, required=False)
def main(lulc_raster_filepath, biophysical_table_filepath,
         ref_et_raster_filepath, station_t_filepath,
         calibrated_params_filepath, dst_filepath, change_num_step,
         change_num_min, change_num_max, vulnerable_pop_filepath,
         num_scenario_runs):
    logger = logging.getLogger(__name__)
    # disable InVEST's logging
    for module in ('natcap.invest.urban_cooling_model', 'natcap.invest.utils',
                   'pygeoprocessing.geoprocessing'):
        logging.getLogger(module).setLevel(logging.WARNING)
    # ignore all warnings
    warnings.filterwarnings('ignore')

    # 1. align the rasters
    # # TODO: use a dummy call to the UCM to avoid copy-pasting their code?
    # base_raster_filepaths = [lulc_raster_filepath, ref_et_raster_filepath]
    # target_raster_filepaths = [
    #     path.join(tmp_dir, path.basename(base_raster_filepath))
    #     for base_raster_filepath in base_raster_filepaths
    # ]
    # resample_methods = ['mode', 'cubicspline']
    # if vulnerable_pop_filepath:
    #     base_raster_filepaths += [vulnerable_pop_filepath]
    #     target_raster_filepaths += [
    #         path.join(tmp_dir, path.basename(vulnerable_pop_filepath))
    #     ]
    #     resample_methods += ['bilinear']
    # with rio.open(lulc_raster_filepath) as src:
    #     pygeoprocessing.align_and_resize_raster_stack(
    #         base_raster_filepaths, target_raster_filepaths,
    #         resample_methods, src.res, 'intersection')
    # logger.info("aligned rasters %s to %s",
    #             ' '.join(base_raster_filepaths),
    #             ' '.join(target_raster_filepaths))

    # 1. read inputs
    # 1.1. get the ref. temperature and magnitude of the UHI effect
    station_t_df = pd.read_csv(station_t_filepath, index_col=0)
    t_ref = station_t_df.min()
    uhi_max = station_t_df.max() - t_ref

    # 1.2. read the calibrated parameters
    with open(calibrated_params_filepath) as src:
        ucm_params = json.load(src)

    # 2. generate scenarios
    change_nums = np.arange(change_num_min, change_num_max + change_num_step,
                            change_num_step)
    sg = ScenarioGenerator(lulc_raster_filepath, biophysical_table_filepath)
    kws = {}
    if vulnerable_pop_filepath:
        with rio.open(vulnerable_pop_filepath) as src:
            kws['priority_arr'] = src.read(1)
    else:
        kws['scenario_runs'] = np.arange(num_scenario_runs)

    scenario_lulc_da = sg.generate_scenario_lulc_da(change_nums, **kws)
    logger.info("simulated LULC raster for %d scenarios",
                np.prod(scenario_lulc_da.shape[:-2]))

    scenario_t_da = simulate_scenario_t_da(scenario_lulc_da,
                                           biophysical_table_filepath,
                                           ref_et_raster_filepath, t_ref,
                                           uhi_max, ucm_params)
    logger.info("simulated temperature for each scenario")

    xr.Dataset({
        'lulc': scenario_lulc_da,
        'T': scenario_t_da
    }).to_netcdf(dst_filepath)
    logger.info("dumped scenario dataset to %s", dst_filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=settings.DEFAULT_LOG_FMT)

    main()
