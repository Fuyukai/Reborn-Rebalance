import attr


@attr.s(frozen=True, slots=True, kw_only=True)
class PokemonAbility:
    """
    A single ability that multiple Pokémon can have.
    """

    #: The internal ID for this ability.
    id: int = attr.ib()

    #: The internal name for this ability.
    name: str = attr.ib()

    #: The display name for this ability.
    display_name: str = attr.ib()

    #: The description for this ability.
    description: str = attr.ib()

    @classmethod
    def from_pbs(cls, pbs: list[str]):
        """
        Creates a new ability from the providied CSV PBS line.
        """

        return cls(
            id=int(pbs[0]),
            name=pbs[1],
            display_name=pbs[2],
            description=pbs[3],
        )

    def to_pbs(self) -> list[str]:
        """
        Converts this ability to a PBS-formatted CSV line.
        """

        return [
            str(self.id),
            self.name,
            self.display_name,
            self.description,
        ]
