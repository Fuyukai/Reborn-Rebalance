from __future__ import annotations

import enum
from functools import cached_property
from io import StringIO


class PokemonType(enum.Enum):
    """
    An enumeration of all supported Pokémon types.
    """

    # The base definitions. Don't change these!

    NORMAL = (["FIGHTING"], [], ["GHOST"])
    FIGHTING = (["FLYING", "PSYCHIC", "FAIRY"], ["ROCK", "BUG", "DARK"])
    FLYING = (["ROCK", "ELECTRIC", "ICE"], ["FIGHTING", "BUG", "GRASS"], ["GROUND"])
    POISON = (["GROUND", "PSYCHIC"], ["FIGHTING", "POISON", "BUG", "GRASS", "FAIRY"])
    GROUND = (["WATER", "GRASS", "ICE"], ["POISON", "ROCK"], ["ELECTRIC"])
    ROCK = (
        ["FIGHTING", "GROUND", "STEEL", "WATER", "GRASS"],
        ["NORMAL", "FLYING", "POISON", "FIRE"],
    )
    BUG = (["FLYING", "ROCK", "FIRE"], ["FIGHTING", "GROUND", "GRASS"])
    GHOST = (["GHOST", "DARK"], ["POISON", "BUG"], ["NORMAL", "FIGHTING"])
    STEEL = (
        ["FIGHTING", "GROUND", "FIRE"],
        [
            "NORMAL",
            "FLYING",
            "ROCK",
            "BUG",
            "FAIRY",
            "STEEL",
            "GRASS",
            "PSYCHIC",
            "ICE",
            "DRAGON",
        ],
        ["POISON"],
    )
    # hardcoded
    QMARKS = ([], [])
    FIRE = (
        ["GROUND", "ROCK", "WATER"],
        ["BUG", "STEEL", "FIRE", "GRASS", "ICE", "FAIRY"],
        [],
        True,
    )
    WATER = (["GRASS", "ELECTRIC"], ["STEEL", "FIRE", "WATER", "ICE"], [], True)
    GRASS = (
        ["FLYING", "POISON", "BUG", "FIRE", "ICE"],
        ["GROUND", "WATER", "GRASS", "ELECTRIC"],
        [],
        True,
    )
    ELECTRIC = (["GROUND"], ["FLYING", "STEEL", "ELECTRIC"], [], True)
    PSYCHIC = (["BUG", "GHOST", "DARK"], ["FIGHTING", "PSYCHIC"], [], True)
    ICE = (["FIGHTING", "ROCK", "STEEL", "FIRE"], ["ICE"], [], True)
    DRAGON = (
        ["ICE", "DRAGON", "FAIRY"],
        ["FIRE", "WATER", "GRASS", "ELECTRIC"],
        [],
        True,
    )
    DARK = (["FIGHTING", "BUG", "FAIRY"], ["GHOST", "DARK"], ["PSYCHIC"], True)
    FAIRY = (["POISON", "STEEL"], ["FIGHTING", "DARK", "BUG"], ["DRAGON"], True)

    def __init__(
        self,
        weaknesses: list[str],
        resistances: list[str],
        immunities: list[str] = None,
        special_type: bool = False,
    ):
        """
        :param weaknesses: The list of types this is weak to.
        :param resistances: The list of types this resists.
        :param immunities: The list of types this is immune to.
        :param special_type:
            If True, then all moves of this type will be treated as Special during a Glitch Field.
        """

        self.localised_name = self.name.capitalize()
        self._unresolved_weaknesses = weaknesses
        self._unresolved_resistances = resistances
        self._unresolved_immunities = immunities or []

        self.special_type = special_type

    @property
    def weaknesses(self) -> list[PokemonType]:
        """
        The resolved list of weaknesses that this type has.
        """

        return [PokemonType[it] for it in self._unresolved_weaknesses]

    @property
    def resistances(self) -> list[PokemonType]:
        """
        The resolved list of resistances that this type has.
        """

        return [PokemonType[it] for it in self._unresolved_resistances]

    @property
    def immunities(self) -> list[PokemonType]:
        """
        The resolved list of immunities that this type has.
        """

        return [PokemonType[it] for it in self._unresolved_immunities]


def dump_types() -> str:
    """
    Dumps all types into a PBS types.txt format.
    """

    buffer = StringIO()

    for idx, type in enumerate(PokemonType):
        type: PokemonType

        buffer.write(f"[{idx}]\n")

        if type == PokemonType.QMARKS:
            buffer.write("Name=???\nInternalName=QMARKS\nIsPsuedoType=true")
        else:
            buffer.write(f"Name={type.localised_name}\n")
            buffer.write(f"InternalName={type.name}\n")

            # the standard PBS types don't seem to have this as False, so we copy that behaviour
            if type.special_type:
                buffer.write("IsSpecialType=true\n")

            buffer.write(
                f"Weaknesses={','.join([typ.name for typ in type.weaknesses])}\n"
            )

            resist = [typ.name for typ in type.resistances]
            if resist:
                buffer.write(f"Resistances={','.join(resist)}\n")

            immune = [typ.name for typ in type.immunities]
            if immune:
                buffer.write(f"Immunities={','.join(immune)}\n")

        # extra newline, to keep in line with the stock format.
        buffer.write("\n")

    return buffer.getvalue()


# Apply custom type tweaks here.

# End custom tweaks.

if __name__ == "__main__":
    # without tweaks, this produces identical output to types.txt in the base game.

    print(dump_types())
