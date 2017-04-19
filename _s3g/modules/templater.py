import base, re


class Templater(base.Plugin):
    def __init__(self, logger):
        super().__init__(5, 10, 'Templater', logger)

    @staticmethod
    def process_section_tag(tag):
        for i in ['<', '>', 'section']:
            tag = tag.replace(i, '')
        tag = tag.replace('\'', '"')

        v = dict()
        reading = None

        tag = tag.split('"')
        for item in tag:
            if '=' in item:
                reading = item.replace('=', '').replace(' ', '')
            elif reading is not None:
                item = list(item.split(' '))
                item = [i for i in item if i != '']
                try:
                    v[reading] += item
                except KeyError:
                    v[reading] = item
        return v

    def process(self, obj):
        while True:  # This could this very bad
            try:
                stag = base.get_in_containing_tag(obj.text, 'section')
            except SyntaxError as e:
                self.logger.warning(f'Syntax Error: {e.msg}')
            if stag is None:
                return obj
            args = Templater.process_section_tag(stag[0][1])
            temp = obj.section_manager.get_section(args['type'][0])
            if temp is None:
                self.logger.warning(f'Template named "{args["type"][0]}" not found')
                return obj
            for default_arg in temp.variables:
                if default_arg not in args:
                    args[default_arg] = [temp.variables[default_arg]]

            temptext = temp.text

            for arg in args:
                for x in range(len(args[arg])):
                    if args[arg][x] is None:
                        args[arg][x] = ''
                temptext = temptext.replace(f'%{arg}%', ' '.join(args[arg]))
            content = obj.text[stag[0][0][1]:stag[1][0][0]]
            temptext = temptext.replace('%content%', content)
            obj.text = obj.text.replace(obj.text[stag[0][0][0]:stag[1][0][1]], temptext)
            obj.was_processed = True
        return obj

def init(logger):
    return Templater(logger)