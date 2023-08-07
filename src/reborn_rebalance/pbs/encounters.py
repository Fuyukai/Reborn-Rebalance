import enum
from pathlib import Path
from typing import TextIO

import attr

# like five days into this project I found a lib that can parse ruby marshal files.
# im going to actually for real kill myself.
# anyway, we use the ruby unmarshal to parse MapInfos.rxdata (simple file)
# and use it to get the *actual names* of the regions (fuck the encounters.txt file)
# the ``encounters.txt`` file does have the names, but I don't trust them to be accurate.
# plus it looks like a bastard to parse them out anyway.

ENCOUNTER_SLOTS = {
    # tall grass or the likes
    "Land": [20, 15, 12, 10, 10, 10, 5, 5, 5, 4, 2, 2],
    # caves, any step has a pokemon chance
    "Cave": [20, 15, 12, 10, 10, 10, 5, 5, 5, 4, 2, 2],
    # surfing/diving
    "Water": [50, 25, 15, 7, 3],
    # use rock smash in the overworld
    "RockSmash": [50, 25, 15, 7, 3],
    # fishing
    "OldRod": [70, 30],
    "GoodRod": [60, 20, 20],
    "SuperRod": [40, 35, 15, 7, 3],
    # no clue, the same in code mostly
    "HeadbuttLow": [30, 25, 20, 10, 5, 5, 4, 1],
    "HeadbuttHigh": [30, 25, 20, 10, 5, 5, 4, 1],
    # like land, but at specific time slots...
    "LandMorning": [20, 15, 12, 10, 10, 10, 5, 5, 5, 4, 2, 2],
    "LandDay": [20, 15, 12, 10, 10, 10, 5, 5, 5, 4, 2, 2],
    "LandNight": [20, 15, 12, 10, 10, 10, 5, 5, 5, 4, 2, 2],
}


class EncounterParsingState(enum.Enum):
    #: The initial state, i.e. waiting for a single number.
    INITIAL = 0

    #: We've just parsed a single number, and are waiting for the list of encounter chances.
    READING_CHANCES = 1

    #: We've just parsed the encounter chances, and are waiting for a single word defining the
    #: type of encounter this pool is for.
    READING_NAME = 2

    #: We've just parsed the encounter pool type, now we're reading the body.
    #: This can switch to READING_CHANCES, or READING_NAME.
    READING_ENCOUNTER_POOL = 3


@attr.s(frozen=True, slots=True, kw_only=True)
class RawEncounter:
    """
    A single encounter in the encounters file.
    """

    #: The name of the Pokémon to be encountered.
    name: str = attr.ib()

    #: The minimum level in the level range.
    minimum_level: int = attr.ib()

    #: The maximum level in the level range.
    maximum_level: int = attr.ib()


@attr.s(frozen=True, slots=True, kw_only=True)
class MapEncounters:
    """
    Wraps the full data about encounters for a specific map.
    """

    #: Land Encounter Rate, Cave Encounter Rate, Water Encounter Rate.
    chances: tuple[int, int, int] = attr.ib()

    #: The actual mapping of {type: list of encounters} for this map.
    encounters: dict[str, list[RawEncounter]] = attr.ib()

    def write_out(self, buffer: TextIO):
        """
        Writes the data in this object out in PBS format.
        """

        buffer.write(",".join(map(str, self.chances)))
        buffer.write("\n")

        for header, elist in self.encounters.items():
            buffer.write(header)
            buffer.write("\n")

            for item in elist:
                buffer.write(f"{item.name},{item.minimum_level}")

                if item.maximum_level > item.minimum_level:
                    buffer.write(f",{item.maximum_level}")

                buffer.write("\n")


