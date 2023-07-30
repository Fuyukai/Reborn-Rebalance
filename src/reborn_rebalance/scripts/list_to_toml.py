import string
from pathlib import Path

import cattrs
import tomlkit

from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.pokemon import RawLevelUpMove


def _inner_move(move_slice: str):
    level, move = move_slice.split(",", 1)
    move = move.strip()[9:]

    return RawLevelUpMove(at_level=int(level.strip()), name=move)


# input: raw movelist, e.g. ``[[0, PBMoves::ROCKSMASH], ...]``
def parse_ruby(catalog: EssentialsCatalog, raw_data: str):
    all_moves = raw_data.replace("\n", "").replace("\r", "").strip()
    if all_moves[0] == "[":
        all_moves = all_moves[1:]

    if all_moves[-1] == "]":
        all_moves = all_moves[:-1]

    moves = []
    idx = 0

    while idx < len(all_moves):
        next_char = all_moves[idx]
        if next_char == "[":
            start = idx + 1

            while all_moves[idx] != "]":
                idx += 1

            moves.append(_inner_move(all_moves[start:idx]))
            idx += 1

        elif next_char == "," or next_char in string.whitespace:
            idx += 1

        else:
            raise ValueError(f"Unexpected char '{next_char}' ({hex(ord(next_char))})")

    raw_data = {"raw_level_up_moves": cattrs.unstructure(moves)}
    return tomlkit.dumps(raw_data)


def parse_buffel_salt(catalog: EssentialsCatalog, form: str, data: str):
    lines = data.splitlines()
    moves = []

    for line in lines:
        if not (line := line.strip()):
            continue

        level, move = line.strip().split(" - ")
        move = catalog.move_by_display_name(move)
        moves.append(RawLevelUpMove(at_level=int(level), name=move.internal_name))

    data = {"forms": {form: {"raw_level_up_moves": cattrs.unstructure(moves)}}}
    return tomlkit.dumps(data)


if __name__ == "__main__":
    loaded = EssentialsCatalog.load_from_toml(Path("./data"), skip_species=True)
    print(
        parse_buffel_salt(
            loaded,
            "Female",
            """
    1 - Stored Power
1 - Me First
1 - Magical Leaf
1 - Scratch
1 - Leer
1 - Covet
1 - Confusion
5 - Covet
9 - Confusion
13 - Light Screen
17 - Psybeam
19 - Fake Out
22 - Disarming Voice
25 - Psyshock
28 - Charge Beam
31 - Shadow Ball
33 - Assist
35 - Extrasensory
40 - Psychic
43 - Role Play
45 - Signal Beam
48 - Sucker Punch
50 - Future Sight
53 - Stored Power
56 - Nasty Plot""",
        )
    )
