import base, re


class VarSetter(base.Plugin):
    def __init__(self, logger):
        super().__init__(5, 20, 'VarSetter', logger)

    @staticmethod
    def ensure_list(l):
        if not isinstance(l, list):
            return [l]
        return l

    def process(self, obj):
        matches = re.findall('%.*?%', obj.text)
        if len(matches) == 0:
            return obj
        for match in matches:
            m = match[1:-1]
            m = obj.data.get(*VarSetter.ensure_list(m.split('.')))
            if m is not None:
                obj.text = obj.text.replace(match, m)
                obj.was_processed = True
        return obj



def init(logger):
    return VarSetter(logger)