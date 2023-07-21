from __future__ import annotations

import csv
from pathlib import Path

import cattrs
from ruamel import yaml

from reborn_rebalance.pbs.move import MoveCategory, MoveFlag, MoveTarget, PokemonMove
from reborn_rebalance.pbs.pokemon import (
    EggGroup,
    GenderRatio,
    GrowthRate,
    PokemonSpecies,
)
from reborn_rebalance.pbs.raw.pokemon import raw_parse_pokemon_pbs
from reborn_rebalance.pbs.type import PokemonType
from reborn_rebalance.util import PbsBuffer

GENERATIONS = [
    # Bulbasaur -> Mew
    range(1, 152),
    # Chikorita -> Celebi
    range(152, 252),
    # Treecko -> Deoxys
    range(252, 387),
    # Turtwig -> Arceus
    range(387, 494),
    # Victini(?) -> Genesect
    range(494, 650),
    # Chespin -> Volcanion
    range(650, 722),
    # Rowlet -> Melmetal
    range(722, 810),
    # Grookey -> Enamorus
    range(810, 906),
    # Sprigatito -> Iron Leaves
    range(906, 1021),
]

# round-trip parser is non-C and way slower.
YAML = yaml.YAML(typ="rt")
YAML.indent(mapping=4, offset=4, sequence=6)


def create_cattrs_converter() -> cattrs.Converter:
    converter = cattrs.Converter()

    # dump enums via name rather than by value
    for enum in (
        PokemonType,
        EggGroup,
        GenderRatio,
        GrowthRate,
        MoveCategory,
        MoveTarget,
        MoveFlag,
    ):
        converter.register_structure_hook(enum, lambda name, klass: klass[name])
        converter.register_unstructure_hook(enum, lambda it: it.name)

    return converter


CONVERTER = create_cattrs_converter()


def load_single_species_yaml(path: Path) -> (int, PokemonSpecies):
    """
    Loads a single species from the provided YAML file.

    :return A tuple of (dex number, parsed species).
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = YAML.load(f)

    key, obb = next(iter(data.items()))
    return key, CONVERTER.structure(obb, PokemonSpecies)


def load_all_species_from_pbs(path: Path) -> list[PokemonSpecies]:
    """
    Loads all Pokémon species from the provided PBS file.
    """

    raw_data = raw_parse_pokemon_pbs(path)
    return [PokemonSpecies.from_pbs(it) for it in raw_data]


def load_all_species_from_yaml(path: Path) -> list[PokemonSpecies]:
    """
    Loads all species from the YAML directory, and returns them in Pokédex order.
    """

    to_read = []

    for dir in path.iterdir():
        for subpath in dir.iterdir():
            to_read.append(subpath)

    species: list[PokemonSpecies] = [None] * len(to_read)  # type: ignore
    for path in to_read:
        print(f"LOAD: {path}")
        idx, decoded = load_single_species_yaml(path)
        species[idx - 1] = decoded

    if __debug__:
        for idx, read_in in enumerate(species):
            if read_in is None:
                raise ValueError(f"didn't load {idx + 1}")

    return species


def save_all_species_to_pbs(path: Path, all_species: list[PokemonSpecies]):
    """
    Saves all Pokémon species from the provided list into PBS format.
    """

    buffer = PbsBuffer()

    for idx, species in enumerate(all_species):
        buffer.write_id_header(idx + 1)
        species.to_pbs(buffer)

    path.write_text(buffer.backing.getvalue(), encoding="utf-8")


def save_single_species_to_yaml(output_path: Path, species: PokemonSpecies, dex: int):
    """
    Saves a single species to a YAML file.
    """

    output = {dex: CONVERTER.unstructure(species)}

    with output_path.open(encoding="utf-8", mode="w") as f:
        YAML.dump(output, f)


def save_all_species_to_yaml(output_path: Path, input_pokemon: list[PokemonSpecies]):
    """
    Saves all species to the provided ``output_path`` in YAML format, divided by generation.
    """

    for gen in range(0, 9):
        (output_path / f"gen_{gen + 1}").mkdir(exist_ok=True)

    for idx, species in enumerate(input_pokemon):
        idx += 1

        for gidx, gen_range in enumerate(GENERATIONS):
            if idx in gen_range:
                break
        else:
            raise ValueError(f"unknown generation for pokemon #{idx}")

        name = f"{idx:04d}-{species.name.lower()}"
        yaml_path = (output_path / f"gen_{gidx + 1}" / name).with_suffix(".yaml")

        if yaml_path.exists():
            print(f"Not overwriting {name}")
            continue

        save_single_species_to_yaml(yaml_path, species, idx)
        print(f"Saved {name}")


def load_moves_from_pbs(path: Path) -> list[PokemonMove]:
    """
    Loads all moves from the provided ``PBS/moves.txt`` file.
    """

    moves: list[PokemonMove] = []

    with path.open(mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)

        for line in reader:
            moves.append(PokemonMove.load_from_pbs_line(line))

    return moves


def load_moves_from_yaml(path: Path) -> list[PokemonMove]:
    """
    Loads all moves from the providied ``moves.yaml`` file.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = YAML.load(f)

    moves: list[PokemonMove] = []
    for move in data:
        moves.append(CONVERTER.structure(move, PokemonMove))

    return moves


def save_moves_to_yaml(output_path: Path, moves: list[PokemonMove]):
    """
    Saves all moves to YAML.
    """

    # sort the moves by internal ID first.
    # probably essentials doeesn't like it if you don't do this.
    moves = sorted(moves, key=lambda it: it.id)

    output = CONVERTER.unstructure(moves)

    with output_path.open(encoding="utf-8", mode="w") as f:
        YAML.dump(output, f)


def save_moves_to_pbs(output_path: Path, moves: list[PokemonMove]):
    """
    Saves all moves to PBS format (CSV) instead.
    """

    moves = sorted(moves, key=lambda it: it.id)

    with output_path.open(mode="w", encoding="utf-8") as f:
        writer = csv.writer(f)

        for move in moves:
            writer.writerow(move.get_as_pbs_row())
