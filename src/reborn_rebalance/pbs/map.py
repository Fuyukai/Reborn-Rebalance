from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import attr
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn, override
from rubymarshal.classes import RubyString
from rubymarshal.reader import loads

from reborn_rebalance.util import PbsBuffer

# global metadata, nothing to do with other metadata
MAP_DATA_HEADER = """[000]
Home=38,5,22,8
PlayerA=PkMnTRAINER_Male,boy_walk,boy_bike,boy_surf,boy_run,boy_dive,fishing000,fishing000surf
PlayerB=PkMnTRAINER_Female,girl_walk,girl_bike,girl_surf,girl_run,girl_dive,fishing001,fishing001surf
PlayerC=PkMnTRAINER_Male,pkmn_tauros2,boy_bike,boy_surf,boy_run,boy_dive,fishing000,fishing000surf
PlayerD=PkMnTRAINER_Female,pkmn_tauros3,girl_bike,girl_surf,girl_run,girl_dive,fishing001,fishing001surf
PlayerE=PkMnTRAINER_Male2,boy2_walk,boy2_bike,boy2_surf,boy2_run,boy2_dive,fishing004,fishing004surf
PlayerF=PkMnTRAINER_Female2,girl2_walk,girl2_bike,girl2_surf,girl2_run,girl2_dive,fishing005,fishing005surf
PlayerG=PkMnTRAINER_Male2,pkmn_tauros4,boy2_bike,boy2_surf,boy2_run,boy2_dive,fishing004,fishing004surf
PlayerH=PkMnTRAINER_Female2,pkmn_tauros5,girl2_bike,girl2_surf,girl2_run,girl2_dive,fishing005,fishing005surf
PlayerI=PkMnTRAINER_NB,nb_walk,nb_bike,nb_surf,nb_run,nb_dive,fishing006,fishing006surf
PlayerJ=PkMnTRAINER_NB2,nb2_walk,nb2_bike,nb2_surf,nb2_run,nb2_dive,fishing007,fishing007surf
PlayerK=PkMnTRAINER_NB,pkmn_tauros6,nb_bike,nb_surf,nb_run,nb_dive,,
PlayerL=PkMnTRAINER_NB2,pkmn_tauros7,nb2_bike,nb2_surf,nb2_run,nb2_dive,,
PlayerM=SIGMUND,trchar184,trchar184,trchar184,trchar184,trchar184,,
PlayerN=Taka2,trchar071,trchar071,trchar071,trchar071,trchar071,,
PlayerO=ZTAKA2,trchar071c,trchar071c,trchar071c,trchar071c,trchar071c,,
PlayerP=ZEL3,trchar070b,trchar070b,trchar070b,trchar070b,trchar070b,,
TrainerVictoryME=Victory!.ogg
WildVictoryME=Victory!.ogg
TrainerBattleBGM=Battle- Trainer.ogg
SurfBGM=Atmosphere- Surfing.ogg
BicycleBGM=Atmosphere- Rush.ogg
WildBattleBGM=Battle- Wild.ogg
"""

FIELD_NAMES = {
    "Electric": "Electric Terrain",
    "Grassy": "Grassy Terrain",
    "Misty": "Misty Terrain",
    "DarkCrystalCavern": "Dark Crystal Cavern",
    "Chess": "Chess Board",
    "BigTop": "Big Top Arena",
    "Burning": "Burning Field",
    "Swamp": "Swamp Field",
    "Rainbow": "Rainbow Field",
    "Corrosive": "Corrosive Field",
    "CorrosiveMist": "Corrosive Mist Field",
    "Desert": "Desert Field",
    "Icy": "Icy Field",
    "Rocky": "Rocky Field",
    "Forest": "Forest Field",
    "Superheated": "Super-Heated Field",
    "Factory": "Factory Field",
    "Shortcircuit": "Short-Circuit Field",
    "Wasteland": "Wasteland",
    "AshenBeach": "Ashen Beach",
    "WaterSurface": "Water Surface",
    "Underwater": "Underwater",
    "Cave": "Cave",
    "Glitch": "Glitch Field",
    "CrystalCavern": "Crystal Cavern",
    "MurkwaterSurface": "Murkwater Surface",
    "Mountain": "Mountain",
    "SnowyMountain": "Snowy Mountain",
    "Holy Field": "Holy",  # is that a fucking toaru reference??????!!!?!?!?
    "Mirror": "Mirror Arena",
    "FairyTale": "Fairy Tale Field",
    "DragonsDen": "Dragon's Den",
    "FlowerGarden0": "Flower Garden Field",
    "Starlight": "Starlight Arena",
    "NewWorld": "New World",
    "Inverse": "Inverse Field",
    "Psychic": "Psychic Terrain",
}


