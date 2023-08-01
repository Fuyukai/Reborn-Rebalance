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
[[0,PBMoves::SHELLSIDEARM],[1,PBMoves::SHELLSIDEARM],[1,PBMoves::WITHDRAW],
      [1,PBMoves::TACKLE],[1,PBMoves::CURSE],[1,PBMoves::GROWL],[1,PBMoves::ACID],[9,PBMoves::YAWN],[12,PBMoves::CONFUSION],
      [15,PBMoves::DISABLE],[18,PBMoves::WATERPULSE],[21,PBMoves::HEADBUTT],[24,PBMoves::ZENHEADBUTT],
      [27,PBMoves::AMNESIA],[30,PBMoves::SURF],[33,PBMoves::SLACKOFF],[36,PBMoves::PSYCHIC],[39,PBMoves::PSYCHUP],
      [42,PBMoves::RAINDANCE],[45,PBMoves::HEALPULSE]]
        """,
        )
    )
