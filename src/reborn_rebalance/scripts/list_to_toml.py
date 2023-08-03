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
def parse_ruby(catalog: EssentialsCatalog, form: str, raw_data: str):
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

    if form is not None:
        raw_data = {"forms": {form: {"raw_level_up_moves": cattrs.unstructure(moves)}}}
    else:
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

    if form:
        data = {"forms": {form: {"raw_level_up_moves": cattrs.unstructure(moves)}}}
    else:
        data = {"raw_level_up_moves": cattrs.unstructure(moves)}

    return tomlkit.dumps(data)


if __name__ == "__main__":
    loaded = EssentialsCatalog.load_from_toml(Path("./data"), skip_species=True)
    print(
        parse_ruby(
            loaded,
            "Galar",
            """
[[1,PBMoves::BATONPASS],[1,PBMoves::COPYCAT],[1,PBMoves::DAZZLINGGLEAM],[1,PBMoves::ENCORE],
      				 [1,PBMoves::ICESHARD],[1,PBMoves::LIGHTSCREEN],[1,PBMoves::MIMIC],[1,PBMoves::MISTYTERRAIN],[1,PBMoves::POUND],
     				  [1,PBMoves::PROTECT],[1,PBMoves::RAPIDSPIN],[1,PBMoves::RECYCLE],[1,PBMoves::REFLECT],[1,PBMoves::ROLEPLAY],
     				  [1,PBMoves::SAFEGUARD],[12,PBMoves::CONFUSION],[16,PBMoves::ALLYSWITCH],[20,PBMoves::ICYWIND],[24,PBMoves::DOUBLEKICK],
      				  [28,PBMoves::PSYBEAM],[32,PBMoves::HYPNOSIS],[36,PBMoves::MIRRORCOAT],[40,PBMoves::SUCKERPUNCH],[44,PBMoves::FREEZEDRY],
      				  [48,PBMoves::PSYCHIC],[52,PBMoves::TEETERDANCE]]
        """,
        )
    )
