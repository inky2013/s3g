import importlib.machinery
import logging
import collections
import types
import os
import re

class Page:
    def __init__(self):
        self.name = str()                             # Name of file (without extension)
        self.text = str()                             # File contents
        self.requirements = dict(head=[], footer=[])  # Requirements for <head> and at end of <body> (Requirement Class)
        self.data = object()                          # Data available to the current file
        self.path = str()                             # Path to file
        self.ext = str()                              # File extension
        self.was_processed = True                     # Set to false when processing is complete
        self.needs_processing = bool()                # Should the file be processed or copied
        self.out_path = None                          # If set the file will be saved here instead
        self.section_manager = None                   # Section Manager to get the sections/templates from

class PageData:
    def __init__(self):
        self.ext = str()                 # File extension
        self.path = str()                # Path to file
        self.size = int()                # Size in bytes
        self.processed = False           # If any plugin has processed the page
        self.needs_processing = False    # Should the file be processed or copied
        self.copy = True                 # Should the page be copied into the site


class PreProcessedData:
    def __init__(self):
        self.name = str()  # Base Name
        self.ext = str()  # File extension
        self.text = str()  # File Contents
        self.data = dict()  # Stores Data
        self.processed = False  # Has the file been fully processed

    def __str__(self):
        return f'PreProcessedData: {str(self.data)}'


class DataManager:
    def __init__(self, logger, data=None):
        self.logger = logger
        if data is None:
            data = dict()
        elif type(data) is list:
            data = self.list_to_dict(data)
        self.data = data

    def __str__(self):
        return f'DataManager containing: {str(self.data)}'

    def list_to_dict(self, data):
        datalist = data
        data = dict()
        for x in range(len(datalist)):
            data[str(x)] = datalist[x]
        return data

    def iterate(self, *path):
        val = self.get(*path)
        try:
            for k in val:
                yield val[k]
        except KeyError:
            self.logger.error(f'{k} is not a value in {str(val)}')
            return None
        except TypeError:
            self.logger.error(f'{val} is not iterable')
            return None

    def get(self, *args):
        args = list(args)
        d = self.data
        return self._get(args, d)

    def _get(self, path, d):
        if isinstance(d, list):
            d = self.list_to_dict(d)
        if len(path) == 0:
            return d
        a = path.pop(0)
        try:
            return self._get(path, d[a])
        except KeyError:
            return None

    def update(self, u):
        self.data = self._update(self.data, u)

    def _update(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                r = self._update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d

    def add_data(self, path, data):
        path.reverse()
        last = {path.pop(0):data}
        for i in path:
            last = {i: last}
        self.update(last)


class Plugin:
    def __init__(self, phase, position, name, logger):
        self.logger = logger           # Logger is a logger
        self.load_phase = phase        # Program load phase
        # Load phase (0: Program Initialization, 1: Data collection, 2: Indexing,  3: File Processing, 4: File saving)
        self.load_position = position  # Load position in phase
        self.name = name               # Name of plugin
        logger.info(f'Loaded Plugin Object "{name}"')

    def process(self, obj):
        if obj.processed:
            return obj


class SectionManager:
    def __init__(self):
        self.sections = []

    def add_section(self, section):
        self.sections.append(section)

    def get_section(self, name):
        for s in self.sections:
            if s.name == name:
                return s
        return None

class Section:
    def __init__(self):
        self.variables = dict()
        self.text = str()
        self.name = str()
        self.ext = str()
        self.path = str()
        self.processed = False


class PluginManager:
    def __init__(self, phases):
        self.plugins = list()

    def _add_plugin(self, obj):
        self.plugins.append(obj)

    def add_plugin(self, o):
        if isinstance(o, list):
            for i in o:
                self._add_plugin(i)
        else:
            self._add_plugin(o)

    def get_plugins(self, phase):
        cplugins = list()
        for plugin in self.plugins:
            if plugin.load_phase == phase:
                cplugins.append(plugin)
        cplugins.sort(key=lambda x: x.load_position, reverse=False)
        for plugin in cplugins:
            yield plugin


class PluginLoader:
    @staticmethod
    def load_plugin(path, logger):
        loader = importlib.machinery.SourceFileLoader(f's3g_plugin_{os.path.splitext(os.path.split(path)[1])[0]}', path)
        logger.debug(f'Loaded "{loader.name}"')
        m = types.ModuleType(loader.name)
        loader.exec_module(m)
        try:
            pg = m.init(logger)
            return pg
        except AttributeError:
            logger.error(f'"{m.__name__}" has no init() function so could not be loaded"')

    @staticmethod
    def load_directory(d, logger):
        rv = []
        for f in os.listdir(d):
            if f.endswith('.py'):
                p = PluginLoader.load_plugin(os.path.join(d, f), logger)
                if p is not None:
                    rv.append(p)
        return rv


def _get_in_containing_tag(s, tag):
    START_PATTERN = f"<\s*?{tag}.*?>"
    END_PATTERN = f'<\s*?/\s*?{tag}\s*?>'
    start_matches = list()
    for m in re.finditer(START_PATTERN, s):
        start_matches.append(m)
    end_matches = list()
    for m in re.finditer(END_PATTERN, s):
        end_matches.append(m)
    if len(start_matches) != len(end_matches):
        raise SyntaxError('Invalid Tags')
    elif len(start_matches) == 0:
        return None
    return (start_matches[0].span(), start_matches[0].group()), (end_matches[-1].span(), end_matches[-1].group()), s[start_matches[0].span()[1]:end_matches[-1].span()[0]]


def get_in_containing_tag(s, tag):
    START_PATTERN = f"<\s*?{tag}.*?>"
    END_PATTERN = f'<\s*?/\s*?{tag}\s*?>'
    start = [i for i in re.finditer(START_PATTERN, s)]
    end = [i for i in re.finditer(END_PATTERN, s)]
    if (len(start) == 0) and (len(end) == 0):
        return None
    all_items = [*start, *end]
    all_items.sort(key=lambda x: x.span()[1], reverse=False)
    depth, start, end = 0, None, None
    for x in range(len(all_items)):
        if re.match(START_PATTERN, all_items[x].group()):
            if start is None:
                start = x
            else:
                depth += 1
        elif re.match(END_PATTERN, all_items[x].group()):
            if depth == 0:
                end = x
                break
            else:
                depth -= 1

    if start is None:
        raise SyntaxError('Invalid Structure')
    elif end is None:
        raise SyntaxError(f'Invalid Structure Processing ({str(all_items[start].group())})')
    start, end = all_items[start], all_items[end]
    return (start.span(), start.group()), (end.span(), end.group()), s[start.span()[0]:end.span()[1]]


def get_logger(name, log_level='INFO'):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(module)s/%(levelname)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

