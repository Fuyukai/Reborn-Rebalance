from __future__ import annotations

import enum
from functools import cached_property
from pathlib import Path

import attr
import attrs
import prettyprinter
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn

from reborn_rebalance.pbs.move import MoveCategory, PokemonMove
from reborn_rebalance.pbs.raw.pokemon import raw_parse_pokemon_pbs
from reborn_rebalance.pbs.type import PokemonType
from reborn_rebalance.util import PbsBuffer, chunks

# XXX: This currently has *some* code to support non-Reborn pokemon.txt, but practically speaking
#      it only supports Reborn pokemon.txt. Keep that in mind.
#
# A note on roundtripping:
# This roundtrips perfectly for the original Gen 7 entries.
# The Gen 8+9 Pokémon have some quirks in the original, like an unconditional Type2= field, and
# integers for Height/Weight, and some badly padded values.
# But, otherwise, it generates output that works perfectly fine for the game.


class PbsStatFormat(enum.Enum):
    REBORN_STYLE = 0
    NEW_EV_STYLE = 1


@attr.s(frozen=True, slots=True, kw_only=True)
class FormAttributes:
    """
    The attributes for a specific Pokémon form.
    """

    #: The root display name for the Pokémon this is a form of.
    name: str = attr.ib()

    #: The display name for this form.
    form_name: str = attr.ib(default="Normal")

    #: The internal name for this Pokémon.
    internal_name: str = attr.ib()

    #: The base stats for this Pokémon.
    base_stats: StatWrapper = attr.ib()

    #: The primary type for this species, e.g. ``PokemonType.FLYING``.
    primary_type: PokemonType = attr.ib()
    #: The secondary type for this species, e.g. ``PokemonType.FAIRY``.
    #: May be the same as the primary type if this Pokémon has only one type.
    secondary_type: PokemonType = attr.ib()

    #: The list of raw abilities this Pokémon can have. Non-empty.
    raw_abilities: list[str] = attr.ib()

    #: The list of moves learned upon level up.
    raw_level_up_moves: list[RawLevelUpMove] = attr.ib()

    #: The Pokédex entry for this form.
    pokedex_entry: str | None = attr.ib()

    def has_stab_on(self, move: PokemonMove) -> bool:
        """
        Checks if this Pokémon has STAB (Same Type Advantage Bonus) on the given move.
        """

        if move.category == MoveCategory.STATUS:
            return False

        if move.base_power <= 0:
            return False

        return move.type == self.primary_type or move.type == self.secondary_type


@attr.s(slots=True, frozen=True)
class StatWrapper:
    """
    Wrapper class for a set of six stats, e.g. base stats or EV yield.
    """

    @staticmethod
    def validate_base_stat(_, __, stat: int):
        if stat < 0:
            raise ValueError("Stats cannot be less than zero")

        elif stat > 255:
            raise ValueError("Stats cannot be greater than 255")

    hp: int = attr.ib(validator=validate_base_stat)
    atk: int = attr.ib(validator=validate_base_stat)
    def_: int = attr.ib(validator=validate_base_stat)
    spa: int = attr.ib(validator=validate_base_stat)
    spd: int = attr.ib(validator=validate_base_stat)
    spe: int = attr.ib(validator=validate_base_stat)

    @classmethod
    def from_pbs(cls, line: str, for_format: PbsStatFormat = PbsStatFormat.REBORN_STYLE):
        """
        Creates a new :class:`.StatWrapper` for the provided PBS line.
        """

        if for_format == PbsStatFormat.REBORN_STYLE:
            stats = [int(i) for i in line.split(",")]
            stats = [stats[0], stats[1], stats[2], stats[4], stats[5], stats[3]]
            return cls(*stats)

        else:
            # new-style EV format...
            raise NotImplementedError("not yet")

    def sum(self) -> int:
        """
        Gets the total sum of this stat list.
        """

        return self.hp + self.atk + self.def_ + self.spa + self.spd + self.spe

    def to_pbs(self, for_format: PbsStatFormat = PbsStatFormat.REBORN_STYLE) -> str:
        """
        Converts these base stats into a PBS list.
        """

        if for_format == PbsStatFormat.REBORN_STYLE:
            return f"{self.hp},{self.atk},{self.def_},{self.spe},{self.spa},{self.spd}"

        else:
            raise NotImplementedError("not yet")


