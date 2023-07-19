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

YAML = yaml.YAML()
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
