import sys
from math import ceil, log
from pathlib import Path

import tomlkit
import unidecode

from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.move import PokemonMove
from reborn_rebalance.pbs.serialisation import generation_for

CORRECTIONS = {
    "Faint Attack": "Feint Attack",
    "Twinneedle": "Twineedle",
    "Sliver Wind": "Silver Wind",
    "Autonomize": "Autotomize",
    "Double Edge": "Double-Edge",  # lol?
    "Acid Armour": "Acid Armor",
    "Will-O-Wiisp": "Will-O-Wisp",
    "Ominous Mind": "Ominous Wind",  # my fav so far
    "V-Create": "V-create",
}

NAME_CORRECTIONS = {"mr. mime": "mr"}  # ?


def get_leading_int(line: str) -> int:
    built = 0

    for char in line:
        if char.isnumeric():
            built = (built * 10) + int(char)
        else:
            return built


def page_length(i: int) -> int:
    return int(ceil(log(i, 10) + 0.000001))


def find_move_by_display(catalog: EssentialsCatalog, move_name: str) -> PokemonMove:
    for move in catalog.moves:
        if move.display_name == move_name:
            return move

    raise ValueError(f"no such move: {move_name}")


def main(catalog: EssentialsCatalog):
    changes_file = Path(sys.argv[1])
    # why?
    changes_data = changes_file.read_text(encoding="utf-16").splitlines()

    # fuck the enum
    cached_move_mapping = {}
    is_reading_moves = True
    files = {}
    current_file = None
    current_moves = []

    idx = 0
    while True:
        try:
            initial_line = changes_data[idx]
        except IndexError:
            break

        if not initial_line:
            idx += 1

        elif initial_line.startswith("="):
            if current_moves:
                if (
                    not any(current_file[1].endswith(str(it)) for it in range(1, 11))
                    and current_file[0] >= 650
                    or current_file[0] in (524, 525, 526)
                ):
                    files[current_file] = current_moves
                    print(f"parsed {current_file}")

                current_moves = []

            pdx_idx, name = changes_data[idx + 1].split(" ", 1)
            pdx_idx = int(pdx_idx)

            # skip extra forms
            current_file: tuple[int, str] = (int(pdx_idx), unidecode.unidecode(name.lower()))

            # skip past the next line, otherwise it'll trigger this if block again
            idx += 3
        # reading off the moves now
        elif initial_line.startswith("Level Up"):
            idx += 1
            is_reading_moves = True

        elif initial_line.startswith("Base Exp"):
            # Nosepass
            idx += 3

        elif initial_line.startswith("Gender Ratio"):
            # Combee
            idx += 4

        elif (level := get_leading_int(initial_line)) > 0 and is_reading_moves:
            # extra condition is here to prevent e.g. wormadam from fucking up
            # move data!
            move_name = initial_line[page_length(level) + 3 :].strip()
            # [*]
            if move_name.endswith("]"):
                move_name = move_name[:-4]

            # remove fancy apostrophes
            move_name = unidecode.unidecode(move_name)

            # ech. hardcode it for now
            if move_name != "Light of Ruin":
                move_name = CORRECTIONS.get(move_name, move_name)
                if move_name in cached_move_mapping:
                    internal_name = cached_move_mapping[move_name]
                else:
                    internal_name = cached_move_mapping.setdefault(
                        move_name, find_move_by_display(catalog, move_name)
                    )

                current_moves.append((level, internal_name))
            idx += 1
        else:
            # idc
            idx += 1

    # manually load species from toml
    for key, moves in files.items():
        number, name = key

        if name == "mr. mime":
            name = "mr"

        elif name == "kyurem":
            number = 646

        # stupid fucking files that I edited manually
        if number not in (524, 525, 526) and number < 650:
            print("skipping", number)
            continue

        gen = generation_for(number)
        name = NAME_CORRECTIONS.get(name, name.lower())
        filename = Path("./data/species") / f"gen_{gen + 1}" / f"{number:04d}-{name.lower()}.toml"

        with filename.open(mode="r", encoding="utf-8") as f:
            data = dict(tomlkit.load(f).items())

        pokemon_moves: list[tuple[int, PokemonMove]] = sorted(moves, key=lambda it: it[0])

        data["raw_level_up_moves"] = []

        for level_up_at, move in pokemon_moves:
            entry = {"at_level": level_up_at, "name": move.internal_name}
            data["raw_level_up_moves"].append(entry)

        with filename.open(mode="w", encoding="utf-8") as f:
            tomlkit.dump(data, f)


if __name__ == "__main__":
    print("loading catalog...")
    catalog = EssentialsCatalog.load_from_toml(Path("./data"), skip_species=True)
    print('"parsing" changes file...')
    main(catalog)