class SexRatio(enum.Enum):
    AlwaysMale = 0
    FemaleOneEighth = 1
    Female25Percent = 2
    Female50Percent = 3
    Female75Percent = 4
    FemaleSevenEighths = 5
    AlwaysFemale = 6
    Genderless = 7


class GrowthRate(enum.Enum):
    Fast = 0
    Medium = 1
    Slow = 2
    Parabolic = 3
    Erratic = 4
    Fluctuating = 5


@attr.s(frozen=True, kw_only=True)
class RawLevelUpMove:
    """
    A raw wrapper for a level-up move.
    """

    #: The level this move is learned at.
    at_level: int = attr.ib()

    #: The internal name of the move.
    name: str = attr.ib()


class EggGroup(enum.Enum):
    Monster = 0
    Water1 = 1
    Bug = 2
    Flying = 3
    Field = 4
    Fairy = 5
    Grass = 6
    Humanlike = 7
    Water3 = 8
    Mineral = 9
    Amorphous = 10
    Water2 = 11  # lol, what?
    Ditto = 12
    Dragon = 13
    Undiscovered = 14


@attr.s(frozen=True, kw_only=True, slots=True)
class WildItems:
    """
    Wraps the possible items a Pokémon in the wild can hold.
    """

    #: An item with 50% chance.
    common: str | None = attr.ib(default=None)

    #: An item with 5% chance.
    uncommon: str | None = attr.ib(default=None)

    #: An item with 1% chance.
    rare: str | None = attr.ib(default=None)

    def write(self, buffer: PbsBuffer):
        """
        Writes the items out to PBS format.
        """

        if self.common:
            buffer.write_key_value("WildItemCommon", self.common)

        if self.uncommon:
            buffer.write_key_value("WildItemUncommon", self.uncommon)

        if self.rare:
            buffer.write_key_value("WildItemRare", self.rare)


# TODO: this sucks dick. can probably awkwardly ruby-codegen this...?
@attr.s(frozen=True, kw_only=True, slots=True)
class PokemonEvolution:
    """
    A single evolution method for a Pokémon.
    """

    #: What Pokémon this one will evolve into.
    into_name: str = attr.ib()

    #: The evolution condition. Refers to an internal value in the Reborn code.
    condition: str = attr.ib()

    #: Condition-specific parameter.
    parameter: str | None = attr.ib(default=None)