@attr.s(kw_only=True)
class MapMetadata:
    """
    Contains external metadata about a map.
    """

    #: The ID of this map.
    id: int = attr.ib()

    #: The parent ID of this map. Backfilled.
    parent_id: int = attr.ib(default=None)

    # backfilled from MapInfos.rxdata
    #: The name of this map.
    name: str = attr.ib(default=None)

    #: The position for this map. 3-int tuple. No clue what this means.
    map_position: tuple[int, int, int] | None = attr.ib(default=None)

    #: The trainer battle BGM for this map.
    trainer_battle_music: str | None = attr.ib(default=None)

    #: The wild battle BGM for this map.
    wild_battle_music: str | None = attr.ib(default=None)

    #: If this map is an outdoors map. Mostly controls rendering, so dark maps look dark at night
    #: and etc.
    is_outdoors: bool = attr.ib(default=False)

    #: If true, the tooltip for this area will be shown when entering the map.
    show_area_tooltip: bool = attr.ib(default=False)

    #: If it is possible to use the bicycle in this area.
    can_use_bicycle: bool = attr.ib(default=False)

    #: A 3-tuple of (map ID, entrance X, entrance Y) of the Pokémon Centre for this map.
    healing_spot: tuple[int, int, int] | None = attr.ib(default=None)

    # TODO: Make this an enum
    #: The possible weather conditions for this map. Tuple of (name, probability).
    weather: tuple[str, int] | None = attr.ib(default=None)

    #: The map ID for the map to switch to when using the Dive HM.
    dive_map_id: int | None = attr.ib(default=None)

    #: If true, this map is dark and only shows a small area around the player.
    is_dark: bool = attr.ib(default=False)

    #: If true, this map is part of the Safari Zone.
    is_safari_zone: bool = attr.ib(default=False)

    #: No clue what this means. Unused by Reborn.
    snap_edges: bool = attr.ib(default=False)

    #: If true, the layout is randomly generated (?).
    is_dungeon: bool = attr.ib(default=False)

    #: The battle background for this map. This also controls the field effect, if any.
    battle_background: str | None = attr.ib(default=None)

    # in reborn, these are only really used for the Terra nonsense.
    #: The sound effect played after winning a wild battle.
    wild_victory_sfx: str | None = attr.ib(default=None)

    #: The sound effect played after winning a trainer battle.
    trainer_victory_sfx: str | None = attr.ib(default=None)

    #: The width (?) of the map? Not used by Reborn.
    map_size: str | None = attr.ib(default=None)

    # used to avoid O(N^2) loop in the map template rendering code.
    child_maps: set[int] = attr.ib(init=False, factory=set)

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        unst_hook = make_dict_unstructure_fn(
            cls,
            converter,
            child_maps=override(omit=True),  # virtual field
            _cattrs_omit_if_default=True,
        )
        converter.register_unstructure_hook(cls, unst_hook)

    @classmethod
    def from_pbs(cls, id: int, data: dict[str, str | int]) -> MapMetadata:
        """
        Parses a single set of map metadata from a PBS section. This requires backfilling in
        the name field.
        """

        is_outdoors = data.pop("Outdoor", "false") == "true"

        if "MapPosition" in data:
            map_position = tuple(map(int, cast(str, data.pop("MapPosition")).split(",")))
        else:
            map_position = None

        trainer_battle_music: str | None = cast(str | None, data.pop("TrainerBattleBGM", None))
        wild_battle_music: str | None = cast(str | None, data.pop("WildBattleBGM", None))

        # thanks, all-gen patch guy
        if "Showarea" in data:
            show_area_tooltip = data.pop("Showarea", "false") == "true"
        else:
            show_area_tooltip = data.pop("ShowArea", "false") == "true"

        can_use_bicycle = data.pop("Bicycle", "false") == "true"
        raw_healing_spot = data.pop("HealingSpot", None)
        healing_spot = (
            tuple(map(int, cast(str, raw_healing_spot).split(","))) if raw_healing_spot else None
        )

        weather: tuple[str, int] | None = None
        raw_weather = data.pop("Weather", None)
        if isinstance(raw_weather, str):
            weather_split = raw_weather.split(",", 2)
            weather = (weather_split[0], int(weather_split[1]))

        dive_map_id = cast(int | None, data.pop("DiveMap", None))
        safari_zone = data.pop("SafariMap", "false") == "true"
        is_dark = data.pop("DarkMap", "false") == "true"
        snap_edges = data.pop("SnapEdges", "false") == "true"
        is_dungeon = data.pop("Dungeon", "false") == "true"
        battle_background = cast(str | None, data.pop("BattleBack", None))
        if battle_background is None:
            print(f"warning: map {id} has missing battle background")

        wild_victory_sfx = cast(str | None, data.pop("WildVictoryME", None))
        trainer_victory_sfx = cast(str | None, data.pop("TrainerVictoryME", None))
        map_size = cast(str | None, data.pop("MapSize", None))

        # always false in the reborn metadata.
        # TODO: maybe store this for other games?
        data.pop("BicycleAlways", None)

        if data:
            raise ValueError(f"unknown map metadata: {data}")

        return cls(
            id=id,
            name=None,  # type: ignore
            map_position=map_position,  # type: ignore
            trainer_battle_music=trainer_battle_music,
            wild_battle_music=wild_battle_music,
            is_outdoors=is_outdoors,
            show_area_tooltip=show_area_tooltip,
            can_use_bicycle=can_use_bicycle,
            healing_spot=cast(tuple[int, int, int], healing_spot),
            weather=weather,
            dive_map_id=dive_map_id,
            is_dark=is_dark,
            is_safari_zone=safari_zone,
            snap_edges=snap_edges,
            is_dungeon=is_dungeon,
            battle_background=battle_background,
            wild_victory_sfx=wild_victory_sfx,
            trainer_victory_sfx=trainer_victory_sfx,
            map_size=map_size,
        )

    def to_pbs(self, buffer: PbsBuffer):
        """
        Writes this map metadata to the provided PBS buffer.
        """

        buffer.write_comment(self.name)

        # all of these are guarded with an if to make roundtripping "better".

        if self.battle_background:
            buffer.write_key_value("BattleBack", self.battle_background)

        if self.map_position:
            buffer.write_key_value("MapPosition", ",".join(map(str, self.map_position)))

        if self.trainer_battle_music:
            buffer.write_key_value("TrainerBattleBGM", self.trainer_battle_music)

        if self.wild_battle_music:
            buffer.write_key_value("WildBattleBGM", self.wild_battle_music)

        if self.is_outdoors:
            buffer.write_key_value("Outdoor", "true")

        if self.show_area_tooltip:
            buffer.write_key_value("ShowArea", "true")

        if self.can_use_bicycle:
            buffer.write_key_value("Bicycle", "true")

        if self.healing_spot:
            buffer.write_key_value("HealingSpot", ",".join(map(str, self.healing_spot)))

        if self.weather:
            buffer.write_key_value("Weather", ",".join([str(s) for s in self.weather]))

        if self.dive_map_id:
            buffer.write_key_value("DiveMap", self.dive_map_id)

        if self.is_dark:
            buffer.write_key_value("DarkMap", "true")

        if self.is_safari_zone:
            buffer.write_key_value("SafariMap", "true")

        if self.snap_edges:
            buffer.write_key_value("SnapEdges", "true")

        if self.is_dungeon:
            buffer.write_key_value("Dungeon", "true")

        if self.wild_victory_sfx:
            buffer.write_key_value("WildVictoryME", self.wild_victory_sfx)

        if self.trainer_victory_sfx:
            buffer.write_key_value("TrainerVictoryME", self.trainer_victory_sfx)

        if self.map_size:
            buffer.write_key_value("MapSize", self.map_size)


@attr.s(slots=True, frozen=True, kw_only=True)
class RawMapInfo:
    """
    Raw RPG maker map info for a single map.
    """

    #: The name of this map in the editor.
    name: str = attr.ib()

    #: The parent ID for this map.
    parent_id: int = attr.ib()


def parse_rpg_maker_mapinfo(map_info_path: Path) -> dict[int, RawMapInfo]:
    """
    Parses the map info file and returns a dict of {map id: map name}.
    """

    content = map_info_path.read_bytes()
    unmarshalled = loads(content)

    items = {}
    for id, obb in unmarshalled.items():
        attrs: dict[str, Any] = obb.attributes

        raw_name = attrs["@name"]
        if isinstance(raw_name, RubyString):
            name: str = raw_name.text
        elif isinstance(raw_name, bytes):
            # wtf?
            name: str = raw_name.decode(encoding="utf-8")
        else:
            raise ValueError(f"illegal map name: {raw_name}")

        parent = int(attrs["@parent_id"])

        if name == "REMOVED":
            print(f"warning: removed map: {id}")

        print("loaded map", name, parent)
        items[id] = RawMapInfo(name=name, parent_id=parent)

    return dict(sorted(items.items()))
