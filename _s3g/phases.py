from base import *
from shutil import copy as shutil_copy_file
from shutil import rmtree
import os


def load_plugins(**kwargs) -> PluginManager:
    logger = kwargs['logger']
    directorylist = kwargs['directories']
    plugin_manager = PluginManager(5)

    for directory in ["./_s3g/modules", directorylist['plugins']]:
        plugin_manager.add_plugin(PluginLoader.load_directory(directory, logger))

    return plugin_manager


def prepare_new_build(**kwargs) -> None:

    if os.path.exists(kwargs['directories']['output']):
        try:
            rmtree(kwargs['directories']['output'])
        except PermissionError:
            kwargs['logger'].error(f"PermissionError deleting \"{kwargs['directories']['output']}\"")
        else:
            kwargs['logger'].debug(f"Removed \"{kwargs['directories']['output']}\"")

    for d in kwargs['directories']:
        if not os.path.exists(kwargs['directories'][d]):
            os.makedirs(kwargs['directories'][d])


def collect_data(**kwargs) -> DataManager:
    data_list = list()
    directories, logger, plugin_manager = kwargs['directories'], kwargs['logger'], kwargs['plugins']

    for root, subdirs, files in os.walk(directories['data']):
        for file in files:
            data = PreProcessedData()
            name = root.split(os.sep)
            name.pop(0)  # Get rid of directories['data']
            name.append(os.path.splitext(file)[0])
            name = '.'.join(name)
            data.name = name
            data.path = os.path.join(root, file)
            data.ext = os.path.splitext(file)[1]
            with open(data.path) as f:
                data.text = f.read()
            data_list.append(data)

    logger.info(f"Read data from \"{directories['data']}\"")

    data_manager = DataManager(logger)

    for x in range(len(data_list)):
        for plugin in plugin_manager.get_plugins(1):
            pre = data_list[x]
            data_list[x] = plugin.process(data_list[x])
            if data_list[x] is None:
                data_list[x] = pre
                logger.warning(f'{plugin.name} returned None so it was ignored')
        path = data_list[x].name.split('.')
        if not isinstance(path, list):
            path = [path]
        data_manager.add_data(path, data_list[x].data)

    return data_manager


def collect_templates(**kwargs) -> SectionManager:
    directories, logger, plugin_manager = kwargs['directories'], kwargs['logger'], kwargs['plugins']
    sections = list()

    for root, subdirs, files in os.walk(directories['templates']):
        for file in files:
            sect = Section()
            name = root.split(os.sep)
            name.pop(0)  # Get rid of _directories['templates']
            name.append(os.path.splitext(file)[0])
            name = '.'.join(name)
            sect.name = name
            sect.path = os.path.join(root, file)
            sect.ext = os.path.splitext(file)[1]
            with open(sect.path) as f:
                sect.text = f.read()
            sections.append(sect)

    section_manager = SectionManager()

    for x in range(len(sections)):
        pre = sections[x]
        for plugin in plugin_manager.get_plugins(2):
            pre = plugin.process(pre)
        if pre is None:
            logger.warning(f'"{sections[x].name}" was None so it was ignored')
        elif not pre.processed:
            logger.warning(f'"{pre.name}" was not processed by any plugins')
        else:
            section_manager.add_section(pre)

    return section_manager


def index_site(**kwargs) -> list:
    directories, logger, plugin_manager = kwargs['directories'], kwargs['logger'], kwargs['plugins']
    page_data_list = list()

    for root, subdirs, files in os.walk(directories['src']):
        for file in files:
            ftp = PageData()
            name = root.split(os.sep)
            name.pop(0)  # Get rid of _directories['src']
            name.append(os.path.splitext(file)[0])
            name = '.'.join(name)
            ftp.name = name
            ftp.path = os.path.join(root, file)
            ftp.ext = os.path.splitext(file)[1]
            page_data_list.append(ftp)

    processed_page_data = list()
    to_process = 0

    for x in range(len(page_data_list)):
        pre = page_data_list[x]
        for plugin in plugin_manager.get_plugins(3):
            pre = plugin.process(pre)
        if pre is None:
            logger.warning(f'"{page_data_list[x].name}" was None so it was ignored')
        else:
            processed_page_data.append(pre)
        if not pre.processed:  # Page is copied anyway
            logger.warning(f'"{pre.name}{pre.ext}" was not not read by any plugins')
        if pre.needs_processing:
            to_process += 1

    logger.info(f'Marked {str(to_process)}/{str(len(processed_page_data))} pages to be processed')
    logger.info('Finished indexing site')

    return processed_page_data


def process_files(**kwargs) -> list:
    directories, logger, plugin_manager = kwargs['directories'], kwargs['logger'], kwargs['plugins']
    processed_page_data, section_manager, iter_limit = kwargs['files'], kwargs['templates'], kwargs['args']['iter-limit']
    DATA = kwargs['data']

    logger.info('Building Page Objects')
    pages = list()
    for item in processed_page_data:
        if not item.copy:
            continue
        p = Page()
        p.ext = item.ext
        p.name = item.name
        p.path = item.path
        p.needs_processing = item.needs_processing
        p.section_manager = section_manager
        if p.needs_processing:
            with open(p.path) as f:
                p.text = f.read()
            p.data = DATA
        pages.append(p)

    logger.info('Processing Files')

    processed_pages = [pages, list(), list(), list()]

    for x in range(len(processed_pages) - 1):
        iteration_count = 0
        error_count = 1
        for page in processed_pages[x]:
            if not page.needs_processing:
                processed_pages[x + 1].append(page)
                continue
            while True:
                iteration_count += 1
                was_processed = False
                for plugin in plugin_manager.get_plugins(4 + x):
                    safe_text = page.text
                    try:
                        page = plugin.process(page)
                    except Exception as e:
                        logger.warning(f'Error while processing file with {str(plugin.name)}')
                        logger.warning(e)
                        f = open(f'{directories["error"]}/error-{str(error_count)}.txt', "w+")
                        f.write(safe_text)
                        f.close()
                        error_count += 1
                    if page.was_processed:
                        logger.debug(f'"{plugin.name}" processed "{page.path}"')
                        page.was_processed = False
                        was_processed = True
                if iteration_count > iter_limit:
                    logger.warning(
                        f'Iteration limit reached while processing "{os.path.relpath(page.path, directories["src"])}"')
                    break
                if not was_processed:
                    break
            processed_pages[x + 1].append(page)

    return processed_pages[3]


def save_site(**kwargs) -> None:
    processed_pages, directories, logger = kwargs['files'], kwargs['directories'], kwargs['logger']

    for page in processed_pages:

        if not page.out_path:
            page.out_path = os.path.join(directories['output'], os.path.relpath(page.path, directories['src']))

        if not os.path.exists(os.path.split(page.out_path)[0]):
            os.makedirs(os.path.split(page.out_path)[0])

        if page.needs_processing:
            f = open(page.out_path, "w+")
            f.write(page.text)
            f.close()
            logger.debug(f'Saved {page.name} to {page.out_path}')
        else:
            shutil_copy_file(
                os.path.abspath(page.path),
                os.path.join(page.out_path)
            )
            logger.debug(f'Copied {page.name} to {page.out_path}')
    logger.info('Finished Saving Pages')