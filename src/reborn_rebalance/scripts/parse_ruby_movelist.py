
import re
import sys

import tomli_w

MOVE_NAME_REGEX = re.compile(r"\[(?P<at_level>[0-9]{1,2}) ?, ?PBMoves::(?P<name>[A-Z]+)", re.MULTILINE)

def main():
    try:
        form = sys.argv[1]
        input = sys.argv[2]
    except IndexError:
        print(f"usage: {sys.argv[0]} <form name> <ruby movelist>")

    moves = []
    toml_out = {"forms": {form: {"raw_level_up_moves": moves}}}

    for split in MOVE_NAME_REGEX.finditer(input):
        matched = split.groupdict()
        moves.append(matched)
    
    print(tomli_w.dumps(toml_out))
    
