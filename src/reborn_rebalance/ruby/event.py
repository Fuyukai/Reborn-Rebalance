from __future__ import annotations

import enum
import re
from collections.abc import Callable, Iterator

import attrs
from rgss import RubyEventPage, RubyRpgEvent, RubyRpgMap
from rgss.rpg.commands import (
    ConditionalBranchCommand,
    InlineRubyCommand,
    InlineRubyContinuedCommand,
    RubyBaseEventCommand,
)
from rgss.rpg.commands.flow import CheckScriptReturnOpval

TM_MATCH = re.compile(r"(?P<type>pbReceiveItem|pbItemBall)\(PBItems::TM(?P<tm>[0-9]{1,3})\)")
WILD_BATTLE_MATCH = re.compile(
    r"pbWildBattle\(PBSpecies::(?P<name>[a-zA-Z]+),[\s]?(?P<level>[0-9]{1,3})[\s]?,[0-9]+\)"
)
EVENT_ADD_MATCH = re.compile(
    r"(?:PokeBattle_Pokemon\.new|pbAddPokemon)\((?:PBSpecies:)?:(?P<name>[a-zA-Z]+),[\s]?(?P<level>[0-9]{1,3})\)"
)
EGG_MATCH = re.compile(r"pbGenerateEgg\(:(?P<species>[a-zA-Z]+)\)")
TRADE_MATCH = re.compile(r"pbStartTrade\(.*,[\s]*PBSpecies::(?P<species>[a-zA-Z]+)")


@attrs.define(kw_only=True)
class PickedEventCommand:
    """
    A single event command picked out of the event stream.
    """

    #: The parent event for this picked out command.
    event: RubyRpgEvent = attrs.field()

    #: The event page the picked out command is contained within.
    page: RubyEventPage = attrs.field()


type EventPicker = Callable[[RubyRpgMap, RubyRpgEvent, int, int], PickedEventCommand | None]


@attrs.define(kw_only=True)
class EventStream:
    """
    A stream of events that can have individual commands picked out for further inspection.
    """

    pickers: list[EventPicker] = attrs.field(factory=list)

    def _select_from_event(
        self, map: RubyRpgMap, evt: RubyRpgEvent
    ) -> Iterator[PickedEventCommand]:
        for idx, page in enumerate(evt.pages):
            for cmd_idx, _ in enumerate(page.commands):
                for picker in self.pickers:
                    result = picker(map, evt, idx, cmd_idx)
                    if result is not None:
                        yield result

    def pick_events(self, map: RubyRpgMap) -> Iterator[PickedEventCommand]:
        """
        Picks out events from the provided map.
        """

        for event in map.events.values():
            yield from self._select_from_event(map, event)


# individual pickers


def _unwrap_single_command(command: RubyBaseEventCommand) -> str | None:
    if isinstance(command, ConditionalBranchCommand) and isinstance(
        command.wrapped, CheckScriptReturnOpval
    ):
        return command.wrapped.script

    if isinstance(command, (InlineRubyCommand, InlineRubyContinuedCommand)):
        return command.script

    return None


def unwrap_scripts(page: RubyEventPage, start_idx: int) -> str:
    """
    Unwraps a series of Ruby script commands.
    """

    counter = start_idx
    full_script = ""

    while counter < len(page.commands):
        if (script := _unwrap_single_command(page.commands[counter])) is None:
            break

        full_script += script
        full_script += "\n"
        counter += 1

    return full_script.rstrip()


@attrs.define(kw_only=True)
class ReceivedTechnicalMachineCommand(PickedEventCommand):
    """
    Picks out receiving a TM from the event stream.
    """

    map: RubyRpgMap
    is_given: bool = attrs.field()
    item_name: str = attrs.field()

    @classmethod
    def pick(
        cls, map: RubyRpgMap, event: RubyRpgEvent, page_idx: int, command_idx: int
    ) -> ReceivedTechnicalMachineCommand | None:
        script = unwrap_scripts(event.pages[page_idx], command_idx)

        if (matched := TM_MATCH.search(script)) is None:
            return None

        type, number = matched.groups()
        return ReceivedTechnicalMachineCommand(
            map=map,
            event=event,
            page=event.pages[page_idx],
            is_given=type != "pbItemBall",
            item_name="TM" + number,
        )


class StaticEncounterType(enum.Enum):
    OVERWORLD_WILD = 0
    NPC_EVENT = 1
    EGG = 2
    TRADE = 3


@attrs.define(kw_only=True)
class StaticEncounterCommand(PickedEventCommand):
    """
    A command for starting a static encounter in some form.
    """

    type: StaticEncounterType = attrs.field()
    raw_species_name: str = attrs.field()
    level: int = attrs.field()

    @classmethod
    def pick(
        cls, map: RubyRpgMap, event: RubyRpgEvent, page_idx: int, command_idx: int
    ) -> StaticEncounterCommand | None:
        script = unwrap_scripts(event.pages[page_idx], command_idx).replace("\n", "")

        if (m := WILD_BATTLE_MATCH.search(script)) is not None:
            type = StaticEncounterType.OVERWORLD_WILD
            species, level = m.groups()

        elif (m := EVENT_ADD_MATCH.search(script)) is not None:
            type = StaticEncounterType.NPC_EVENT
            species, level = m.groups()

        elif (m := EGG_MATCH.search(script)) is not None:
            type = StaticEncounterType.EGG
            species = m.groups()[0]
            level = 1

        elif (m := TRADE_MATCH.search(script)) is not None:
            type = StaticEncounterType.TRADE
            species = m.groups()[0]
            level = 1

        else:
            return None

        return StaticEncounterCommand(
            type=type,
            event=event,
            page=event.pages[page_idx],
            raw_species_name=species,
            level=int(level),
        )


EVENT_PICKER = EventStream(
    pickers=[
        ReceivedTechnicalMachineCommand.pick,
        StaticEncounterCommand.pick,
    ]
)
