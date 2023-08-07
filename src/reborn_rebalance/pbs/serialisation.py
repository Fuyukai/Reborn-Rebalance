from __future__ import annotations

import concurrent.futures
import csv
from concurrent.futures import Future
from io import StringIO
from pathlib import Path

import cattrs
from rtoml import load
from tomli_w import dump

from reborn_rebalance.pbs.ability import PokemonAbility
from reborn_rebalance.pbs.encounters import EncounterParser, MapEncounters
from reborn_rebalance.pbs.form import PokemonForms, SinglePokemonForm
from reborn_rebalance.pbs.item import PokemonItem
from reborn_rebalance.pbs.map import MAP_DATA_HEADER, MapMetadata
from reborn_rebalance.pbs.move import MoveCategory, MoveFlag, MoveTarget, PokemonMove
from reborn_rebalance.pbs.pokemon import EggGroup, GrowthRate, PokemonSpecies, SexRatio
from reborn_rebalance.pbs.raw.kv import raw_parse_kv
from reborn_rebalance.pbs.tm import TechnicalMachine
from reborn_rebalance.pbs.trainer import (
    SingleTrainerPokemon,
    Trainer,
    TrainerCatalog,
    TrainerType,
)
from reborn_rebalance.pbs.type import PokemonType
from reborn_rebalance.util import PbsBuffer, StupidFuckingIterationWrapper, chunks

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


def generation_for(dex_number: int) -> int:
    for gen, range in enumerate(GENERATIONS):
        if dex_number in range:
            return gen

    raise ValueError(dex_number)


def create_cattrs_converter() -> cattrs.Converter:
    converter = cattrs.Converter(forbid_extra_keys=True)

    # dump enums via name rather than by value
    for enum in (
        PokemonType,
        EggGroup,
        SexRatio,
        GrowthRate,
        MoveCategory,
        MoveTarget,
        MoveFlag,
    ):
        converter.register_structure_hook(enum, lambda name, klass: klass[name])
        converter.register_unstructure_hook(enum, lambda it: it.name)

    TechnicalMachine.add_unstructuring_hook(converter)
    PokemonSpecies.add_unstructuring_hook(converter)
    PokemonItem.add_unstructuring_hook(converter)
    PokemonForms.add_unstructure_hook(converter)
    SinglePokemonForm.add_unstructure_hook(converter)
    MapMetadata.add_unstructure_hook(converter)
    TrainerType.add_unstructure_hook(converter)
    SingleTrainerPokemon.add_unstructure_hook(converter)
    Trainer.add_unstructure_hook(converter)
    TrainerCatalog.add_unstructure_hook(converter)

    return converter


CONVERTER = create_cattrs_converter()


def load_single_species_toml(path: Path) -> (int, PokemonSpecies):
    """
    Loads a single species from the provided TOML file.

    :return A tuple of (dex number, parsed species).
    """

    print(f"LOAD: {path}")

    with path.open(encoding="utf-8", mode="r") as f:
        data = load(f)

    idx = int(path.name.split("-", 1)[0])

    return idx, CONVERTER.structure(data, PokemonSpecies)


def load_all_species_from_pbs(path: Path) -> list[PokemonSpecies]:
    """
    Loads all Pokémon species from the provided PBS file.
    """

    raw_data = raw_parse_kv(path)
    return [PokemonSpecies.from_pbs(key, it) for key, it in raw_data.items()]


def load_all_species_from_toml(path: Path) -> list[PokemonSpecies]:
    """
    Loads all species from the TOML directory, and returns them in Pokédex order.
    """

    to_read: list[Path] = []

    for f in path.rglob("*"):
        if f.is_dir():
            continue

        to_read.append(f)

    species: list[PokemonSpecies] = [None] * len(to_read)  # type: ignore

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for idx, decoded in executor.map(load_single_species_toml, to_read):
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


