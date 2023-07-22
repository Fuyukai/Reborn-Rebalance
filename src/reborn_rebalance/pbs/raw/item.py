import attr


# pretty much only used for TM parsing.
# since TM definitions are (bafflingly) dependant on items (lol).

@attr.s(kw_only=True, slots=True)
class PokemonItem:
    """
    A single item available in the game.
    """

    #: The item ID for this item.
    id: int = attr.ib()

    #: The internal name for this item.
    internal_name: str = attr.ib()

    #: The display name for this item.
    display_name: str = attr.ib()

    # don't really care about making this an enum.
    #: The pocket this item belongs to.
    pocket: str = attr.ib()

    #: The price of this item.
    price: int = attr.ib()

    #: The description of this item.
    description: str = attr.ib()

    #: The way this item can be used from the bag.
    bag_usage: int = attr.ib()

    #: The battle usage for this item.
    battle_usage: int = attr.ib()

    #: The type for this item.
    type: int = attr.ib()

    #: The move this item teaches, if any.
    move: str | None = attr.ib()

    @classmethod
    def from_row(cls, row: list[str]):
        """
        Creates a new item from a row in the items file.
        """

        # some lines are missing the last comma, yay.
        if len(row) <= 9:
            move = None
        else:
            move = row[9]

            if not move:
                move = None

        return cls(
            id=int(row[0]),
            internal_name=row[1],
            display_name=row[2],
            pocket=row[3],
            price=int(row[4]),
            description=row[5],
            bag_usage=int(row[6]),
            battle_usage=int(row[7]),
            type=int(row[8]),
            move=move,
        )

    def get_as_pbs_row(self) -> list[str]:
        """
        Gets a PBS (CSV) row for this item.
        """

        return [
            str(self.id),
            self.internal_name,
            self.display_name,
            self.pocket,
            str(self.price),
            self.description,
            str(self.bag_usage),
            str(self.battle_usage),
            str(self.type),
            self.move if self.move is not None else "",
        ]
