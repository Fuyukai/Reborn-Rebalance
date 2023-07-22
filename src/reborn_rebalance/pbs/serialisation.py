from __future__ import annotations

import csv
from io import StringIO
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
from reborn_rebalance.pbs.raw.item import PokemonItem
from reborn_rebalance.pbs.raw.pokemon import raw_parse_pokemon_pbs
from reborn_rebalance.pbs.raw.tm import TechnicalMachine
from reborn_rebalance.pbs.type import PokemonType
from reborn_rebalance.util import PbsBuffer, chunks

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

    TechnicalMachine.add_unstructuring_hook(converter)

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


def load_items_from_pbs(path: Path) -> list[PokemonItem]:
    """
    Loads all items from the provided ``PBS/items.txt`` file.
    """

    items: list[PokemonItem] = []

    with path.open(mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)

        for line in reader:
            items.append(PokemonItem.from_row(line))

    return items


def load_items_from_yaml(path: Path) -> list[PokemonItem]:
    """
    Loads all items from the provided ``items.yaml`` file.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = YAML.load(f)

    items: list[PokemonItem] = []
    for item in data:
        items.append(CONVERTER.structure(item, PokemonItem))

    return items


def save_items_to_pbs(output_path: Path, items: list[PokemonItem]):
    """
    Saves all items to PBS format (CSV) instead.
    """

    items = sorted(items, key=lambda it: it.id)

    with output_path.open(mode="w", encoding="utf-8") as f:
        writer = csv.writer(f)

        for item in items:
            writer.writerow(item.get_as_pbs_row())


def save_items_to_yaml(output_path: Path, items: list[PokemonItem]):
    """
    Saves all items to YAML.
    """

    items = sorted(items, key=lambda it: it.id)
    output = CONVERTER.unstructure(items)

    with output_path.open(encoding="utf-8", mode="w") as f:
        YAML.dump(output, f)


def load_tms_from_pbs(path: Path) -> list[TechnicalMachine]:
    """
    Loads all TMs from the provided ``PBS/tm.txt`` file.

    The provided definitions will be incomplete! The catalog will automatically fill these in.
    """

    tms: list[TechnicalMachine] = []

    with path.open(mode="r", encoding="utf-8") as f:
        # silly format, really
        lines = [line for line in f.read().splitlines() if line and not line.startswith("#")]
        lines = chunks(lines, 2)

        for move, pokemon in lines:
            move = move[1:-1]
            pokemon = pokemon.split(",")
            tms.append(TechnicalMachine.incomplete_from_pbs(move, pokemon))

    return tms


def load_tms_from_yaml(path: Path) -> list[TechnicalMachine]:
    """
    Loads all TMs from the provided ``technical_machines.yaml`` file.

    This produces full, complete TM objects.
    """

    tms: list[TechnicalMachine] = []

    with path.open(encoding="utf-8", mode="r") as f:
        data = YAML.load(f)
        real_data = data["tm"] + data["tutor"]

        for tm in real_data:
            tms.append(CONVERTER.structure(tm, TechnicalMachine))

    return tms


def save_tms_to_yaml(path: Path, tms: list[TechnicalMachine]):
    """
    Saves all TMs to YAML.
    """

    # fucking sort these properly
    real_dict = {
        "tm": sorted([it for it in tms if not it.is_tutor], key=lambda it: it.number),
        "tutor": sorted([it for it in tms if it.is_tutor], key=lambda it: it.move),
    }

    output = CONVERTER.unstructure(real_dict)

    with path.open(encoding="utf-8", mode="w") as f:
        YAML.dump(output, f)


def save_tms_to_pbs(path: Path, tms: list[TechnicalMachine]):
    """
    Saves all TMs to PBS format (CSV) instead.

    This *requires* that you backfill the ``pokemon`` field!
    """

    # yay, more stupid formats
    buffer = StringIO()

    for tm in tms:
        buffer.write(f"[{tm.move}]\n")
        buffer.write(",".join(tm.pokemon))
        buffer.write("\n")

    path.write_text(buffer.getvalue(), encoding="utf-8")