def save_single_species_to_toml(output_path: Path, species: PokemonSpecies):
    """
    Saves a single species to a TOML file.
    """

    output = CONVERTER.unstructure(species)

    with output_path.open(mode="wb") as f:
        dump(output, f)


def save_all_species_to_toml(output_path: Path, input_pokemon: list[PokemonSpecies]):
    """
    Saves all species to the provided ``output_path`` in TOML format, divided by generation.
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
        toml_path = (output_path / f"gen_{gidx + 1}" / name).with_suffix(".toml")

        if toml_path.exists():
            print(f"Not overwriting {name}")
            continue

        save_single_species_to_toml(toml_path, species)
        print(f"Saved {name}")


def load_single_form(path: Path) -> PokemonForms:
    """
    Loads a single form from the provided path.
    """

    print(f"LOAD (form): {path}")
    with path.open(mode="r", encoding="utf-8") as f:
        forms_for_mon = load(f)

    if "internal_name" not in forms_for_mon:
        name = path.stem
        forms_for_mon["internal_name"] = name.upper()

    forms_for_mon = CONVERTER.structure(forms_for_mon, PokemonForms)

    # backfill in form name. why did I type this into 100 files manually? im gonna kill myself.
    for name, form in forms_for_mon.forms.items():
        form.form_name = name

    return forms_for_mon


def load_all_forms(path: Path) -> dict[str, PokemonForms]:
    """
    Loads all forms from the provided path.
    """

    all_forms = {}
    to_load: list[Path] = []

    for subfile in path.glob("**/*"):
        if subfile.is_dir():
            continue

        if subfile.suffix != ".toml":
            continue

        to_load.append(subfile)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for forms in executor.map(load_single_form, to_load):
            all_forms[forms.internal_name] = forms

    return all_forms


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


def load_moves_from_toml(path: Path) -> list[PokemonMove]:
    """
    Loads all moves from the providied ``moves.TOML`` file.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = load(f)["moves"]

    moves: list[PokemonMove] = []
    for move in data:
        moves.append(CONVERTER.structure(move, PokemonMove))

    return moves


def save_moves_to_toml(path: Path, moves: list[PokemonMove]):
    """
    Saves all moves to disk in the TOML format.
    """

    if path.exists():
        print(f"Not overwriting: {path}")
        return

    moves = sorted(moves, key=lambda it: it.id)

    output = {"moves": CONVERTER.unstructure(moves)}

    with path.open(mode="wb") as f:
        dump(output, f)


def save_moves_to_pbs(path: Path, moves: list[PokemonMove]):
    """
    Saves all moves to PBS format (CSV) instead.
    """

    moves = sorted(moves, key=lambda it: it.id)

    with path.open(mode="w", encoding="utf-8") as f:
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


def load_items_from_toml(path: Path) -> list[PokemonItem]:
    """
    Loads all items from the provided ``items.TOML`` file.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = load(f)["items"]

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


def save_items_to_toml(path: Path, items: list[PokemonItem]):
    """
    Saves all items to TOML format.
    """

    if path.exists():
        print(f"Not overwriting: {path}")
        return

    items = sorted(items, key=lambda it: it.id)
    output = {"items": CONVERTER.unstructure(items)}

    with path.open(mode="wb") as f:
        dump(output, f)


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

        for line in lines:
            try:
                move, pokemon = line
            except ValueError:
                print(f"warning: bad line {line[0]}")
                continue

            move = move[1:-1]
            pokemon = pokemon.split(",")
            tms.append(TechnicalMachine.incomplete_from_pbs(move, pokemon))

    return tms


def load_tms_from_toml(path: Path) -> list[TechnicalMachine]:
    """
    Loads all TMs from the provided ``technical_machines.TOML`` file.

    This produces full, complete TM objects.
    """

    tms: list[TechnicalMachine] = []

    with path.open(encoding="utf-8", mode="r") as f:
        data = load(f)
        real_data = data["tm"] + data["tutor"]

        for tm in real_data:
            tms.append(CONVERTER.structure(tm, TechnicalMachine))

    return tms


def save_tms_to_toml(path: Path, tms: list[TechnicalMachine]):
    """
    Saves all TMs in TOML format.
    """

    if path.exists():
        print(f"Not overwriting: {path}")
        return

    real_dict = {
        "tm": sorted([it for it in tms if not it.is_tutor], key=lambda it: it.number),
        "tutor": sorted([it for it in tms if it.is_tutor], key=lambda it: it.move),
    }

    output = CONVERTER.unstructure(real_dict)

    with path.open(mode="wb") as f:
        dump(output, f)


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


def load_abilities_from_pbs(path: Path) -> list[PokemonAbility]:
    """
    Loads all abilities from PBS format.
    """

    with path.open(mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        abilities = [PokemonAbility.from_pbs(it) for it in reader]

    return abilities


def load_abilities_from_toml(path: Path) -> list[PokemonAbility]:
    """
    Loads all abilities from TOML format.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = load(f)["abilities"]

    abilities: list[PokemonAbility] = []
    for ability in data:
        abilities.append(CONVERTER.structure(ability, PokemonAbility))

    return abilities


