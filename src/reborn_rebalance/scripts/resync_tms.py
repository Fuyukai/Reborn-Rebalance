import sys
from pathlib import Path

import sortedcontainers
from rich import print

from reborn_rebalance.pbs.serialisation import (
    load_all_species_from_toml,
    load_tms_from_toml,
    save_all_species_to_toml,
)


def main() -> int:
    """
    Re-adds all species TM data from the ``tms.toml`` file.
    """

    try:
        species_path = Path(sys.argv[1])
        tms_path = Path(sys.argv[2])
    except IndexError:
        print(
            f"usage: {sys.argv[0]} <path to species dir> <path to tms dir> "
            "<path to output species dir>"
        )
        return 1

    try:
        output_dir = Path(sys.argv[3])
    except IndexError:
        output_dir = Path("./data/species-1")
        output_dir.mkdir(parents=True, exist_ok=True)

    all_species = load_all_species_from_toml(species_path)
    tm_data = load_tms_from_toml(tms_path)

    tm_mapping = {tm.move: tm for tm in tm_data}

    for species in all_species:
        existing_tms = set(species.raw_tms)
        existing_tutors = set(species.raw_tutor_moves)
        new_tms = sortedcontainers.SortedList(
            existing_tms,
        )
        new_tutors = sortedcontainers.SortedList(existing_tutors)

        for move in species.raw_level_up_moves:
            tm_name = move.name
            if tm_name not in tm_mapping:
                continue

            # ugh, slow
            tm = tm_mapping[tm_name]

            if tm_name in tm_mapping:
                if tm.is_tutor and tm.move not in existing_tutors:
                    print(
                        f"adding [green]new tutor move[green] '{move.name}' to "
                        f"{species.internal_name}"
                    )
                    new_tutors.add(move.name)

                elif not tm.is_tutor and tm.move not in existing_tms:
                    print(
                        f"adding [green]new TM[/green] TM{tm.number} '{move.name}' "
                        f"to {species.internal_name}"
                    )
                    new_tms.add(move.name)

        species.raw_tms = list(new_tms)
        species.raw_tutor_moves = list(new_tutors)

    save_all_species_to_toml(output_dir, all_species, allow_overwriting=True)

    return 0
