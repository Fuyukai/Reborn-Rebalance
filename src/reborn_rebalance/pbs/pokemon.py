from __future__ import annotations

import enum
from functools import cached_property

import attr
import attrs
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn

from reborn_rebalance.pbs.move import MoveCategory, PokemonMove
from reborn_rebalance.pbs.raw.kv import KvResultDict
from reborn_rebalance.pbs.type import PokemonType
from reborn_rebalance.util import PbsBuffer, chunks, get_safely

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

    def get_ability_name(self, number: int) -> str:
        try:
            return self.raw_abilities[number]
        except IndexError:
            raise IndexError(
                f"Pokemon '{self.internal_name}' has no such ability #{number}"
            ) from None

    def renamed(self, name: str) -> FormAttributes:
        return FormAttributes(
            internal_name=self.internal_name,
            name=self.name,
            form_name=name,
            base_stats=self.base_stats,
            primary_type=self.primary_type,
            secondary_type=self.secondary_type,
            raw_abilities=self.raw_abilities,
            raw_level_up_moves=self.raw_level_up_moves,
            pokedex_entry=self.pokedex_entry,
        )


@attr.s(slots=True, frozen=True)
class StatWrapper:
    """
    Wrapper class for a set of six stats, e.g. base stats or EV yield.
    """

    # there used to be validators here.
    # gargantuan steelix has 3252 hp evs. (or 1104 hp)
    hp: int = attr.ib()
    atk: int = attr.ib()
    def_: int = attr.ib()
    spa: int = attr.ib()
    spd: int = attr.ib()
    spe: int = attr.ib()

    def __iter__(self):
        yield self.hp
        yield self.atk
        yield self.def_
        yield self.spa
        yield self.spd
        yield self.spe

    @classmethod
    def empty(cls) -> StatWrapper:
        return StatWrapper(hp=0, atk=0, def_=0, spa=0, spd=0, spe=0)

    @classmethod
    def from_pbs(cls, line: str, for_format: PbsStatFormat = PbsStatFormat.REBORN_STYLE):
        """
        Creates a new :class:`.StatWrapper` for the provided PBS line.
        """

        if for_format == PbsStatFormat.REBORN_STYLE:
            stats = [int(i) for i in line.split(",")]
            stats = [stats[0], stats[1], stats[2], stats[4], stats[5], stats[3]]
            return cls(*stats)

        # new-style EV format...
        raise NotImplementedError("not yet")

    @classmethod
    def from_incomplete_list(cls, items: list[int]) -> StatWrapper:
        """
        Creates a new stat wrapper from an incomplete list.
        """

        # this is alwways coming from some nonsense like the trainer class
        hp = int(get_safely(items, 0, 0))
        atk = int(get_safely(items, 1, 0))
        def_ = int(get_safely(items, 2, 0))
        spe = int(get_safely(items, 3, 0))
        spa = int(get_safely(items, 4, 0))
        spd = int(get_safely(items, 5, 0))

        return StatWrapper(hp=hp, atk=atk, def_=def_, spe=spe, spa=spa, spd=spd)

    def to_slashed_list(self) -> str:
        return "/".join(map(str, self))

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
    A single Pokémon species.
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
    dex_number: int = attr.ib()

    #: The name for this species, e.g. 'Togekiss'.
    name: str = attr.ib()

    #: The internal name for this species. Defaults to the uppercase of ``name``.
    internal_name: str = attr.ib(
        default=attrs.Factory(lambda it: it.name.upper(), takes_self=True),
    )

    #: The base stats for this species.
    base_stats: StatWrapper = attr.ib()

    #: The primary type for this species, e.g. ``PokemonType.FLYING``.
    primary_type: PokemonType = attr.ib()
    #: The secondary type for this species, e.g. ``PokemonType.FAIRY``.
    #: May be the same as the primary type if this Pokémon has only one type.
    secondary_type: PokemonType = attr.ib()

    #: The gender ratio for this species. Governs random encounters.
    gender_ratio: SexRatio = attr.ib()
    #: The XP growth curve for this species.
    growth_rate: GrowthRate = attr.ib()

    #: The base EXP yielded when a Pokémon of this type is killed.
    exp_yield: int = attr.ib()
    #: The EVs yielded when a Pokémon of this type is killed.
    ev_yield: StatWrapper = attr.ib()

    #: The base catch rate for this species. Must be a positive number below 256.
    catch_rate: int = attr.ib(validator=validate_catch_rate, )

    #: The base happiness when caught for this species. Most have this set to 70.
    caught_happiness: int = attr.ib()

    #: The list of raw abilities this Pokémon can have. Non-empty.
    raw_abilities: list[str] = attr.ib()
    #: The hidden ability for this Pokémon, or None if it has no specific hidden ability.
    #: Deprecated.
    raw_hidden_ability: str | None = attr.ib(default=None)

    #: The list of moves learned upon level up.
    raw_level_up_moves: list[RawLevelUpMove] = attr.ib()
    #: The list of egg moves this species can learn.
    raw_egg_moves: list[str] = attr.ib(factory=list)
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
    evolutions: list[PokemonEvolution] = attr.ib(factory=list)

    # used internally ig?
    form_names: list[str] = attr.ib(factory=list)
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

        return self.raw_abilities

    @classmethod
    def from_pbs(cls, dex_number: int, data: KvResultDict) -> PokemonSpecies:
        """
        Creates a new :class:`.PokemonSpecies` from the raw ``pokemon.txt`` data.

        Note that you will need to backfill the TMs field manually after calling this.
        """

        name = data.pop_str("Name")
        internal_name = data.pop_str("InternalName", name.upper())

        # annoyingly, the base stats are in the WRONG ORDER
        # normal order: hp,atk,def,spa,spd,spe
        # PBS order: hp,atk,def,spe,spa,spd
        base_stats = StatWrapper.from_pbs(
            data.pop_str("BaseStats"), for_format=PbsStatFormat.REBORN_STYLE
        )

        primary_type: PokemonType
        secondary_type: PokemonType

        # new essentials: Types=FLYING,FAIRY
        # old (reborn) essentials: Type1=Flying ; Type2=Fairy
        if "Types" in data:
            types = [i.strip() for i in data.pop_str("types").split(",")]
            primary_type = PokemonType[types[0]]

            secondary_type = PokemonType[types[1]] if len(types) >= 1 else primary_type
        else:
            primary_type = PokemonType[data.pop_str("Type1")]
            secondary_type_name = data.pop_str("Type2", None)

            if secondary_type_name:
                secondary_type = PokemonType[secondary_type_name]
            else:
                secondary_type = primary_type

        if "GenderRatio" in data:  # newer essentials versions
            gender_ratio = SexRatio[data.pop_str("GenderRatio")]
        else:
            gender_ratio = SexRatio[data.pop_str("GenderRate")]

        growth_rate = GrowthRate[data.pop_str("GrowthRate")]
        exp_yield = data.pop_int("BaseEXP")
        evs = StatWrapper.from_pbs(
            data.pop_str("EffortPoints"), for_format=PbsStatFormat.REBORN_STYLE
        )
        catch_rate = data.pop_int("Rareness")
        happiness = data.pop_int("Happiness")

        raw_abilities = [it.upper() for it in data.pop_str("Abilities").split(",")]
        hidden_ability: str | None = data.pop_str("HiddenAbility", None)

        unparsed_moves = chunks(data.pop_str("Moves").split(","), 2)
        raw_moves: list[RawLevelUpMove] = []
        for level, move_name in unparsed_moves:
            move = RawLevelUpMove(at_level=int(level), name=move_name)
            raw_moves.append(move)

        raw_egg_moves = data.pop_str("EggMoves", "").split(",")
        if not any(raw_egg_moves):
            raw_egg_moves = []

        raw_compatibility = data.pop_str("Compatibility").split(",")
        compatibility = [EggGroup[it] for it in raw_compatibility]

        steps_to_hatch = data.pop_int("StepsToHatch", 128)
        height = float(data.pop("Height"))
        weight = float(data.pop("Weight"))
        colour = data.pop_str("Color", "White")
        habitat = data.pop_str("Habitat", None)
        kind = data.pop_str("Kind", "???")
        pokedex = data.pop_str("Pokedex")

        item_data = WildItems(
            common=data.pop_str("WildItemCommon", None),
            uncommon=data.pop_str("WildItemUncommon", None),
            rare=data.pop_str("WildItemRare", None),
        )

        battler_player_y = data.pop_int("BattlerPlayerY")
        battler_enemy_y = data.pop_int("BattlerEnemyY")
        battler_altitude = data.pop_int("BattlerAltitude")

        raw_evos: list[PokemonEvolution] = []

        pbs_evos = data.pop_str("Evolutions", "")
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

        forms = []
        for key_name in ("FormNames", "Formnames"):  # !!!
            raw_forms = data.pop_str(key_name, "")
            if forms:
                forms = raw_forms.split(",")
                continue

        regional_num = data.pop_int("RegionalNumbers", None)
        shape = data.pop_int("Shape", None)

        # FINALLY, construction the object
        if data:
            raise ValueError(f"Unparsed Pokémon data: {list(data.keys())}")

        return PokemonSpecies(
            dex_number=dex_number,
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

        if len(self.raw_abilities) <= 2:
            buffer.write_list("Abilities", self.raw_abilities)

            if self.raw_hidden_ability:
                buffer.write_key_value("HiddenAbility", self.raw_hidden_ability)

        else:
            # merged hidden abilities
            buffer.write_list("Abilities", self.raw_abilities[:2])
            buffer.write_key_value("HiddenAbility", self.raw_abilities[2])

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

        evos = [
            f"{evolution.into_name},{evolution.condition},{evolution.parameter}"
            for evolution in self.evolutions
        ]
        buffer.write_key_value("Evolutions", ",".join(evos))
