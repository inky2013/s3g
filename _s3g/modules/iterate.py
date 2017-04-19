import base


class Iterator(base.Plugin):
    def __init__(self, logger):
        super().__init__(5, 30, 'Iterator', logger)

    @staticmethod
    def get_iterlist(stag, obj):
        stag = stag.replace('<', '').replace('>', '').replace('for', '')
        stag = [i for i in stag.split(' ') if i != '']
        identifier = stag[0]
        if stag[1] == "from":
            if stag[3] != "to":
                raise SyntaxError('Expected "to" in loop')
            step = 1
            if len(stag) > 5:
                if stag[5] == "step":
                    step = stag[6]
            f, t = stag[2], stag[4]
            return identifier, range(int(f), int(t), int(step)), None
        elif stag[1] == "in":
            dlist = stag[2].split('.')
            if not isinstance(dlist, list):
                dlist = [dlist]
            return identifier, obj.data.iterate(*dlist), stag[2]

    def process(self, obj):
        loop = base.get_in_containing_tag(obj.text, 'for')
        if loop is None:
            return obj
        i, r, fb = Iterator.get_iterlist(loop[0][1], obj)
        tti = obj.text[loop[0][0][1]:loop[1][0][0]]
        fin = ''
        index = 0
        for item in r:
            val = tti.replace(f'%{i}%', str(item))
            val = val.replace(f'%{i}', f'%{str(fb)}.{str(index)}')
            fin += val
            index += 1
        obj.text = obj.text.replace(obj.text[loop[0][0][0]:loop[1][0][1]], fin, 1)
        obj.was_processed = True
        return obj



def init(logger):
    return Iterator(logger)