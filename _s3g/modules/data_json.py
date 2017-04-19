import base
from json import loads
import json.decoder


class JsonDataReader(base.Plugin):
    def __init__(self, logger):
        super().__init__(1, 1, 'JsonDataReader', logger)

    def process(self, obj):
        super().process(obj)
        if obj.ext == ".json":
            try:
                obj.data = loads(obj.text)
            except json.decoder.JSONDecodeError as e:
                self.logger.error(f'"{obj.name}" contains invalid json: {e.msg} on line {e.lineno}, column {e.colno} (char {e.pos})')
            else:
                obj.processed = True
        return obj


def init(logger):
    return JsonDataReader(logger)