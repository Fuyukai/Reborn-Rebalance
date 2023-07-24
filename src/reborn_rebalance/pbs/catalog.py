import types
from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from typing import Optional, Self

import attr
import tomlkit

from reborn_rebalance.pbs.move import PokemonMove
from reborn_rebalance.pbs.pokemon import PokemonEvolution, PokemonSpecies
from reborn_rebalance.pbs.raw.encounters import MapEncounters, parse_maps
from reborn_rebalance.pbs.raw.item import PokemonItem
from reborn_rebalance.pbs.raw.tm import TechnicalMachine, tm_number_for
from reborn_rebalance.pbs.serialisation import (
    load_all_species_from_pbs,
    load_all_species_from_toml,
    load_encounters_from_pbs,
    load_encounters_from_toml,
    load_items_from_pbs,
    load_items_from_toml,
    load_moves_from_pbs,
    load_moves_from_toml,
    load_tms_from_pbs,
    load_tms_from_toml,
    save_all_species_to_pbs,
    save_all_species_to_toml,
    save_encounters_to_toml,
    save_items_to_pbs,
    save_items_to_toml,
    save_moves_to_pbs,
    save_moves_to_toml,
    save_tms_to_pbs,
    save_tms_to_toml,
)


@attr.s(frozen=True, slots=True, kw_only=True)
class EvolutionaryChain:
    """
    A single chain of evolutions for a species.
    """

    #: What this Pokémon evolves from.
    evolves_from: PokemonSpecies | None = attr.ib()
    #: The evolution data for said evolution.
    evolves_from_evo: PokemonEvolution | None = attr.ib()

    #: What this Pokémon evolves into, in (species, evolution data) format.
    evolves_into: list[tuple[PokemonSpecies, PokemonEvolution]] = attr.ib()


@attr.s(slots=False, kw_only=True)
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

    #: The mapping of map IDs to map names.
    map_names: dict[int, str] = attr.ib()

    #: The mapping of encounters for map IDs to encounter data.
    encounters: dict[int, MapEncounters] = attr.ib()

    @cached_property
    def species_mapping(self) -> Mapping[str, PokemonSpecies]:
        return types.MappingProxyType({it.internal_name: it for it in self.species})

    @classmethod
    def load_from_pbs(cls, path: Path) -> Self:
        """
        Loads all objects from PBS files in the provided Reborn ``PBS`` directory.
        """

        pokemon_path = path / "pokemon.txt"
        all_species = load_all_species_from_pbs(pokemon_path)

        for idx, sp in enumerate(all_species):
            sp.dex_number = idx + 1

        moves_path = path / "moves.txt"
        moves = load_moves_from_pbs(moves_path)

        items_path = path / "items.txt"
        items = load_items_from_pbs(items_path)

        tm_path = path / "tm.txt"
        tms = load_tms_from_pbs(tm_path)

        # now, backfill in the TMs fields from tms and items
        # (this is saved in the actual toml)
        # use the display names
        tm_move_mapping: dict[str, PokemonMove] = {it.internal_name: it for it in moves}
        tm_item_mapping: dict[str, PokemonItem] = {
            it.move: it for it in items if it.display_name.startswith("TM")
        }
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
                    # naughty type nonsense
                    species.raw_tms.append(tm)  # type: ignore

            tm.pokemon.clear()

        for poke in all_species:
            poke.raw_tms = [it.move for it in sorted(poke.raw_tms, key=lambda it: it.number)]

        # 🍳
        map_file_path = (path / ".." / "Data" / "MapInfos.rxdata").absolute()
        map_data = parse_maps(map_file_path)

        encounter_path = path / "encounters.txt"
        encounter_data = load_encounters_from_pbs(encounter_path)

        return cls(
            species=all_species,
            moves=moves,
            items=items,
            tms=tms,
            map_names=map_data,
            encounters=encounter_data,
        )

    @classmethod
    def load_from_toml(cls, path: Path) -> Self:
        """
        Loads all objects from toml files in the provided ``data`` directory.
        """

        species_dir = path / "species"
        species = load_all_species_from_toml(species_dir)

        moves_file = path / "moves.toml"
        moves = load_moves_from_toml(moves_file)

        items_path = path / "items.toml"
        items = load_items_from_toml(items_path)

        tm_path = path / "tms.toml"
        tms = load_tms_from_toml(tm_path)

        maps_path = path / "map_names.toml"
        with maps_path.open(encoding="utf-8") as f:
            maps = {int(k): v for (k, v) in tomlkit.load(f).items()}

        encounters_path = path / "encounters"
        encounters = load_encounters_from_toml(encounters_path)

        return cls(
            species=species, moves=moves, items=items, tms=tms, map_names=maps,
            encounters=encounters,
        )

    def save_to_toml(self, path: Path):
        """
        Serialises all objects within this catalog to toml format.
        """

        path.mkdir(parents=True, exist_ok=True)

        species_path = path / "species"
        species_path.mkdir(parents=True, exist_ok=True)
        save_all_species_to_toml(species_path, self.species)

        moves_path = path / "moves.toml"
        save_moves_to_toml(moves_path, self.moves)

        items_path = path / "items.toml"
        save_items_to_toml(items_path, self.items)

        tms_path = path / "tms.toml"
        save_tms_to_toml(tms_path, self.tms)

        # practically speaking, this file will never change Reborn-side.
        # so we don't bother updating it.
        maps_path = path / "map_names.toml"
        if not maps_path.exists():
            with maps_path.open(mode="w", encoding="utf-8") as f:
                tomlkit.dump(
                    {str(k): v for (k, v) in sorted(self.map_names.items(), key=lambda it: it[0])},
                    f,
                )

        encounters_path = path / "encounters"
        encounters_path.mkdir(exist_ok=True, parents=True)
        save_encounters_to_toml(encounters_path, self.map_names, self.encounters)

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
                tm_mapping[tm].pokemon.add(poke.internal_name)

            for tm in poke.raw_tutor_moves:
                tm_mapping[tm].pokemon.add(poke.internal_name)

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

    def tm_id_for(self, tm_name: str) -> Optional[int]:
        """
        Finds a TM's number by its move's internal name.
        """

        for tm in self.tms:
            if tm.move == tm_name:
                return tm.number

        return None

    def item_loc_name(self, internal_name: str) -> str:
        """
        Gets an item's localised name from its internal name.
        """

        for item in self.items:
            if item.internal_name == internal_name:
                return item.display_name

        raise ValueError(f"no such item {internal_name}")

    def evolutionary_chain_for(self, species: PokemonSpecies) -> EvolutionaryChain | None:
        """
        Gets the evolutionary chain for this Pokémon.
        """

        before: PokemonSpecies | None = None
        before_evo: PokemonEvolution | None = None
        for poke in self.species:
            for evo in poke.evolutions:
                if evo.into_name == species.internal_name:
                    before_evo = evo
                    before = poke
                    break

        after = []
        for into in species.evolutions:
            after.append((self.species_mapping[into.into_name], into))

        if not (before or after):
            return None

        return EvolutionaryChain(
            evolves_from=before, evolves_from_evo=before_evo, evolves_into=after
        )
