import phases
import base
import httpserver
from time import sleep
from argparse import ArgumentParser
import os
from socket import gethostbyname, gethostname
try:
    import xmldict
except ModuleNotFoundError:
    import pip
    pip.main(['install', 'xmldict'])
finally:
    import xmldict
try:
    import better_exceptions
except ModuleNotFoundError as e:
    pass

_phases = [
    "Program Initialization",
    "Data Collection and Processing",
    "Template Collection and Processing",
    "Indexing",
    "File Pre-Processing",
    "File Processing",
    "File Post-Processing"
]

_directories = {
    "data": "_data",
    "plugins": "_plugins",
    "templates": "_templates",
    "src": "src",
    "output": "_site",
    "s3g": "_s3g",
    "default_modules": "_s3g/modules",
    "error": "errors"
}


def load_plugins(**kwargs):
    phases.prepare_new_build(**kwargs)
    kwargs['logger'].info('Loading Plugins')
    plugin_manager = phases.load_plugins(**kwargs)
    return plugin_manager


def build_site(logger, plugin_manager, args):
    phases.prepare_new_build(logger=logger, directories=_directories)
    logger.info('Starting Data Collection')
    data_manager = phases.collect_data(logger=logger, directories=_directories, plugins=plugin_manager)
    logger.info('Starting Template Collection')
    templates_manager = phases.collect_templates(logger=logger, directories=_directories, plugins=plugin_manager)
    logger.info('Indexing Site')
    indexed = phases.index_site(logger=logger, directories=_directories, plugins=plugin_manager)
    logger.info('Processing Pages')
    processed = phases.process_files(logger=logger, args=args, directories=_directories, files=indexed, templates=templates_manager, data=data_manager, plugins=plugin_manager)
    logger.info('Saving Files')
    phases.save_site(logger=logger, directories=_directories, files=processed, plugins=plugin_manager)


def main(args):
    os.chdir(args['working-directory'])
    logger = base.get_logger(__name__, args['log-level'])
    build_site(logger, load_plugins(logger=logger, directories=_directories), args)

    def server_watchdog_callback():
        build_site(logger, load_plugins(logger=logger, directories=_directories), args)

    server_callback = None
    if args['server-refresh'] == 'true':
        server_callback = server_watchdog_callback

    if args['server'] == 'true':
        server_thread, addr = httpserver.start_server(_directories['output'], 'localhost', 8000, server_callback, (_directories['src'], _directories['data'], _directories['templates'], _directories['plugins']))
        logger.info(f'Started server at {addr[0]}:{str(addr[1])}')

        try:
            while server_thread.is_alive():
                sleep(1)
        except KeyboardInterrupt:
            logger.debug('KeyboardInterrupt received')

    logger.info('Finished')


if __name__ == '__main__':
    default_args = {
        "log-level": "INFO",
        "iter-limit": 60,
        "server": "true",
        "server-port": "8000",
        "server-refresh": "true",
        "working-directory": "../",
        "server-ip": str(gethostbyname(gethostname()))
    }
    argparser = ArgumentParser()
    for key in default_args:
        argparser.add_argument(f'--{key}', default=default_args[key])
    parsed = argparser.parse_args().__dict__
    args = dict()
    for val in parsed:
        args[val.replace('_', '-')] = parsed[val]
    main(args)