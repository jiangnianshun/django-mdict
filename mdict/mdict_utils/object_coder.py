from json import JSONEncoder
from .entry_object import entryObject


class objectEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def objectDecoder(o):
    return entryObject(o['mdx_name'], o['mdx_entry'], o['mdx_record'], o['mdx_pror'], o['pk'], o['f_pk'], o['f_p1'], o['f_p2'], o['extra'])