@attr.s(kw_only=True)
class PokemonSpecies:
    """
    A single species as stored in a YAML file.
    """

    @classmethod
    def add_unstructuring_hook(cls, converter: Converter):
        for klass in [
            PokemonEvolution,
            PokemonSpecies,
            WildItems,
            cls,
        ]:
            unst_hook = make_dict_unstructure_fn(
                klass,
                converter,
                _cattrs_omit_if_default=True,
            )
            converter.register_unstructure_hook(klass, unst_hook)

    @staticmethod
    def validate_catch_rate(_, __, rate: int):
        if rate > 255:
            raise ValueError(f"catch rate {rate} is > 255 (not allowed)")

    #: The Pokédex number of this species. Backfilled.
    dex_number: int = attr.ib(default=0)

    #: The name for this species, e.g. 'Togekiss'.
    name: str = attr.ib(kw_only=True)

    #: The internal name for this species. Defaults to the uppercase of ``name``.
    internal_name: str = attr.ib(
        default=attrs.Factory(lambda it: it.name, takes_self=True),
        kw_only=True,
    )

    #: The base stats for this species.
    base_stats: StatWrapper = attr.ib(kw_only=True)

    #: The primary type for this species, e.g. ``PokemonType.FLYING``.
    primary_type: PokemonType = attr.ib(kw_only=True)
    #: The secondary type for this species, e.g. ``PokemonType.FAIRY``.
    #: May be the same as the primary type if this Pokémon has only one type.
    secondary_type: PokemonType = attr.ib(kw_only=True)

    #: The gender ratio for this species. Governs random encounters.
    gender_ratio: SexRatio = attr.ib(kw_only=True)
    #: The XP growth curve for this species.
    growth_rate: GrowthRate = attr.ib(kw_only=True)

    #: The base EXP yielded when a Pokémon of this type is killed.
    exp_yield: int = attr.ib(kw_only=True)
    #: The EVs yielded when a Pokémon of this type is killed.
    ev_yield: StatWrapper = attr.ib(kw_only=True)

    #: The base catch rate for this species. Must be a positive number below 256.
    catch_rate: int = attr.ib(validator=validate_catch_rate, kw_only=True)

    #: The base happiness when caught for this species. Most have this set to 70.
    caught_happiness: int = attr.ib(kw_only=True)

    #: The list of raw abilities this Pokémon can have. Non-empty.
    raw_abilities: list[str] = attr.ib()
    #: The hidden ability for this Pokémon, or None if it has no specific hidden ability.
    raw_hidden_ability: str | None = attr.ib(default=None)

    #: The list of moves learned upon level up.
    raw_level_up_moves: list[RawLevelUpMove] = attr.ib()
    #: The list of egg moves this species can learn.
    raw_egg_moves: list[str] = attr.ib()
    #: The list of TMs this species can learn.
    raw_tms: list[str] = attr.ib()
    #: The list of tutor moves this species can learn.
    raw_tutor_moves: list[str] = attr.ib()

    #: The list of egg groups that this species can breed with.
    compatible_egg_groups: list[EggGroup] = attr.ib()

    #: The number of steps this species requires to hatch an egg of.
    steps_to_hatch: int = attr.ib()

    #: The height of this species, in metres.
    height: float = attr.ib()
    #: The weight of this species, in metres.
    weight: float = attr.ib()

    #: Colour used by the Pokédex.
    colour: str = attr.ib()
    #: Unused.
    habitat: str | None = attr.ib(default=None)
    #: Type listed in the Pokédex, e.g. 'Jubilee' (whatever that means).
    kind: str = attr.ib()

    #: The Pokédex entry for this species.
    pokedex_entry: str = attr.ib()

    #: The wild item chances for this species.
    wild_items: WildItems = attr.ib(factory=WildItems)

    # used by reborn for things?
    battler_player_y: int = attr.ib()
    battler_enemy_y: int = attr.ib()
    battler_altitude: int = attr.ib()

    #: The list of possible evolutions for this species.
    evolutions: list[PokemonEvolution] = attr.ib()

    # used internally ig?
    form_names: list[str] = attr.ib()
    # ? gen 8 nonsense. we keep it for round-tripping
    regional_numbers: int | None = attr.ib(default=None)
    shape: int | None = attr.ib(default=None)

    @cached_property
    def default_attributes(self) -> FormAttributes:
        return FormAttributes(
            name=self.name,
            form_name="Normal",
            primary_type=self.primary_type,
            secondary_type=self.secondary_type,
            base_stats=self.base_stats,
            raw_abilities=self.full_abilities,
            raw_level_up_moves=self.raw_level_up_moves,
            pokedex_entry=self.pokedex_entry,
            internal_name=self.internal_name,
        )

    @cached_property
    def full_abilities(self) -> list[str]:
        if self.raw_hidden_ability:
            return [*self.raw_abilities, self.raw_hidden_ability]
        else:
            return self.raw_abilities

    @classmethod
    def from_pbs(cls, data: dict[str, str | int]) -> PokemonSpecies:
        """
        Creates a new :class:`.PokemonSpecies` from the raw ``pokemon.txt`` data.

        Note that you will need to backfill the TMs field manually after calling this.
        """

        name = data.pop("Name")
        internal_name = data.pop("InternalName", name.upper())

        # annoyingly, the base stats are in the WRONG ORDER
        # normal order: hp,atk,def,spa,spd,spe
        # PBS order: hp,atk,def,spe,spa,spd
        base_stats = StatWrapper.from_pbs(
            data.pop("BaseStats"), for_format=PbsStatFormat.REBORN_STYLE
        )

        primary_type: PokemonType
        secondary_type: PokemonType

        # new essentials: Types=FLYING,FAIRY
        # old (reborn) essentials: Type1=Flying ; Type2=Fairy
        if "Types" in data:
            types = [i.strip() for i in data.pop("types").split(",")]
            primary_type = PokemonType[types[0]]

            if len(types) >= 1:
                secondary_type = PokemonType[types[1]]
            else:
                secondary_type = primary_type
        else:
            primary_type = PokemonType[data.pop("Type1")]
            secondary_type_name = data.pop("Type2", None)

            if secondary_type_name:
                secondary_type = PokemonType[secondary_type_name]
            else:
                secondary_type = primary_type

        if "GenderRatio" in data:  # newer essentials versions
            gender_ratio = SexRatio[data.pop("GenderRatio")]
        else:
            gender_ratio = SexRatio[data.pop("GenderRate")]

        growth_rate = GrowthRate[data.pop("GrowthRate")]
        exp_yield = data.pop("BaseEXP")
        evs = StatWrapper.from_pbs(data.pop("EffortPoints"), for_format=PbsStatFormat.REBORN_STYLE)
        catch_rate = data.pop("Rareness")
        happiness = data.pop("Happiness")

        raw_abilities = [it.upper() for it in data.pop("Abilities").split(",")]
        hidden_ability: str | None = data.pop("HiddenAbility", None)

        unparsed_moves = chunks(data.pop("Moves").split(","), 2)
        raw_moves: list[RawLevelUpMove] = []
        for level, move_name in unparsed_moves:
            move = RawLevelUpMove(at_level=int(level), name=move_name)
            raw_moves.append(move)

        raw_egg_moves = data.pop("EggMoves", "").split(",")
        if not any(raw_egg_moves):
            raw_egg_moves = []

        raw_compatibility = data.pop("Compatibility").split(",")
        compatibility = [EggGroup[it] for it in raw_compatibility]

        steps_to_hatch = data.pop("StepsToHatch", 128)
        height = float(data.pop("Height"))
        weight = float(data.pop("Weight"))
        colour = data.pop("Color", "White")
        habitat = data.pop("Habitat", None)
        kind = data.pop("Kind", "???")
        pokedex = data.pop("Pokedex")

        item_data = WildItems(
            common=data.pop("WildItemCommon", None),
            uncommon=data.pop("WildItemUncommon", None),
            rare=data.pop("WildItemRare", None),
        )

        battler_player_y = data.pop("BattlerPlayerY")
        battler_enemy_y = data.pop("BattlerEnemyY")
        battler_altitude = data.pop("BattlerAltitude")

        raw_evos: list[PokemonEvolution] = []

        pbs_evos = data.pop("Evolutions", "")
        if pbs_evos:
            unparsed_evos = list(chunks(pbs_evos.split(","), 3))

            for packed in unparsed_evos:
                # wtf? thanks gen 8
                try:
                    into, cond, cond_param = packed
                except ValueError:
                    into, cond = packed
                    cond_param = ""

                raw_evos.append(
                    PokemonEvolution(into_name=into, condition=cond, parameter=cond_param)
                )

        forms = data.pop("FormNames", "")
        if forms:
            forms = forms.split(",")
        else:
            forms = []

        regional_num = data.pop("RegionalNumbers", None)
        shape = data.pop("Shape", None)

        # FINALLY, construction the object
        if data:
            raise ValueError(f"Unparsed Pokémon data: {list(data.keys())}")

        return PokemonSpecies(
            dex_number=0,
            name=name,
            internal_name=internal_name,
            base_stats=base_stats,
            primary_type=primary_type,
            secondary_type=secondary_type,
            gender_ratio=gender_ratio,
            growth_rate=growth_rate,
            exp_yield=exp_yield,
            ev_yield=evs,
            catch_rate=catch_rate,
            caught_happiness=happiness,
            raw_abilities=raw_abilities,
            raw_hidden_ability=hidden_ability,
            raw_level_up_moves=raw_moves,
            raw_egg_moves=raw_egg_moves,
            raw_tms=[],  # not available here
            raw_tutor_moves=[],  # also not available here
            compatible_egg_groups=compatibility,
            steps_to_hatch=steps_to_hatch,
            height=height,
            weight=weight,
            colour=colour,
            habitat=habitat,
            kind=kind,
            pokedex_entry=pokedex,
            wild_items=item_data,
            battler_player_y=battler_player_y,
            battler_enemy_y=battler_enemy_y,
            battler_altitude=battler_altitude,
            evolutions=raw_evos,
            form_names=forms,
            regional_numbers=regional_num,
            shape=shape,
        )

    def to_pbs(self, buffer: PbsBuffer):
        """
        Writes this Pokémon species definition out into PBS format.

        This does not output the leading dex number format (well, how could it?)
        """

        buffer.write_key_value("Name", self.name)
        buffer.write_key_value("InternalName", self.internal_name)
        buffer.write_key_value("Type1", self.primary_type.name)

        if self.secondary_type != self.primary_type:
            buffer.write_key_value("Type2", self.secondary_type.name)

        buffer.write_key_value("BaseStats", self.base_stats.to_pbs())
        # TODO: new format
        buffer.write_key_value("GenderRate", self.gender_ratio.name)
        buffer.write_key_value("GrowthRate", self.growth_rate.name)
        buffer.write_key_value("BaseEXP", self.exp_yield)
        buffer.write_key_value("EffortPoints", self.ev_yield.to_pbs())
        buffer.write_key_value("Rareness", self.catch_rate)
        buffer.write_key_value("Happiness", self.caught_happiness)
        buffer.write_list("Abilities", self.raw_abilities)

        if self.raw_hidden_ability:
            buffer.write_key_value("HiddenAbility", self.raw_hidden_ability)

        moves = [f"{move.at_level},{move.name}" for move in self.raw_level_up_moves]
        buffer.write_list("Moves", moves)

        if self.raw_egg_moves:
            buffer.write_list("EggMoves", self.raw_egg_moves)

        buffer.write_list("Compatibility", [i.name for i in self.compatible_egg_groups])
        buffer.write_key_value("StepsToHatch", self.steps_to_hatch)
        buffer.write_key_value("Height", self.height)
        buffer.write_key_value("Weight", self.weight)
        buffer.write_key_value("Color", self.colour)

        if self.habitat:
            buffer.write_key_value("Habitat", self.habitat)

        # the order of some of the below ones is guessed.

        if self.regional_numbers is not None:
            buffer.write_key_value("RegionalNumbers", self.regional_numbers)

        if self.shape is not None:
            buffer.write_key_value("Shape", self.shape)

        buffer.write_key_value("Kind", self.kind)
        buffer.write_key_value("Pokedex", self.pokedex_entry)

        # oricorio is our source for this, it goes ABOVE wild_items.
        if self.form_names:
            buffer.write_list("FormNames", self.form_names)

        self.wild_items.write(buffer)

        buffer.write_key_value("BattlerPlayerY", self.battler_player_y)
        buffer.write_key_value("BattlerEnemyY", self.battler_enemy_y)
        buffer.write_key_value("BattlerAltitude", self.battler_altitude)

        evos = []
        for evolution in self.evolutions:
            evos.append(f"{evolution.into_name},{evolution.condition},{evolution.parameter}")
        buffer.write_key_value("Evolutions", ",".join(evos))


if __name__ == "__main__":

    def main():
        prettyprinter.install_extras(include=["attrs"])

        pbs = raw_parse_pokemon_pbs(Path.home() / "aur/pokemon/reborn/PBS/pokemon.txt")

        pbs_buffer = PbsBuffer()
        for idx, entry in enumerate(pbs):
            parsed = PokemonSpecies.from_pbs(entry)
            pbs_buffer.write_id_header(idx + 1)
            parsed.to_pbs(pbs_buffer)

        Path("./pokemon.txt").write_text(pbs_buffer.backing.getvalue())

    main()
