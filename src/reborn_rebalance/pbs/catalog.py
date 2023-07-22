import csv
from pathlib import Path
from typing import Self, Optional

import attr

from reborn_rebalance.pbs.move import PokemonMove
from reborn_rebalance.pbs.pokemon import PokemonSpecies
from reborn_rebalance.pbs.raw.item import PokemonItem
from reborn_rebalance.pbs.raw.tm import tm_number_for, TechnicalMachine
from reborn_rebalance.pbs.serialisation import (
    load_all_species_from_pbs,
    load_all_species_from_yaml,
    load_moves_from_pbs,
    load_moves_from_yaml,
    save_all_species_to_pbs,
    save_all_species_to_yaml,
    save_moves_to_pbs,
    save_moves_to_yaml, load_items_from_pbs, load_tms_from_pbs, save_items_to_yaml,
    save_tms_to_yaml, save_items_to_pbs, save_tms_to_pbs,
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

    #: The list of all known items.
    items: list[PokemonItem] = attr.ib()

    #: The list of all known TMs.
    tms: list[TechnicalMachine] = attr.ib()

    @classmethod
    def load_from_pbs(cls, path: Path) -> Self:
        """
        Loads all objects from PBS files in the provided Reborn ``PBS`` directory.
        """

        pokemon_path = path / "pokemon.txt"
        all_species = load_all_species_from_pbs(pokemon_path)

        moves_path = path / "moves.txt"
        moves = load_moves_from_pbs(moves_path)

        items_path = path / "items.txt"
        items = load_items_from_pbs(items_path)

        tm_path = path / "tm.txt"
        tms = load_tms_from_pbs(tm_path)

        # now, backfill in the TMs fields from tms and items
        # (this is saved in the actual YAML)
        # use the display names
        tm_move_mapping: dict[str, PokemonMove] = {it.internal_name: it for it in moves}
        tm_item_mapping: dict[str, PokemonItem] = {it.move: it for it in items if
                                                   it.display_name.startswith("TM")}
        tm_poke_mapping: dict[str, PokemonSpecies] = {it.internal_name: it for it in all_species}

        for tm in tms:
            try:
                tm_item = tm_item_mapping[tm.move]
            except KeyError:
                # actually a fucking tutor move!
                tm.is_tutor = True
            else:
                tm.is_tmx = tm_item.display_name.startswith("TMX")
                tm.number = tm_number_for(tm_item.display_name)

                # synchronise descriptions
                tm_item.description = tm_move_mapping[tm.move].description

            for poke_name in tm.pokemon:
                if not poke_name:
                    print(f"empty entry in {tm.move}!")
                    continue

                species = tm_poke_mapping[poke_name]

                if tm.is_tutor:
                    species.raw_tutor_moves.append(tm.move)
                else:
                    species.raw_tms.append(tm.move)

            tm.pokemon.clear()

        return cls(species=all_species, moves=moves, items=items, tms=tms)

    @classmethod
    def load_from_yaml(cls, path: Path) -> Self:
        """
        Loads all objects from YAML files in the provided ``data`` directory.
        """

        species_dir = path / "species"
        species = load_all_species_from_yaml(species_dir)

        moves_file = path / "moves.yaml"
        moves = load_moves_from_yaml(moves_file)

        items_path = path / "items.yaml"
        items = load_items_from_pbs(items_path)

        tm_path = path / "tms.yaml"
        tms = load_tms_from_pbs(tm_path)

        return cls(
            species=species, moves=moves,
            items=items, tms=tms
        )

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

        items_path = path / "items.yaml"
        save_items_to_yaml(items_path, self.items)

        tms_path = path / "tms.yaml"
        save_tms_to_yaml(tms_path, self.tms)

    def save_to_pbs(self, pbs_dir: Path):
        """
        Serialises all objects within this catalog to PBS format.
        """

        pokemon_txt = pbs_dir / "pokemon.txt"
        save_all_species_to_pbs(pokemon_txt, self.species)

        moves_txt = pbs_dir / "moves.txt"
        save_moves_to_pbs(moves_txt, self.moves)

        items_txt = pbs_dir / "items.txt"
        save_items_to_pbs(items_txt, self.items)

        # re-fill the tms list
        tm_mapping: dict[str, TechnicalMachine] = {tm.move: tm for tm in self.tms}

        for poke in self.species:
            for tm in poke.raw_tms:
                tm_mapping[tm].pokemon.append(poke.internal_name)

            for tm in poke.raw_tutor_moves:
                tm_mapping[tm].pokemon.append(poke.internal_name)

        tm_txt = pbs_dir / "tm.txt"
        save_tms_to_pbs(tm_txt, self.tms)

    # == Helper methods == #
    def move_by_name(self, internal_name: str) -> Optional[PokemonMove]:
        """
        Finds a move by name, or None if no such move exists.
        """

        for move in self.moves:
            if move.internal_name == internal_name:
                return move

        return None
