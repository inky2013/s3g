from base import *
import xmldict


class HTMLTemplateReader(Plugin):
    def __init__(self, logger):
        super().__init__(2, 10, 'HTMLTemplateReader', logger)

    def process(self, obj):
        super().process(obj)
        varxml = get_in_containing_tag(obj.text, 'defaults')
        if varxml is not None:
            if varxml[0][0][0] != 0:
                self.logger.error(f'Default variables for "{obj.name}" do not appear at top of file')
                return obj
            xmls = obj.text[varxml[0][0][0]:varxml[1][0][1]]
            obj.variables = xmldict.xml_to_dict(xmls)['defaults']
            obj.text = obj.text.replace(xmls, '', 1)
        obj.processed = True
        return obj


def init(logger):
    return HTMLTemplateReader(logger)