def save_abilities_to_pbs(path: Path, abilities: list[PokemonAbility]):
    """
    Saves all abilities into the PBS (CSV) format.
    """

    with path.open(mode="w", encoding="utf-8") as f:
        writer = csv.writer(f)

        for ability in sorted(abilities, key=lambda it: it.id):
            writer.writerow(ability.to_pbs())


def save_abilities_to_toml(path: Path, abilities: list[PokemonAbility]):
    """
    Saves all abilities into the TOML format.
    """

    if path.exists():
        print(f"Not overwriting: {path}")
        return

    output = {"abilities": CONVERTER.unstructure(abilities)}

    with path.open(mode="wb") as f:
        dump(output, f)


def load_encounters_from_pbs(path: Path) -> dict[int, MapEncounters]:
    """
    Loads the encounters data from the ``encounters.txt`` file.
    """

    parser = EncounterParser(path)
    return parser.parse()


def load_single_encounter(path: Path) -> tuple[int, MapEncounters]:
    """
    Loads a single encounter from the provided path.
    """

    print(f"LOAD (Encounter): {path}")
    id = int(path.name.split("_", 1)[0])

    with path.open(mode="r", encoding="utf-8") as f:
        data = load(f)

    encounter = CONVERTER.structure(data, MapEncounters)
    return id, encounter


def load_encounters_from_toml(path: Path) -> dict[int, MapEncounters]:
    """
    Loads the encounters data from the ``encounters.toml`` file.
    """

    encounters = {}
    futures: list[Future[tuple[int, MapEncounters]]] = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for file in path.rglob("*"):
            if file.is_dir():
                continue

            if file.suffix != ".toml":
                continue

            futures.append(executor.submit(load_single_encounter, file))

    for fut in futures:
        id, encounter = fut.result()
        encounters[id] = encounter

    return encounters


def save_encounters_to_pbs(path: Path, data: dict[int, MapEncounters]):
    """
    Saves the encounters data to PBS format.
    """

    with path.open(mode="w", encoding="utf-8") as f:
        # aaaaaaaaahHHHH

        sorted_encounters = sorted(data.items(), key=lambda it: it[0])

        for map_id, map_data in sorted_encounters:
            # no clue if this is needed!
            f.write("#########################\n")
            f.write(f"{map_id:03d}\n")
            map_data.write_out(f)


