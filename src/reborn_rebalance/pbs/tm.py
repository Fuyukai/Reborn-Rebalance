from __future__ import annotations

import re
from functools import total_ordering
from typing import Any, Self

import attr
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn, override

# reborn devs are really smart and made the HMs "tmxes".
# these are like regular TMs, but in a different number namespace.
# as a side note, TMs 1..100 are Gen 5 TMs, and TMs 101..196 are Gen 8 TRs.
# the fields here will be backfilled by the catalog.

TM_NUMBER_REGEXP = re.compile(r"^(TMX?|HM)(\d{1,3})$")


def tm_number_for(name: str) -> int:
    """
    Gets the actual TM number for the provided TM string.
    """

    match = TM_NUMBER_REGEXP.match(name)
    assert match is not None, "hwat"

    return int(match.group(2))


@attr.s(kw_only=True, slots=True, order=False, hash=True, eq=True)
@total_ordering
class TechnicalMachine:
    """
    A single technical machine that can be learned by various Pokémon.
    """

    @classmethod
    def add_unstructuring_hook(cls, converter: Converter):
        unst_hook = make_dict_unstructure_fn(
            cls, converter, _cattrs_omit_if_default=True, pokemon=override(omit=True)
        )
        converter.register_unstructure_hook(cls, unst_hook)

    #: If true, this TM is actually a TMX.
    is_tmx: bool = attr.ib(default=False)

    #: The number for this TM, e.g. '76'.
    number: int | None = attr.ib(default=None)

    # what the fuck, man.
    #: If True, this is a tutor move; not a TM.
    is_tutor: bool = attr.ib(default=False)

    #: The name of the move for this TM.
    move: str = attr.ib()

    # aaaa
    # ok, this field is EMPTY in the TOML and is only used when loading from PBS.
    # tms are stored (as they fucking should be, what the fuck is this design in the game) on thee
    # POKEMON themselves.
    # this is written to during PBS serialisation as well...
    
    #: The list of compatible Pokémon for this TM. This is always empty at runtime, and is only
    #: used for serialisation purposes.
    pokemon: set[str] = attr.ib(factory=set, hash=False, eq=False)

    @classmethod
    def incomplete_from_pbs(cls, move: str, line: list[str]) -> Self:
        """
        Creates an (incomplete) TM from the provided PBS data.
        """

        return cls(move=move, pokemon=set(line))

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, TechnicalMachine):
            return NotImplemented
        
        # TMXs are always sorted before TMs
        if self.is_tmx and not other.is_tmx:
            return True

        if self.number is not None and other.number is not None:
            return self.number < other.number
        
        # lexicographic sort
        return self.move < other.move
