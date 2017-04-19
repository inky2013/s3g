import base


class FileDataReader(base.Plugin):
    def __init__(self, logger):
        super().__init__(1, 1, 'FileDataReader', logger)

    def process(self, obj):
        super().process(obj)
        if obj.ext in [".js", ".txt", ".html", ".css"]:
            obj.data = obj.text
            obj.processed = True
        return obj


def init(logger):
    return FileDataReader(logger)
