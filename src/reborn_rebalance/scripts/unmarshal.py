import sys
from io import StringIO
from pathlib import Path

import prettyprinter
from prettyprinter import pprint, pretty_call, pretty_call_alt
from prettyprinter.prettyprinter import pretty_dict
from rubymarshal.classes import RubyObject
from rubymarshal.reader import loads


@prettyprinter.register_pretty(RubyObject)
def prettify_ro(value: RubyObject, ctx):
    return pretty_dict(value.attributes, ctx)


def main():
    data = Path(sys.argv[1]).read_bytes()
    obb = loads(data)

    outputted = StringIO()
    pprint(obb, stream=outputted)
    print(outputted.getvalue().replace("'", '"').replace("True", "true").replace("False", "false"))
