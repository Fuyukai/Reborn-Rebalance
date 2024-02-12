from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from functools import partial
from io import StringIO

import attr
import cattrs.gen
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn, override

from reborn_rebalance.pbs.pokemon import StatWrapper
from reborn_rebalance.util import get_safely


@attr.s(slots=True, kw_only=True)
class TrainerType:
    """
    A single trainer type.
    """

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        unst_hook = make_dict_unstructure_fn(
            cls,
            converter,
            _cattrs_omit_if_default=True,
        )
        converter.register_unstructure_hook(cls, unst_hook)

    #: The ID for this trainer type. Corresponds to the trainer images in the Graphics directory.
    id: int = attr.ib()

    #: The internal name for this trainer type.
    internal_name: str = attr.ib()

    #: The prefix for this trainer type, e.g. 'Agent'. Shown in game.
    name_prefix: str = attr.ib()

    #: The money this trainer gives out per level.
    money_per_level: int = attr.ib()

    #: The custom BGM for this trainer type, or None if there is no custom BGM.
    bgm: str | None = attr.ib(default=None)

    #: The custom ending sound effect, or None if there is none.
    end_sfx: str | None = attr.ib(default=None)

    #: The custom intro sfx, or None if there is none.
    intro_sfx: str | None = attr.ib(default=None)

    #: The gender (?) of this trainer type.
    gender: str = attr.ib(default="Mixed")

    #: The skill level (?) for this trainer.
    skill_level: int | None = attr.ib(default=None)

    @classmethod
    def from_csv_row(cls, row: list[str]) -> TrainerType:
        """
        Parses a single trainer type from a CSV row.
        """

        id = int(row[0])
        internal_name = row[1]
        name_prefix = row[2]
        money_per_level = int(row[3])
        bgm = row[4] or None
        end_sfx = row[5] or None
        intro_sfx = row[6] or None
        gender = row[7]
        try:
            skill_level = int(row[8])
        except ValueError:
            # missing :yert:
            skill_level = None

        return cls(
            id=id,
            internal_name=internal_name,
            name_prefix=name_prefix,
            money_per_level=money_per_level,
            bgm=bgm,
            end_sfx=end_sfx,
            intro_sfx=intro_sfx,
            gender=gender,
            skill_level=skill_level,
        )

    def into_csv_row(self) -> list[str]:
        """
        Writes this trainer type to a CSV row.
        """

        return [
            str(self.id),
            self.internal_name,
            self.name_prefix,
            str(self.money_per_level),
            self.bgm or "",
            self.end_sfx or "",
            self.intro_sfx or "",
            self.gender,
            str(self.skill_level) if self.skill_level is not None else "",
        ]


@attr.s(slots=True, kw_only=True)
class SingleTrainerPokemon:
    """
    A single Pokémon that a trainer can have.
    """

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        converter.register_unstructure_hook(
            SingleTrainerPokemon,
            make_dict_unstructure_fn(
                SingleTrainerPokemon,
                converter,
                nickname=override(omit_if_default=True),
                _cattrs_omit_if_default=True,
            ),
        )

    @staticmethod
    def validate_raw_moves(it: tuple):
        if len(it) != 4:
            raise ValueError(f"Expected 4 moves, but got ${it}")

    #: The internal species name for this Pokémon.
    internal_name: str = attr.ib()

    #: The level for this Pokémon.
    level: int = attr.ib()

    #: The item this Pokémon is holding, if any.
    raw_item: str | None = attr.ib(default=None)

    #: The four moves this Pokémon has.
    raw_moves: tuple[str, ...] = attr.ib(factory=tuple)

    #: The ability number this Pokémon has.
    ability_number: int = attr.ib(default=0)

    #: The sex of this Pokémon.
    sex: str = attr.ib(default="M")

    #: The form number of this Pokémon.
    form_number: int = attr.ib(default=0)

    #: If this Pokémon is shiny or not.
    is_shiny: bool = attr.ib(default=False)

    #: The nature of this Pokémon. If none, is a neutral nature (Hardy). Cue terrible joke.
    nature: str = attr.ib(default="HARDY")

    #: The IV that all of this Pokémon's stats will be set to, e.g. 31. Defaults to 10.
    iv: int = attr.ib(default=10)

    #: The happiness for this Pokémon. Only affects Return/Frustration.
    happiness: int = attr.ib(default=70)

    #: The nickname for this Pokémon.
    nickname: str | None = attr.ib(default=None)

    #: Ignored.
    shadow: bool = attr.ib(default=False)

    #: The Pokéball number this Pokémon is in.
    pokeball_type: int = attr.ib(default=0)

    #: The EVs for this Pokémon.
    evs: StatWrapper | None = attr.ib(default=None)

    @classmethod
    def from_csv_line(cls, line: list[str]):
        """
        Creates a new single trainer Pokémon from a single CSV line.
        """

        # im gonna actually kill whoever made these parameters optional.
        pokemon_name = line[0]
        level = int(line[1])

        try:
            item = line[2]
        except IndexError:
            item = None

        if not item:
            item = None

        moves = []
        for name_idx in range(4):
            real_idx = 3 + name_idx
            if (len(line) > real_idx) and (move := line[real_idx]):
                moves.append(move)

        try:
            ability_number = int(line[7])
        except (IndexError, ValueError):
            # aaaaaa
            ability_number = 0

        sex = get_safely(line, 8, "M")
        try:
            form_number = int(line[9])
        except (ValueError, IndexError):
            # again, what?
            form_number = 0

        # all the following are just f-ing not there sometimes???
        is_shiny = get_safely(line, 10, "false").lower() == "true"
        nature = get_safely(line, 11, "HARDY")

        try:
            iv = int(line[12])
        except (IndexError, ValueError):
            iv = 0

        try:
            happiness = int(line[13])
        except (IndexError, ValueError):
            happiness = 70

        nickname = get_safely(line, 14, "").strip()
        if not nickname:
            nickname = None

        # always false, practically
        shadow = get_safely(line, 15, "false").lower() == "true"
        try:
            pokeball_type = int(line[16])
        except (ValueError, IndexError):
            pokeball_type = 0

        # weh, evs are optional and not all of them have to be there
        # yay for slices
        ev_slice = line[17:23]
        ev_slice = [it if it else "0" for it in ev_slice]
        if not ev_slice:
            evs = StatWrapper.empty()
        else:
            evs = StatWrapper.from_incomplete_list(ev_slice)

        return cls(
            internal_name=pokemon_name,
            level=level,
            raw_item=item,
            raw_moves=tuple(moves),
            ability_number=ability_number,
            sex=sex,
            form_number=form_number,
            is_shiny=is_shiny,
            nature=nature,
            iv=iv,
            happiness=happiness,
            nickname=nickname,
            shadow=shadow,
            pokeball_type=pokeball_type,
            evs=evs,
        )

    def into_csv_line(self) -> list[str]:
        """
        Writes this Pokémon to a CSV line.
        """

        if len(self.raw_moves) == 0:
            moves = [""] * 4
        else:
            # pad moves out if its less than 4
            moves = []
            for idx in range(4):
                try:
                    moves.append(self.raw_moves[idx])
                except IndexError:
                    moves.append("")

        if self.evs:
            ev_data = [
                str(self.evs.hp),
                str(self.evs.atk),
                str(self.evs.def_),
                str(self.evs.spe),
                str(self.evs.spa),
                str(self.evs.spd),
            ]
        else:
            ev_data = ["0"] * 6

        return [
            self.internal_name,
            str(self.level),
            self.raw_item or "",
            *moves,
            str(self.ability_number),
            self.sex,
            str(self.form_number),
            str(self.is_shiny).lower(),
            self.nature,
            str(self.iv),
            str(self.happiness),
            self.nickname or "",
            str(self.shadow).lower(),
            str(self.pokeball_type),
            *ev_data,
        ]


