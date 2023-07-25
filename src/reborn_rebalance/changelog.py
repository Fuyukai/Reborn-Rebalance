from __future__ import annotations

import abc
import textwrap
from collections import defaultdict
from typing import KeysView, Self

import attr

from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.type import PokemonType


class BaseChangeSet:
    """
    Base class shared between changeset types.
    """

    def __init__(self, name: str, changelog: Changelog):
        self._name = name
        self._log = changelog

        # simple mapping of {version: list of changes}.
        self._changes: dict[str, list[dict]] = {}
        self._comments: dict[str, str] = {}
        self._current_version = None

    def _add_change(self, change: dict):
        assert "key" in change, "missing changelog entry key"

        self._changes[self._current_version].append(change)

    def _set_current_version(self, version: str):
        self._current_version = version
        self._changes[version] = []

    def has_version(self, version: str) -> bool:
        """
        Checks if this Pokémon was changed for the provided version.
        """

        return version in self._changes


class PokemonChangeSet(BaseChangeSet):
    """
    A changelog for a single Pokémon. This class shouldn't be created directly.
    """

    def add_base_stat_change(self, stat: str, from_: int, to: int) -> Self:
        """
        Adds a new base stat change addittion to this Pokémon.
        """

        self._add_change({"key": "base_stat", "stat": stat, "from": from_, "to": to})
        return self

    def add_type_change(self, prev_type: PokemonType | None, new_type: PokemonType) -> Self:
        """
        Adds a type change to this Pokémon.
        """

        self._add_change({"key": "type", "prev": prev_type, "new": new_type})
        return self

    def remove_level_up_move(self, move_name: str) -> Self:
        """
        Removes an level-up move from this Pokémon.
        """

        assert move_name in self._log.catalog.move_mapping, f"no such move {move_name}"
        # no level property signifies removal.
        self._add_change({"key": "move", "type": "level", "move": move_name})
        return self

    def add_level_up_move(self, level: int, move_name: str) -> Self:
        """
        Adds or adjusts a level-up move to this Pokémon.
        """

        assert move_name in self._log.catalog.move_mapping, f"no such move {move_name}"
        self._add_change({"key": "move", "type": "level", "level": level, "move": move_name})
        return self

    def add_ability_change(self, replaces: str | None, new_ability: str) -> Self:
        """
        Adds an ability change to this Pokémon.
        """

        self._add_change({"key": "ability", "replaces": replaces, "new": new_ability})
        return self

    def add_tm_move(self, tm: int) -> Self:
        """
        Adds a TM to this Pokémon's learnset.
        """

        self._add_change({"key": "move", "type": "tm", "action": "add", "number": tm})
        return self

    def remove_tm_move(self, tm: int) -> Self:
        """
        Removes a TM from this Pokémon's learnset.
        """

        self._add_change({"key": "move", "type": "tm", "action": "remove", "number": tm})
        return self


class MoveChangeSet(BaseChangeSet):
    """
    A changelog for individual moves.
    """

    def change_move_base_power(self, old_bp: int, new_bp: int) -> Self:
        """
        Adds an entry for changing a move's base power.
        """

        self._add_change({"key": "bp", "old": old_bp, "new": new_bp})
        return self

    def change_move_accuracy(self, old_acc: int, new_acc: int) -> Self:
        """
        Adds an entry for changing a move's accuracy.
        """

        self._add_change({"key": "acc", "old": old_acc, "new": new_acc})
        return self


class ChangelogBuilder(object):
    """
    Progressively builds a changelog up.
    """

    def __init__(self, log: Changelog, version: str):
        self._log = log
        self._version = version

        self._finalized = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._finalized = True
        return False

    def custom(self, comment: str):
        """
        Adds a single custom comment to the overall changelog.
        """

        self._log.custom_comments[self._version].append(comment)

    def pokemon(self, internal_name: str, comment: str = None) -> PokemonChangeSet:
        """
        Gets the Pokémon changes builder for the provided Pokémon species.
        """

        internal_name = internal_name.upper()

        changes = self._log.pokemon.setdefault(
            internal_name, PokemonChangeSet(internal_name, self._log)
        )
        changes._set_current_version(self._version)

        if comment:
            comment = textwrap.dedent(comment)
            if comment.startswith("\n"):
                comment = comment[1:]

            changes._comments[self._version] = comment

        return changes

    def move(self, internal_name: str, comment: str = None) -> MoveChangeSet:
        """
        Gets the move changes builder for the provided move.
        """

        # todo: dedeuplicate
        internal_name = internal_name.upper()

        changes = self._log.moves.setdefault(internal_name, MoveChangeSet(internal_name, self._log))
        changes._set_current_version(self._version)

        if comment:
            comment = textwrap.dedent(comment)
            if comment.startswith("\n"):
                comment = comment[1:]

            changes._comments[self._version] = comment

        return changes


@attr.s(slots=True, kw_only=True)
class Changelog:
    """
    Contains all data about *all* changelogs.
    """

    #: The catalog stored on this changelog. Used for validation.
    catalog: EssentialsCatalog = attr.ib()

    #: A mapping of Pokémon internal name to the changes made, across all versions.
    pokemon: dict[str, PokemonChangeSet] = attr.ib(factory=dict)

    #: A mapping of move internal name to the changes made, across all versions.
    moves: dict[str, MoveChangeSet] = attr.ib(factory=dict)

    #: A list of custom comments, under the "General" section,
    #: in {version: list[version comments]} format.
    custom_comments: dict[str, list[str]] = attr.ib(factory=lambda: defaultdict(list))

    # sets aren't ordered. yay!
    _versions: dict[str, None] = attr.ib(factory=dict)

    @property
    def versions(self) -> KeysView[str]:
        """
        Gets all of the versions in this changelog as a set-like object.
        """

        return self._versions.keys()

    def version(self, version: str) -> ChangelogBuilder:
        """
        Gets a :class:`.ChangelogBuilder` for the provided changelog version.
        """

        self._versions[version] = None
        return ChangelogBuilder(self, version)