class EncounterParser(object):
    """
    Parses the ``encounters.txt`` file.
    """

    #: The available encounter types.
    ENCOUNTER_TYPES = {
        "Land",
        "Cave",
        "Water",
        "RockSmash",
        "OldRod",
        "GoodRod",
        "SuperRod",
        "HeadbuttLow",
        "HeadbuttHigh",
        "LandMorning",
        "LandDay",
        "LandNight",
    }

    def __init__(self, path: Path):
        self.path = path

        self._current_mapping: dict[str, list[RawEncounter]] = {}
        self._maps: dict[int, MapEncounters] = {}

        #: The last map ID we've seen.
        self.last_map_id: int | None = None

        #: The last encounter type we've seen.
        self.last_encounter_type: str | None = None

        #: The last encounter rates we've seen.
        self.last_encounter_rate: tuple[int, int, int] | None = None

        #: The list of Pokémon in the current encounter type.
        self.current_encounters: list[RawEncounter] = []
        self.state: EncounterParsingState = EncounterParsingState.INITIAL

    def _push_encounter_list(self):
        """
        Pushes the current encounter list to the current encounter storage.
        """

        if not self.last_encounter_type:
            return

        self._current_mapping[self.last_encounter_type] = self.current_encounters
        self.last_encounter_type = None
        self.current_encounters = []

    def _push_map(self):
        assert self.last_map_id, "no map?"
        assert self.last_encounter_rate, "no encounter rate?"

        # make sure the trailing encounters are added on
        self._push_encounter_list()

        self._maps[self.last_map_id] = MapEncounters(
            chances=self.last_encounter_rate, encounters=self._current_mapping
        )
        self.last_encounter_rate = None
        self._current_mapping = {}
        self.last_map_id = None

    def _parse_name(self, line: str):
        if line not in self.ENCOUNTER_TYPES:
            raise ValueError(f"no such encounter type {line}")

        self._push_encounter_list()
        self.last_encounter_type = line
        self.state = EncounterParsingState.READING_ENCOUNTER_POOL

    def parse(self) -> dict[int, MapEncounters]:
        """
        Parses the entire encounters file.
        """

        if self.state != EncounterParsingState.INITIAL:
            raise ValueError("parser has already completed")

        content = self.path.read_text(encoding="utf-8").splitlines()

        for line in content:
            if line.startswith("#"):
                continue

            # strip trailing comments
            comma_idx = line.rfind("#")
            if comma_idx >= 0:
                line = line[: line.rfind("#")]

            if not line:
                continue

            # explicit ordered states first.
            if self.state == EncounterParsingState.INITIAL:
                # Initial state: the first line (post comments) is the map ID.
                self.last_map_id = int(line)
                self.state = EncounterParsingState.READING_CHANCES
                continue

            if self.state == EncounterParsingState.READING_CHANCES:
                # The first line of a map's encounter data can be a three-entry item of
                # (land, cave, water). If so, we set the variables and move onto the next line.
                # Otherwise, we can assume it's an encounter type and fall-through.

                self.state = EncounterParsingState.READING_NAME

                if "," in line:
                    land, cave, water = map(int, line.split(","))
                    self.last_encounter_rate = (land, cave, water)
                    continue
                else:
                    # apparently the default values?
                    self.last_encounter_rate = (25, 10, 10)

            if self.state == EncounterParsingState.READING_NAME:
                # This is only set after a READING_CHANCES so we don't need to validate.

                self._parse_name(line)
                continue

            # otherwise, we need to determine by the content.
            try:
                map_id = int(line)
            except ValueError:
                # definitely not a map id.
                pass
            else:
                # only map ids can be single-int lines, so switch to that.
                # push off the last map and switch to the next one.
                self._push_map()
                self.last_map_id = map_id
                self.state = EncounterParsingState.READING_CHANCES
                continue

            # okay, not a map ID. maybe it's a header?
            if line in self.ENCOUNTER_TYPES:
                # it is!
                self._parse_name(line)
                continue

            # not a map ID or an encounter type. we can assume it's a pokemon entry.
            try:
                internal_name, lower_bound, higher_bound = line.split(",")
            except ValueError:
                internal_name, lower_bound = line.split(",")
                # for exact encounters?
                higher_bound = lower_bound

            pokemon = RawEncounter(
                name=internal_name, minimum_level=int(lower_bound), maximum_level=int(higher_bound)
            )
            self.current_encounters.append(pokemon)

        # push trailing encounters and maps so we don't miss any.
        self._push_map()

        return self._maps