def save_encounters_to_toml(
    path: Path, maps: dict[int, MapMetadata], data: dict[int, MapEncounters]
):
    """
    Saves the encounters data to TOML.
    """

    if path.exists():
        print(f"Not overwriting: {path}")
        return

    for idx, encounter in data.items():
        # there's two removed areas still in the default encounters data
        # removed map 107, which is an old version of... the pulse tangrowth forest in obsidia.
        # notably, this has a few actual NPCs, a really old tangrowth sprite (?), and it segfaults
        # mkxp-z. fun!
        # the other removed map 550, which appears to be an unfinished "new" rhidochrine jungle.
        # in the final game, the old rhidochrine jungle is always accessiblee from beryl ward
        # instead.
        # we skip those as there's no way to get there without save editing.

        try:
            info = maps[idx]
            name = info.name
        except IndexError:
            print(f"skipping encounter for removed map '{idx}'")
            continue

        if name == "REMOVED":
            print(f"skipping encounter for removed map '{idx}'")
            continue

        filename = path / f"{idx:03d}_{name.lower().replace(' ', '_')}.toml"
        if filename.exists():
            continue

        with filename.open(mode="wb") as f:
            dump(CONVERTER.unstructure(encounter), f)


def load_map_metadata_from_pbs(path: Path) -> dict[int, MapMetadata]:
    """
    Loads all map metadata from the PBS files.
    """

    raw_data = raw_parse_kv(path)
    raw_data.pop(0)

    return {id: MapMetadata.from_pbs(id, line) for id, line in raw_data.items()}


def load_map_metadata_from_toml(path: Path) -> dict[int, MapMetadata]:
    """
    Loads all map metadata from the TOML file.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = load(f)["maps"]

    maps: dict[int, MapMetadata] = {}
    for s_idx, raw_map in data.items():
        maps[int(s_idx)] = CONVERTER.structure(raw_map, MapMetadata)

    return maps


def save_map_metadata_to_pbs(path: Path, maps: dict[int, MapMetadata]):
    """
    Saves all map metadata to PBS format.
    """

    buffer = PbsBuffer()

    with path.open(mode="w", encoding="utf-8") as f:
        buffer.backing.write(MAP_DATA_HEADER)

        s_maps: list[MapMetadata] = sorted(maps.values(), key=lambda it: it.id)
        for meta in s_maps:
            buffer.write_id_header(f"{meta.id:03d}")
            meta.to_pbs(buffer)

        f.write(buffer.backing.getvalue())


def save_map_metadata_to_toml(path: Path, maps: dict[int, MapMetadata]):
    """
    Saves all map metadata to TOML format.
    """

    if path.exists():
        print(f"Not overwriting: {path}")
        return

    actual_data = {str(k): v for (k, v) in CONVERTER.unstructure(maps).items()}
    output = {"maps": actual_data}

    with path.open(mode="wb") as f:
        dump(output, f)


def load_trainer_types_from_pbs(path: Path) -> dict[int, TrainerType]:
    """
    Loads all trainer types from PBS.
    """

    with path.open(mode="r", encoding="utf-8") as f:
        reader = csv.reader(row for row in f if not row.startswith("#"))
        types = [TrainerType.from_csv_row(it) for it in reader]

    return {it.id: it for it in types}


def load_trainer_types_from_toml(path: Path) -> dict[int, TrainerType]:
    """
    Loads all trainer types from TOML.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        data = load(f)["trainer_types"]

    types: dict[int, TrainerType] = {}
    for s_idx, raw_type in data.items():
        types[int(s_idx)] = CONVERTER.structure(raw_type, TrainerType)

    return types


def save_trainer_types_to_pbs(path: Path, types: dict[int, TrainerType]):
    """
    Saves all trainer types to PBS.
    """

    with path.open(mode="w", encoding="utf-8") as f:
        f.write("# This file is automatically generated. Do not edit!\n")
        writer = csv.writer(f)

        for type in sorted(types.values(), key=lambda it: it.id):
            writer.writerow(type.into_csv_row())


def save_trainer_types_to_toml(path: Path, types: dict[int, TrainerType]):
    """
    Saves all trainer types to TOML.
    """

    if path.exists():
        print(f"Not overwriting: {path}")
        return

    output = {"trainer_types": CONVERTER.unstructure(types)}

    with path.open(mode="wb") as f:
        dump(output, f)