@attr.s(kw_only=True, slots=True)
class Trainer:
    """
    A single trainer in the trainer list.
    """

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        converter.register_unstructure_hook(
            cls, make_dict_unstructure_fn(cls, converter, _cattrs_omit_if_default=True)
        )

    #: The trainer class for this trainer.
    raw_trainer_class: str = attr.ib()

    #: The battler name for this trainer.
    battler_name: str = attr.ib()

    #: The battler disambiguator for this trainer, or 0 if this is the default battle.
    battler_id: int = attr.ib(default=0)

    #: The items that this trainer can use in battle.
    raw_battle_items: list[str] = attr.ib(factory=list)

    #: The list of Pokémon that this trainer uses.
    pokemon: list[SingleTrainerPokemon] = attr.ib()

    @classmethod
    def from_single_section(cls, trainer_klass: str, reader: Iterator[str]) -> Trainer:
        """
        Parses a single trainer from a single section.
        """

        battler_name = next(reader)

        if (comment_idx := battler_name.find("#")) >= 0:
            battler_name = battler_name[:comment_idx]

        battler_name = battler_name.replace("\t", "").strip()

        if "," in battler_name:
            battler_name, battler_id = battler_name.split(",", 1)
            battler_id = int(battler_id)
        else:
            battler_id = 0

        count_and_items = next(reader)
        if "," in count_and_items:
            count, *items = count_and_items.split(",")
            count = int(count)
        else:
            count = int(count_and_items)
            items = ()

        lines = [next(reader) for _ in range(count)]
        reader = csv.reader(lines)
        pokes = [SingleTrainerPokemon.from_csv_line(line) for line in reader]

        return Trainer(
            raw_trainer_class=trainer_klass,
            battler_name=battler_name,
            battler_id=battler_id,
            raw_battle_items=items,
            pokemon=pokes,
        )

    def into_pbs(self, buffer: StringIO):
        """
        Writes this trainer out in PBS format.
        """

        buffer.write(self.raw_trainer_class)
        buffer.write("\n")
        buffer.write(self.battler_name)
        if self.battler_id != 0:
            buffer.write(f",{self.battler_id}")

        buffer.write("\n")
        # weird line
        items = ",".join(self.raw_battle_items)
        buffer.write(str(len(self.pokemon)))

        if items:
            buffer.write(f",{items}")

        buffer.write("\n")
        for poke in self.pokemon:
            buffer.write(",".join(poke.into_csv_line()))
            buffer.write("\n")


@attr.s(kw_only=True)
class TrainerCatalog:
    @staticmethod
    def trainers_structure_hook(converter: Converter, data: dict[str, dict[int, Trainer]]):
        new_dict = {}

        for key, value in data.items():
            inner = {str(k): v for (k, v) in value.items()}
            new_dict[key] = converter.unstructure(inner)

        return new_dict

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        hook = cattrs.gen.make_dict_unstructure_fn(
            cls,
            converter,
            trainers=override(unstruct_hook=partial(cls.trainers_structure_hook, converter)),
        )
        converter.register_unstructure_hook(cls, hook)

    #: The name of this trainer, e.g. 'Victoria'.
    trainer_name: str = attr.ib()

    #: The mapping of trainer klass -> dict of trainer objects, keyed by number.
    trainers: dict[str, dict[int, Trainer]] = attr.ib(factory=dict)

    def all_trainers(self) -> Iterable[Trainer]:
        for values in self.trainers.values():
            yield from values.values()
