from __future__ import annotations

import enum
from typing import Self

import attr
from typing_extensions import override

from reborn_rebalance.pbs.type import PokemonType


class MoveCategory(enum.Enum):
    STATUS = 0
    SPECIAL = 1
    PHYSICAL = 2


# this sucks shit
class MoveTarget(enum.Enum):
    ANY_OTHER = 0
    UNTARGETED = 1
    SINGLE_OPPOSING_RANDOM = 2
    ALL_OPPOSING = 4
    ALL_OTHER_THAN_USER = 8
    USER = 10
    BOTH_SIDES = 20
    ONLY_USER_SIDE = 40
    ONLY_OPPOSING_SIDE = 80
    USER_PARTNER = 100  # NOT offensive?
    SINGLE_ON_SIDE = 200  # what?
    SINGLE_OPPOSING = 400  # NOT random
    DIRECTLY_OPPOSITE = 800
    WHO_KNOWS = 1000

    @property
    def template_name(self) -> str:
        return self.name.replace("_", " ").capitalize()


class MoveFlag(enum.Enum):
    MAKES_CONTACT = "a"
    PROTECTABLE = "b"
    MAGIC_COATABLE = "c"  # ??
    SNATCHABLE = "d"  # michael rosen voice
    MIRRORABLE = "e"
    FLINCH = "f"  # inator
    THAWING = "g"
    EXTRA_CRITS = "h"
    BITING = "i"
    PUNCHING = "j"
    SOUND = "k"
    POWDERY = "l"
    PULSING = "m"
    BOMBER_HARRIS = "n"

    @property
    def template_name(self) -> str:
        return self.name.replace("_", " ").capitalize()

@attr.s(kw_only=True, frozen=True, slots=True, eq=False, hash=False)
class PokemonMove:
    """
    A single Pokémon move.
    """

    @staticmethod
    def validate_bp(_, __, it: int):
        if it < 0 or it > 255:
            raise ValueError(f"move base power must be 0..=255, not {it}")

    #: The internal ID for this move. Not very useful.
    id: int = attr.ib()

    #: The internal name for this move, as used inside the game.
    internal_name: str = attr.ib()

    #: The display name for this move.
    display_name: str = attr.ib()

    #: The move function. Used internally by the game.
    move_function: str = attr.ib()

    #: The BP (Base Power) for the move. Moves with no concept of power have 0BP.
    #: Moves with custom BP have 1BP.
    base_power: int = attr.ib(validator=validate_bp)

    #: The type of the move.
    type: PokemonType = attr.ib()

    #: The category for the move.
    category: MoveCategory = attr.ib()

    #: The accuracy for the move. Moves that never miss have accuracy zero.
    accuracy: int = attr.ib()

    #: The maximum PP for this move, before PP Ups.
    max_pp: int = attr.ib()

    #: The chance that a secondary effect might happen.
    secondary_effect_chance: int = attr.ib()

    #: The target selection value for this move. Fake bitfield.
    target_selection: MoveTarget = attr.ib()

    #: The priority of this move, from -6 to 6. (Switching is priority 7).
    priority: int = attr.ib()

    # lol
    #: The list of flags for this move.
    flags: list[MoveFlag] = attr.ib()

    #: The full description for this move.
    description: str = attr.ib()

    @classmethod
    def load_from_pbs_line(cls, line: list[str]) -> Self:
        """
        Loads a single move from a single line of the ``moves.txt`` PBS.
        """

        id = int(line[0])
        internal_name = line[1]
        display_name = line[2]
        move_function = line[3]
        base_power = int(line[4])
        typing = PokemonType[line[5].upper()]
        category = MoveCategory[line[6].upper()]
        accuracy = int(line[7])
        max_pp = int(line[8])
        effect_chance = int(line[9])
        target_selection = MoveTarget(int(line[10]))
        priority = int(line[11])

        raw_flags = line[12]
        flags: list[MoveFlag] = [MoveFlag(c) for c in raw_flags]
        description = line[13]

        return cls(
            id=id,
            internal_name=internal_name,
            display_name=display_name,
            move_function=move_function,
            base_power=base_power,
            type=typing,
            category=category,
            accuracy=accuracy,
            max_pp=max_pp,
            secondary_effect_chance=effect_chance,
            target_selection=target_selection,
            priority=priority,
            flags=flags,
            description=description,
        )

    def get_as_pbs_row(self) -> list[str]:
        """
        Writes this move to a single line of the ``moves.txt`` PBS.
        """

        return [
            str(self.id),
            self.internal_name,
            self.display_name,
            self.move_function,
            str(self.base_power),
            self.type.name.upper(),
            self.category.name.capitalize(),  # wtf? why?
            str(self.accuracy),
            str(self.max_pp),
            str(self.secondary_effect_chance),
            str(self.target_selection.value),
            str(self.priority),
            "".join([flag.value for flag in self.flags]),
            self.description,
        ]
    
    @property
    def final_max_pp(self) -> int:
        """
        Gets the final max PP of this move, after PP Max.
        """

        return int(self.max_pp * 8/5)

    @override
    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, PokemonMove):
            return NotImplemented

        return other.internal_name == self.internal_name
    
    @override
    def __hash__(self) -> int:
        return hash(self.internal_name)


class MoveMappingEntryType(enum.Enum):
    """
    The type (i.e. learning type) of an entry in the move mapping.
    """

    START = 0
    EVOLUTION = 1
    LEVEL_UP = 2
    TM = 3
    TUTOR = 4
    EGG = 5


@attr.s(slots=True, kw_only=True, frozen=True)
class MoveMappingEntry:
    """
    A single entry in the reverse move mapping dict.
    """

    #: The internal name of the move.
    internal_name: str = attr.ib()

    #: The way this move is learned.
    type: MoveMappingEntryType = attr.ib()

    #: The internal name of the Pokémon this move is learned by.
    species_name: str = attr.ib()

    #: The form ID of the Pokémon that this move is learned by.
    form_id: int = attr.ib(default=0)

    #: If this is a level-up move, the level at which this move is learned.
    #: This will be '0' for evolution moves, and '1' for starting moves.
    learned_at: int | None = attr.ib(default=None)
