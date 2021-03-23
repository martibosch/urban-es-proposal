import logging

import click
import geopandas as gpd
import swisslandstats as sls

from urban_es_proposal import settings

VULNERABLE_COLUMNS = [
    f'B19B{sex}{age_group:02}' for sex in ['M', 'W']
    for age_group in range(13, 20)
]


# utils for the CLI
class OptionEatAll(click.Option):
    # Option that can take an unlimided number of arguments
    # Copied from Stephen Rauch's answer in stack overflow.
    # https://bit.ly/2kstLhe
    def __init__(self, *args, **kwargs):
        self.save_other_options = kwargs.pop('save_other_options', True)
        nargs = kwargs.pop('nargs', -1)
        assert nargs == -1, 'nargs, if set, must be -1 not {}'.format(nargs)
        super(OptionEatAll, self).__init__(*args, **kwargs)
        self._previous_parser_process = None
        self._eat_all_parser = None

    def add_to_parser(self, parser, ctx):
        def parser_process(value, state):
            # method to hook to the parser.process
            done = False
            value = [value]
            if self.save_other_options:
                # grab everything up to the next option
                while state.rargs and not done:
                    for prefix in self._eat_all_parser.prefixes:
                        if state.rargs[0].startswith(prefix):
                            done = True
                    if not done:
                        value.append(state.rargs.pop(0))
            else:
                # grab everything remaining
                value += state.rargs
                state.rargs[:] = []
            value = tuple(value)

            # call the actual process
            self._previous_parser_process(value, state)

        retval = super(OptionEatAll, self).add_to_parser(parser, ctx)
        for name in self.opts:
            our_parser = parser._long_opt.get(name) or parser._short_opt.get(
                name)
            if our_parser:
                self._eat_all_parser = our_parser
                self._previous_parser_process = our_parser.process
                our_parser.process = parser_process
                break
        return retval


@click.command()
@click.argument('statpop_filepath', type=click.Path(exists=True))
@click.argument('agglom_extent_filepath', type=click.Path(exists=True))
@click.argument('dst_filepath', type=click.Path())
@click.option('--vulnerable-columns', cls=OptionEatAll, required=False)
@click.option('--buffer-dist', default=100, required=False)
def main(statpop_filepath, agglom_extent_filepath, dst_filepath,
         vulnerable_columns, buffer_dist):
    logger = logging.getLogger(__name__)

    gdf = gpd.read_file(agglom_extent_filepath)
    ldf = sls.read_csv(statpop_filepath,
                       x_column='E_KOORD',
                       y_column='N_KOORD').clip_by_geometry(
                           gdf['geometry'].iloc[0].buffer(buffer_dist),
                           gdf.crs)

    if vulnerable_columns is None:
        vulnerable_columns = VULNERABLE_COLUMNS
    ldf['vulnerable'] = ldf[vulnerable_columns].sum(axis=1)

    ldf.to_geotiff(dst_filepath, 'vulnerable')
    logger.info("dumped vulnerable population raster to %s", dst_filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=settings.DEFAULT_LOG_FMT)

    main()
