import sys
from pathlib import Path

import cattr
import ruamel.yaml

from reborn_rebalance.pbs.pokemon import PokemonSpecies
from reborn_rebalance.pbs.raw.pokemon import raw_parse_pokemon_pbs
from reborn_rebalance.pbs.type import PokemonType

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

YAML = ruamel.yaml.YAML()
YAML.indent(mapping=4, offset=4, sequence=6)


def dump_pokemon(pbs: Path, output: Path):
    """
    Dumps all Pokémon from the provided ``pokemon.txt`` into the provided output directory.
    """

    for gen in range(0, 9):
        (output / f"gen_{gen + 1}").mkdir(exist_ok=True)

    input_pokemon = raw_parse_pokemon_pbs(pbs)

    for idx, raw in enumerate(input_pokemon):
        idx += 1
        parsed = PokemonSpecies.from_pbs(raw)

        for gidx, gen_range in enumerate(GENERATIONS):
            if idx in gen_range:
                break
        else:
            raise ValueError(f"unknown generation for pokemon #{idx}")

        name = f"{idx:04d}-{parsed.name.lower()}"
        yaml_path = (output / f"gen_{gidx + 1}" / name).with_suffix(".yaml")
        dumped = {idx: cattr.unstructure(parsed)}

        if yaml_path.exists():
            print(f"Not overwriting {name}")
            continue

        with yaml_path.open(mode="w", encoding="utf-8") as f:
            YAML.dump(dumped, f)
            print(f"Saved {name}")


def main():
    """
    Dumps all of the PBS data into YAML files.
    """

    try:
        input_dir = Path(sys.argv[1]).absolute()
        output_dir = Path(sys.argv[2]).absolute()
    except IndexError:
        print(f"usage: {sys.argv[0]} <input PBS dir> <output YAML dir>")
        return 1

    if not input_dir.exists():
        print(f"{input_dir} doesn't exist")
        return 1

    # unfuck cattrs
    cattr.global_converter.register_unstructure_hook(PokemonType, lambda it: it.name)

    output_dir.mkdir(exist_ok=True, parents=True)

    pokemon_location = output_dir / "species"
    pokemon_location.mkdir(parents=True, exist_ok=True)

    dump_pokemon(
        input_dir / "pokemon.txt",
        pokemon_location,
    )


if __name__ == "__main__":
    sys.exit(main())
