import sys
from pathlib import Path

from prettyprinter import pprint
from rubymarshal.reader import loads


def main():
    data = Path(sys.argv[1]).read_bytes()
    obb = loads(data)
    pprint(obb)
