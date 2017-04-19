from base import *

class DefaultFileMarker(Plugin):
    def __init__(self, logger):
        super().__init__(3, 1, 'DefaultFileMarker', logger)
        with open('filetypes.txt', 'a+') as f:
            f.seek(0)  # The file opens at the end
            self.types = f.read().split('\n')
            self.types = [t.replace('.', '') for t in self.types if t != '']

    def process(self, obj):
        super().process(obj)
        if obj.ext.replace('.', '') in self.types:
            obj.needs_processing = True
        else:
            self.logger.debug(f'"{obj.ext}" extension not in "filetypes.txt"')
        obj.processed = True
        return obj

def init(logger):
    return DefaultFileMarker(logger)