import concurrent.futures
import time
import types
from collections import defaultdict
from collections.abc import Mapping
from functools import cached_property, partial
from pathlib import Path
from typing import Callable, Optional, Self, TypeVar

import attr

from reborn_rebalance.pbs.ability import PokemonAbility
from reborn_rebalance.pbs.encounters import ENCOUNTER_SLOTS, MapEncounters
from reborn_rebalance.pbs.form import PokemonForms, save_forms_to_ruby
from reborn_rebalance.pbs.item import PokemonItem
from reborn_rebalance.pbs.map import MapMetadata, parse_rpg_maker_mapinfo
from reborn_rebalance.pbs.move import PokemonMove
from reborn_rebalance.pbs.pokemon import (
    FormAttributes,
    PokemonEvolution,
    PokemonSpecies,
)
from reborn_rebalance.pbs.serialisation import (
    load_abilities_from_pbs,
    load_abilities_from_toml,
    load_all_forms,
    load_all_species_from_pbs,
    load_all_species_from_toml,
    load_encounters_from_pbs,
    load_encounters_from_toml,
    load_items_from_pbs,
    load_items_from_toml,
    load_map_metadata_from_pbs,
    load_map_metadata_from_toml,
    load_moves_from_pbs,
    load_moves_from_toml,
    load_tms_from_pbs,
    load_tms_from_toml,
    load_trainer_types_from_pbs,
    load_trainer_types_from_toml,
    load_trainers_from_pbs,
    load_trainers_from_toml,
    save_abilities_to_pbs,
    save_abilities_to_toml,
    save_all_species_to_pbs,
    save_all_species_to_toml,
    save_encounters_to_pbs,
    save_encounters_to_toml,
    save_items_to_pbs,
    save_items_to_toml,
    save_map_metadata_to_pbs,
    save_map_metadata_to_toml,
    save_moves_to_pbs,
    save_moves_to_toml,
    save_tms_to_pbs,
    save_tms_to_toml,
    save_trainer_types_to_pbs,
    save_trainer_types_to_toml,
    save_trainers_to_pbs,
    save_trainers_to_toml,
)
from reborn_rebalance.pbs.tm import TechnicalMachine, tm_number_for
from reborn_rebalance.pbs.trainer import TrainerCatalog, TrainerType

LoadWithPrintT = TypeVar("LoadWithPrintT")


def load_with_print(type_: str, fn: Callable[[], LoadWithPrintT]) -> LoadWithPrintT:
    """
    Loads the provided object, printing the time taken.
    """

    start = time.perf_counter()
    print(f"LOAD: {type_}...")

    result = fn()

    end = time.perf_counter()
    print(f"Loaded {type_} in {end - start:.2f}s")

    return result


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


@attr.s(frozen=False, slots=True)
class ExpandedEncounterEntry:
    """
    An expanded encounter entry for usage with templates.
    """

    #: The name of the Pokémon this entry is for.
    poke_name: str = attr.ib()

    #: The percentage chance this entry is for.
    chance: int = attr.ib()

    min_level: int = attr.ib()
    max_level: int = attr.ib()

    def update(self, chance: int, min_level: int, max_level: int):
        self.chance += chance
        assert self.chance <= 100, "eeeh?"

        self.min_level = min(min_level, self.min_level)
        self.max_level = max(max_level, self.max_level)


