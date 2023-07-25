from __future__ import annotations

import textwrap
from collections import defaultdict
from typing import KeysView, Self

import attr

from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.type import PokemonType


class PokemonChangeSet(object):
    """
    A changelog for a single Pokémon. This class shouldn't be created directly; see
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

    def add_base_stat_change(self, stat: str, from_: int, to: int):
        """
        Adds a new base stat change addittion to this Pokémon.
        """

        self._add_change({"key": "base_stat", "stat": stat, "from": from_, "to": to})

    def add_type_change(self, prev_type: PokemonType | None, new_type: PokemonType):
        """
        Adds a type change to this Pokémon.
        """

        self._add_change({"key": "type", "prev": prev_type, "new": new_type})

    def remove_level_up_move(self, move_name: str):
        """
        Removes an level-up move from this Pokémon.
        """

        assert move_name in self._log.catalog.move_mapping, f"no such move {move_name}"
        # no level property signifies removal.
        self._add_change({"key": "move", "type": "level", "move": move_name})

    def add_level_up_move(self, level: int, move_name: str):
        """
        Adds or adjusts a level-up move to this Pokémon.
        """

        assert move_name in self._log.catalog.move_mapping, f"no such move {move_name}"
        self._add_change({"key": "move", "type": "level", "level": level, "move": move_name})

    def add_ability_change(self, replaces: str | None, new_ability: str):
        """
        Adds an ability change to this Pokémon.
        """

        self._add_change({"key": "ability", "replaces": replaces, "new": new_ability})

    def add_tm_move(self, tm: int):
        """
        Adds a TM to this Pokémon's learnset.
        """

        self._add_change({"key": "move", "type": "tm", "action": "add", "number": tm})

    def remove_tm_move(self, tm: int):
        """
        Removes a TM from this Pokémon's learnset.
        """

        self._add_change({"key": "move", "type": "tm", "action": "remove", "number": tm})


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

    def pokemon(self, internal_name: str, comment: str = None) -> PokemonChangeSet:
        """
        Gets the Pokémon changes builder
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


@attr.s(slots=True, kw_only=True)
class Changelog:
    """
    Contains all data about *all* changelogs.
    """

    #: The catalog stored on this changelog. Used for validation.
    catalog: EssentialsCatalog = attr.ib()

    #: A mapping of Pokémon internal name to the changes made, across all versions.
    pokemon: dict[str, PokemonChangeSet] = attr.ib(factory=dict)

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
