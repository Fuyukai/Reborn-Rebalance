from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import cast

import attrs
from rgss import RubyRpgMap, read_object_rgxp

from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.tm import TM_NUMBER_REGEXP
from reborn_rebalance.ruby.event import (
    EVENT_PICKER,
    PickedEventCommand,
    ReceivedTechnicalMachineCommand,
    StaticEncounterCommand,
)


def eager_process_map(map: Path) -> tuple[str, list[PickedEventCommand]]:
    obb = cast(RubyRpgMap, read_object_rgxp(map))
    return map.stem[3:], list(EVENT_PICKER.pick_events(obb))


@attrs.define(kw_only=True, slots=False)
class EventCatalog:
    """
    A wrapper for static events for usage in the web renderer.
    """

    real_catalog: EssentialsCatalog = attrs.field()

    # raw species -> {map: command}
    static_encounters: dict[str, list[tuple[int, StaticEncounterCommand]]] = attrs.field(
        factory=lambda: defaultdict(list)
    )

    # TM number -> map
    tm_maps: dict[int, tuple[int, ReceivedTechnicalMachineCommand]] = attrs.field(
        factory=dict,
    )

    @classmethod
    def load(cls, project_dir: Path, catalogue: EssentialsCatalog) -> EventCatalog:
        map_files = [
            i for i in (project_dir / "Data").glob("Map**.rxdata") if i.name != "MapInfos.rxdata"
        ]
        instance = EventCatalog(real_catalog=catalogue)

        with ProcessPoolExecutor() as executor:
            for map_name, processed_map in executor.map(eager_process_map, map_files):
                for event in processed_map:
                    if isinstance(event, StaticEncounterCommand):
                        instance.static_encounters[event.raw_species_name].append(
                            (int(map_name), event)
                        )

                    elif isinstance(event, ReceivedTechnicalMachineCommand):
                        # this one is a bit harder due to how stupid reborn's events are
                        item = catalogue.item_mapping[event.item_name]
                        tm_match = TM_NUMBER_REGEXP.match(item.display_name)
                        if not tm_match:
                            # wtf?
                            continue

                        if item.display_name.startswith("TMX"):
                            continue

                        tm_number = int(tm_match.groups()[1])
                        instance.tm_maps[tm_number] = (int(map_name), event)

        return instance
