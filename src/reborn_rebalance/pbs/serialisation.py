from pathlib import Path

import cattrs
from ruamel import yaml

from reborn_rebalance.pbs.pokemon import (
    GrowthRate,
    GenderRatio,
    EggGroup,
    PokemonSpecies,
)
from reborn_rebalance.pbs.type import PokemonType

# round-trip parser is non-C and way slower.
YAML = yaml.YAML(typ="safe")
YAML.indent(mapping=4, offset=4, sequence=6)


def create_cattrs_converter() -> cattrs.Converter:
    converter = cattrs.Converter()

    # dump enums via name rather than by value
    for enum in (PokemonType, EggGroup, GenderRatio, GrowthRate):
        converter.register_structure_hook(enum, lambda name, klass: klass[name])
        converter.register_unstructure_hook(enum, lambda it: it.name)

    return converter


CONVERTER = create_cattrs_converter()


def load_species_from_yaml(path: Path) -> (int, PokemonSpecies):
    """
    Loads a single species from the provided YAML file.

    :return A tuple of (dex number, parsed species).
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = YAML.load(f)

    key, obb = next(iter(data.items()))
    return key, CONVERTER.structure(obb, PokemonSpecies)


def save_species_to_yaml(output_path: Path, species: PokemonSpecies, dex: int):
    """
    Saves a single species to a YAML file.
    """

    output = {dex: CONVERTER.unstructure(species)}

    with output_path.open(encoding="utf-8", mode="w") as f:
        YAML.dump(output, f)


def load_all_species(path: Path) -> list[PokemonSpecies]:
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
        idx, decoded = load_species_from_yaml(path)
        species[idx - 1] = decoded

    if __debug__:
        for idx, read_in in enumerate(species):
            if read_in is None:
                raise ValueError(f"didn't load {idx + 1}")

    return species