def load_single_trainer_file_toml(path: Path) -> tuple[str, dict[str, dict[int, Trainer]]]:
    """
    Loads a single trainer file from TOML.
    """

    with path.open(encoding="utf-8", mode="r") as f:
        print(f"LOAD (Trainer): {path}")
        data = load(f)["trainers"]

    trainers: dict[str, dict[int, Trainer]] = {}

    # skip keys for both, the data is duplicated on the table object itself anyway.
    for all_values in data.values():
        for trainer in all_values.values():
            trainer_obb = CONVERTER.structure(trainer, Trainer)
            by_battler_id = trainers.setdefault(trainer_obb.raw_trainer_class, {})
            by_battler_id[trainer_obb.battler_id] = trainer_obb

    return path.stem, trainers


def load_trainers_from_toml(path: Path) -> dict[str, TrainerCatalog]:
    """
    Loads all trainers from TOML.
    """

    trainers: dict[str, TrainerCatalog] = {}
    # yikes!
    futures: list[Future[tuple[str, dict[str, dict[int, Trainer]]]]] = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for file in path.rglob("*"):
            if file.is_dir():
                continue

            if file.suffix != ".toml":
                continue

            fut = executor.submit(load_single_trainer_file_toml, file)
            futures.append(fut)

    for fut in futures:
        name, mapping = fut.result()
        catalog = TrainerCatalog(trainer_name=name, trainers=mapping)
        trainers[name] = catalog

    return trainers


def load_trainers_from_pbs(path: Path) -> dict[str, TrainerCatalog]:
    """
    Loads all trainers from PBS.
    """

    # turns out trainer names aren't the sole key. yay!

    catalogs: dict[str, TrainerCatalog] = {}

    with path.open(mode="r", encoding="utf-8") as f:
        # because there are *commented out lines* in the middle of entries.
        line_iterator = StupidFuckingIterationWrapper(f)

        while True:
            try:
                next_line = next(line_iterator)
            except StopIteration:
                break

            if next_line.startswith("#"):
                continue

            trainer_obb = Trainer.from_single_section(next_line, line_iterator)
            if (chosen_cat := catalogs.get(trainer_obb.battler_name)) is None:
                chosen_cat = TrainerCatalog(trainer_name=trainer_obb.battler_name)
                catalogs[trainer_obb.battler_name] = chosen_cat

            trainer_mapping = chosen_cat.trainers.setdefault(trainer_obb.raw_trainer_class, {})
            trainer_mapping[trainer_obb.battler_id] = trainer_obb

    return catalogs


def save_trainers_to_toml(path: Path, trainers: dict[str, TrainerCatalog]):
    """
    Saves all trainer data to TOML files.
    """

    existing_files = path.glob("**/*")
    existing_names = {i.stem: i for i in existing_files if not i.is_dir() and i.suffix == ".toml"}

    for key, catalog in trainers.items():
        key = key.replace(".", "_")
        toml_path = (path / key).with_suffix(".toml")

        if key in existing_names:
            toml_path = existing_names[key]
            print("Not overwriting", toml_path)
            continue

        raw_data = CONVERTER.unstructure(catalog)

        with toml_path.open(mode="wb") as f:
            dump(raw_data, f)


def save_trainers_to_pbs(path: Path, trainers: dict[str, TrainerCatalog]):
    """
    Saves all trainer data to the PBS file.
    """

    # yikes
    buffer = StringIO()

    for klass, catalog in trainers.items():
        for trainer in catalog.all_trainers():
            buffer.write("#-------------------\n")
            trainer.into_pbs(buffer)

    path.write_text(buffer.getvalue(), encoding="utf-8")


def load_map_names(path: Path) -> dict[int, str]:
    """
    Loads the map names from TOML.
    """

    with path.open(encoding="utf-8") as f:
        return {int(k): v for (k, v) in load(f).items()}