@attr.s(slots=False, kw_only=True)
class EssentialsCatalog:
    """
    Super-object that contains references to all of the data in the game.
    """

    #: The list of all known species.
    species: list[PokemonSpecies] = attr.ib()

    #: The mapping of all known {internal name -> list of forms}.
    forms: dict[str, PokemonForms] = attr.ib()

    #: The list of all known moves.
    moves: list[PokemonMove] = attr.ib()

    #: The list of all known items.
    items: list[PokemonItem] = attr.ib()

    #: The list of all known TMs.
    tms: list[TechnicalMachine] = attr.ib()

    #: The list of all known abilities.
    abilities: list[PokemonAbility] = attr.ib()

    #: The mapping of map IDs to map metadata.
    maps: dict[int, MapMetadata] = attr.ib()

    #: The mapping of encounters for map IDs to encounter data.
    encounters: dict[int, MapEncounters] = attr.ib()

    #: The mapping of trainer type name -> trainer type.
    trainer_types: dict[str, TrainerType] = attr.ib()

    #: The mapping of trainer name -> list of trainers.
    trainers: dict[str, TrainerCatalog] = attr.ib()

    @cached_property
    def species_mapping(self) -> Mapping[str, PokemonSpecies]:
        return types.MappingProxyType({it.internal_name: it for it in self.species})

    @cached_property
    def move_mapping(self) -> Mapping[str, PokemonMove]:
        return types.MappingProxyType({it.internal_name: it for it in self.moves})

    @cached_property
    def regular_tm_mapping(self) -> Mapping[int, TechnicalMachine]:
        return types.MappingProxyType(
            {it.number: it for it in self.tms if not (it.is_tmx or it.is_tutor)}
        )

    @cached_property
    def tm_name_mapping(self) -> Mapping[str, TechnicalMachine]:
        return types.MappingProxyType({it.move: it for it in self.tms})

    @cached_property
    def ability_name_mapping(self) -> Mapping[str, PokemonAbility]:
        return types.MappingProxyType({it.name: it for it in self.abilities})

    @cached_property
    def item_mapping(self) -> Mapping[str, PokemonItem]:
        return types.MappingProxyType({it.internal_name: it for it in self.items})

    @cached_property
    def pre_evolutionary_cache(self) -> Mapping[str, tuple[PokemonSpecies, PokemonEvolution]]:
        """
        Gets a mapping of (species -> (pre-evo species, pre-evolution)).
        """

        # luckily, there's no cases of multiple species eevolving into one pokemon.
        d = {}

        for species in self.species:
            for evo in species.evolutions:
                d[evo.into_name] = (species, evo)

        return types.MappingProxyType(d)

    @cached_property
    def species_to_encounter_map(self) -> Mapping[str, set[int]]:
        """
        A mapping of {species internal name: [map ID]} to avoid searching all maps repeatedly.
        """

        mapping = defaultdict(set)

        for map_id, info in self.encounters.items():
            for all_entries in info.encounters.values():
                for entry in all_entries:
                    mapping[entry.name].add(map_id)

        return types.MappingProxyType(mapping)

    def __attrs_post_init__(self):
        # apply children maps in a single pass.
        # if we didn't do this, we'd have to iterate over all maps to find backrefs on the parent_id
        # attribute, for every single map.
        for map in self.maps.values():
            if map.parent_id == 0:  # root map, skip
                continue

            parent = self.maps[map.parent_id]
            # has to use the id because map is unhashable.
            parent.child_maps.add(map.id)

    @classmethod
    def load_from_pbs(cls, path: Path) -> Self:
        """
        Loads all objects from PBS files in the provided Reborn ``PBS`` directory.
        """

        pbs_path = path / "PBS"

        pokemon_path = pbs_path / "pokemon.txt"
        all_species = load_all_species_from_pbs(pokemon_path)

        moves_path = pbs_path / "moves.txt"
        moves = load_moves_from_pbs(moves_path)

        items_path = pbs_path / "items.txt"
        items = load_items_from_pbs(items_path)

        tm_path = pbs_path / "tm.txt"
        tms = load_tms_from_pbs(tm_path)

        ability_path = pbs_path / "abilities.txt"
        abilities = load_abilities_from_pbs(ability_path)

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

        map_file_path = (path / "Data" / "MapInfos.rxdata").absolute()
        map_names = parse_rpg_maker_mapinfo(map_file_path)

        map_metadata = load_map_metadata_from_pbs(pbs_path / "metadata.txt")

        # backfill names into the map metadata, as the file only contains the map number.
        for info in map_metadata.values():
            raw_info = map_names.pop(info.id)

            info.name = raw_info.name
            info.parent_id = raw_info.parent_id

        # for the sake of my sanity just add the missing items in.
        for id, info in map_names.items():
            # fix up metadata for missing maps
            print("warning: missing metadata for", id, f"({info.name})")
            missing_metadata = MapMetadata(id=id, name=info.name, parent_id=info.parent_id)
            map_metadata[id] = missing_metadata

        encounter_path = pbs_path / "encounters.txt"
        encounter_data = load_encounters_from_pbs(encounter_path)

        trainer_type_path = pbs_path / "trainertypes.txt"
        trainer_type_data = load_trainer_types_from_pbs(trainer_type_path)

        trainers = pbs_path / "trainers.txt"
        trainers_data = load_trainers_from_pbs(trainers)

        return cls(
            species=all_species,
            forms={},
            moves=moves,
            items=items,
            tms=tms,
            abilities=abilities,
            maps=map_metadata,
            encounters=encounter_data,
            trainer_types=trainer_type_data,
            trainers=trainers_data,
        )

    @classmethod
    def load_only_species(cls, path: Path):
        """
        Loads only species and forms data. Does *no* validation.
        """

        species_dir = path / "species"
        forms_path = path / "forms"

        species = load_all_species_from_toml(species_dir)
        forms = load_all_forms(forms_path)

        return cls(
            species=species,
            forms=forms,
            moves=[],
            items=[],
            maps={},
            encounters={},
            abilities=[],
            tms=[],
            trainer_types={},
            trainers={},
        )

    @classmethod
    def load_from_toml(
        cls,
        path: Path,
        *,
        skip_species: bool = False,
    ) -> Self:
        """
        Loads all objects from toml files in the provided ``data`` directory.
        """

        # processpoolexecutor over threadpoolexecutor cos this is mostly cpu bound tomli stuff

        before = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            moves_file = path / "moves.toml"
            load_moves = partial(load_moves_from_toml, moves_file)
            moves_fut = executor.submit(load_with_print, "moves", load_moves)

            items_path = path / "items.toml"
            load_items = partial(load_items_from_toml, items_path)
            items_fut = executor.submit(load_with_print, "items", load_items)

            tm_path = path / "tms.toml"
            load_tms = partial(load_tms_from_toml, tm_path)
            tms_fut = executor.submit(load_with_print, "tms", load_tms)

            ability_path = path / "abilities.toml"
            load_abilities = partial(load_abilities_from_toml, ability_path)
            abilities_fut = executor.submit(load_with_print, "abilities", load_abilities)

            map_metadata_path = path / "maps.toml"
            load_map_metadata = partial(load_map_metadata_from_toml, map_metadata_path)
            map_metadata_fut = executor.submit(load_with_print, "map metadata", load_map_metadata)

            trainer_types_path = path / "trainer_types.toml"
            load_trainer_types = partial(load_trainer_types_from_toml, trainer_types_path)
            trainer_types_fut = executor.submit(
                load_with_print, "trainer types", load_trainer_types
            )

        after = time.perf_counter()
        print(f"Loaded all non-species data in {after - before:.2f}s")

        species_dir = path / "species"
        forms_path = path / "forms"

        before = time.perf_counter()
        if skip_species:
            species = []
            forms = {}
        else:
            species = load_all_species_from_toml(species_dir)
            forms = load_all_forms(forms_path)

        encounters_path = path / "encounters"
        trainers_path = path / "trainers"
        encounters = load_encounters_from_toml(encounters_path)
        trainers = load_trainers_from_toml(trainers_path)
        after = time.perf_counter()

        print(f"Loaded species, forms, encounters, and trainers in {after - before:.2f}s")

        instance = cls(
            species=species,
            forms=forms,
            moves=moves_fut.result(),
            items=items_fut.result(),
            tms=tms_fut.result(),
            abilities=abilities_fut.result(),
            maps=map_metadata_fut.result(),
            encounters=encounters,
            trainer_types=trainer_types_fut.result(),
            trainers=trainers,
        )

        instance._validate()
        print("loaded and validated catalog")
        return instance

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

        abilities_path = path / "abilities.toml"
        save_abilities_to_toml(abilities_path, self.abilities)

        maps_path = path / "maps.toml"
        save_map_metadata_to_toml(maps_path, self.maps)

        encounters_path = path / "encounters"
        encounters_path.mkdir(exist_ok=True, parents=True)
        save_encounters_to_toml(encounters_path, self.maps, self.encounters)

        trainer_types_path = path / "trainer_types.toml"
        save_trainer_types_to_toml(trainer_types_path, self.trainer_types)

        trainers_path = path / "trainers"
        trainers_path.mkdir(parents=True, exist_ok=True)
        save_trainers_to_toml(trainers_path, self.trainers)

    def save_to_essentials(self, output_dir: Path):
        """
        Saves this catalog into the format ready for Essentials ingestion.
        """

        pbs_dir = output_dir / "PBS"
        pbs_dir.mkdir(parents=True, exist_ok=True)

        scripts_dir = output_dir / "Scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        pokemon_txt = pbs_dir / "pokemon.txt"
        save_all_species_to_pbs(pokemon_txt, self.species)

        moves_txt = pbs_dir / "moves.txt"
        save_moves_to_pbs(moves_txt, self.moves)

        items_txt = pbs_dir / "items.txt"
        save_items_to_pbs(items_txt, self.items)

        for poke in self.species:
            for tm in poke.raw_tms:
                self.tm_name_mapping[tm].pokemon.add(poke.internal_name)

            for tm in poke.raw_tutor_moves:
                self.tm_name_mapping[tm].pokemon.add(poke.internal_name)

        tm_txt = pbs_dir / "tm.txt"
        save_tms_to_pbs(tm_txt, self.tms)

        ability_txt = pbs_dir / "abilities.txt"
        save_abilities_to_pbs(ability_txt, self.abilities)

        encounters_txt = pbs_dir / "encounters.txt"
        save_encounters_to_pbs(encounters_txt, self.encounters)

        map_metadata_txt = pbs_dir / "metadata.txt"
        save_map_metadata_to_pbs(map_metadata_txt, self.maps)

        trainer_types_txt = pbs_dir / "trainertypes.txt"
        save_trainer_types_to_pbs(trainer_types_txt, self.trainer_types)

        trainers_txt = pbs_dir / "trainers.txt"
        save_trainers_to_pbs(trainers_txt, self.trainers)

        forms_file = scripts_dir / "MultipleForms.rb"
        save_forms_to_ruby(forms_file, self.forms)

    def _validate(self):
        for species in self.species:
            errors = []

            for _, _, attrs in self.all_forms_for(species):
                for tm in species.raw_tms:
                    if tm not in self.tm_name_mapping:
                        errors.append(
                            ValueError(f"no such TM: {tm} / when validating {attrs.internal_name}")
                        )

                for move in species.raw_level_up_moves:
                    if move.name not in self.move_mapping:
                        errors.append(
                            ValueError(
                                f"no such move: {move.name} / when validating {attrs.internal_name}"
                            )
                        )

                for ability in species.raw_abilities:
                    if ability not in self.ability_name_mapping:
                        errors.append(
                            ValueError(
                                f"no such ability: {ability} / when validating"
                                f" {attrs.internal_name}"
                            )
                        )

            if errors:
                raise ExceptionGroup(f"Validation error for {species.name}", errors)

        for form_key, form in self.forms.items():
            errors = []

            if ferr := form._validate():
                errors.append(ferr)

            if form_key not in self.species_mapping:
                errors.append(ValueError(f"Form for non-existent Pokémon '{form_key}'"))

            if errors:
                raise ExceptionGroup(f"Validation error for forms", errors)

    # == Helper methods == #
    def get_attribs_for_form(
        self, species_name: str | PokemonSpecies, form_idx: int
    ) -> FormAttributes:
        """
        Gets the attributes for the specified form idx of the provided Pokémon species.
        """

        if isinstance(species_name, PokemonSpecies):
            root_species = species_name
        else:
            root_species = self.species_mapping[species_name]

        if (forms := self.forms.get(root_species.internal_name)) is None:
            return root_species.default_attributes

        if forms.default_form == form_idx:
            return root_species.default_attributes

        form_name = forms.form_mapping[form_idx]
        return forms.forms[form_name].combined_attributes(root_species)

    def all_forms_for(
        self, species_name: str | PokemonSpecies
    ) -> list[tuple[int, str, FormAttributes]]:
        """
        Gets all of the forms for the provided species.
        """

        if isinstance(species_name, PokemonSpecies):
            root_species = species_name
        else:
            root_species = self.species_mapping[species_name]

        if (forms := self.forms.get(root_species.internal_name)) is None:
            return [(0, "Normal", root_species.default_attributes)]

        items: list[tuple[int, str, FormAttributes]] = []

        # make sure all multi-form species with no zero-form existing (i.e. most of them) have
        # the default attributes.
        # some pokes have the zero-form explicit, like zama and zacian.
        if 0 not in forms.form_mapping:
            items.append((0, "Normal", root_species.default_attributes))

        for idx, name in forms.form_mapping.items():
            try:
                form = forms.forms[name]
            except KeyError:
                # visual-only form.
                items.append((idx, name, root_species.default_attributes.renamed(name)))
            else:
                items.append((idx, name, form.combined_attributes(root_species)))

        return items

    def move_by_name(self, internal_name: str) -> Optional[PokemonMove]:
        """
        Finds a move by name, or None if no such move exists.
        """

        for move in self.moves:
            if move.internal_name == internal_name:
                return move

        return None

    def move_by_display_name(self, display_name: str) -> Optional[PokemonMove]:
        """
        Finds a move by display name, or None if no such move exists.
        """

        for move in self.moves:
            if move.display_name == display_name:
                return move

        return None

    def tm_id_for(self, tm_name: str) -> Optional[int]:
        """
        Finds a TM's number by its move's internal name.
        """

        try:
            return self.tm_name_mapping[tm_name].number
        except KeyError:
            return None

    def tm_move_for(self, id: int) -> PokemonMove:
        """
        Finds a TM's name by number.
        """

        move_name = self.regular_tm_mapping[id].move
        return self.move_mapping[move_name]

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
        before, before_evo = self.pre_evolutionary_cache.get(species.internal_name, (None, None))

        after = []
        for into in species.evolutions:
            after.append((self.species_mapping[into.into_name], into))

        if not (before or after):
            return None

        return EvolutionaryChain(
            evolves_from=before, evolves_from_evo=before_evo, evolves_into=after
        )

    def encounters_for(
        self, species: PokemonSpecies
    ) -> dict[int, dict[str, ExpandedEncounterEntry]]:
        """
        Gets a list of encounters for the provided Pokémon, and their chances.
        """

        # map id -> {encounter type -> chance}
        found_encounters: dict[int, dict[str, ExpandedEncounterEntry]] = {}

        # 3 nested loops! 3 nested loops!
        for map_id in self.species_to_encounter_map[species.internal_name]:
            info = self.encounters[map_id]

            for ec_type, all_entries in info.encounters.items():
                slots = ENCOUNTER_SLOTS[ec_type]

                for slot_idx, entry in enumerate(all_entries):
                    # oh god, five levels of indentation
                    if entry.name != species.internal_name:
                        continue

                    subdict = found_encounters.setdefault(map_id, {})
                    chance = slots[slot_idx]

                    # make sure percentages are added up (lol?)
                    # it's what the wiki does...
                    if ec_type in subdict:
                        subdict[ec_type].update(
                            chance=chance,
                            min_level=entry.minimum_level,
                            max_level=entry.maximum_level,
                        )
                    else:
                        subdict[ec_type] = ExpandedEncounterEntry(
                            poke_name=species.internal_name,
                            chance=chance,
                            min_level=entry.minimum_level,
                            max_level=entry.maximum_level,
                        )

        return found_encounters

    def get_map_chain_for(self, map: MapMetadata) -> list[MapMetadata]:
        """
        Gets the map chain for the provided map.
        """

        chain = [map]

        while True:
            next_parent_id = chain[-1].parent_id
            if next_parent_id == 0:
                break

            next_parent = self.maps[next_parent_id]
            chain.append(next_parent)

        return chain
