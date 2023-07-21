import csv
from pathlib import Path
from typing import Self

import attr

from reborn_rebalance.pbs.move import PokemonMove
from reborn_rebalance.pbs.pokemon import PokemonSpecies
from reborn_rebalance.pbs.serialisation import (
    load_all_species_from_pbs,
    load_all_species_from_yaml,
    load_moves_from_pbs,
    load_moves_from_yaml,
    save_all_species_to_pbs,
    save_all_species_to_yaml,
    save_moves_to_pbs,
    save_moves_to_yaml,
)


@attr.s(slots=True, kw_only=True)
class EssentialsCatalog:
    """
    Super-object that contains references to all of the data in the game.
    """

    #: The list of all known species.
    species: list[PokemonSpecies] = attr.ib()

    #: The list of all known moves.
    moves: list[PokemonMove] = attr.ib()

    @classmethod
    def load_from_pbs(cls, path: Path) -> Self:
        """
        Loads all objects from PBS files in the provided Reborn ``PBS`` directory.
        """

        pokemon_path = path / "pokemon.txt"
        species = load_all_species_from_pbs(pokemon_path)

        moves_path = path / "moves.txt"
        moves = load_moves_from_pbs(moves_path)

        return cls(species=species, moves=moves)

    @classmethod
    def load_from_yaml(cls, path: Path) -> Self:
        """
        Loads all objects from YAML files in the provided ``data`` directory.
        """

        species_dir = path / "species"
        species = load_all_species_from_yaml(species_dir)

        moves_file = path / "moves.yaml"
        moves = load_moves_from_yaml(moves_file)

        return cls(species=species, moves=moves)

    def save_to_yaml(self, path: Path):
        """
        Serialises all objects within this catalog to YAML format.
        """

        path.mkdir(parents=True, exist_ok=True)

        species_path = path / "species"
        species_path.mkdir(parents=True, exist_ok=True)
        save_all_species_to_yaml(species_path, self.species)

        moves_path = path / "moves.yaml"
        save_moves_to_yaml(moves_path, self.moves)

    def save_to_pbs(self, pbs_dir: Path):
        """
        Serialises all objects within this catalog to PBS format.
        """

        pokemon_txt = pbs_dir / "pokemon.txt"
        save_all_species_to_pbs(pokemon_txt, self.species)

        moves_txt = pbs_dir / "moves.txt"
        save_moves_to_pbs(moves_txt, self.moves)
