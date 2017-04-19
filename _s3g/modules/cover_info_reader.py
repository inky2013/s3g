import base
import os
import xmldict


class CoverDataReader(base.Plugin):
    def __init__(self, logger):
        super().__init__(4, 0, 'CoverDataReader', logger)
        self.processed_pages = list()  # Plugin only needs to run once per page

    def process(self, obj):
        if obj.path in self.processed_pages:
            return obj

        depth = len([i for i in list(os.path.split(os.path.dirname(obj.path))) if i != ''])
        if depth < 2:
            depthstr = "./"
        else:
            depthstr = '../' * (depth - 1)
        obj.data.add_data(['page', 'root'], depthstr[:-1])

        self.processed_pages.append(obj.path)
        varxml = base.get_in_containing_tag(obj.text, 'cover')
        if varxml is not None:
            if varxml[0][0][0] != 0:
                self.logger.error(f'Cover info for "{obj.name}" does not appear at top of file')
                return obj
            xmls = obj.text[varxml[0][0][0]:varxml[1][0][1]]
            obj.data.update(xmldict.xml_to_dict(xmls))

            obj.text = obj.text.replace(xmls, '', 1)

        obj.was_processed = True
        return obj


def init(logger):
    return CoverDataReader(logger)