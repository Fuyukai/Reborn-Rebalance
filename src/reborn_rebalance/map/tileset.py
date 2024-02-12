import traceback
from collections.abc import Mapping
from functools import cached_property
from pathlib import Path
from types import MappingProxyType

import attr
from PIL import Image
from PIL.Image import Image as ImageKlass
from rubymarshal.classes import RubyObject, RubyString

from reborn_rebalance.scripts.unmarshal import RgssTable, unmarshal

#: The number of *extra tiles* in this tileset. These are the tiles corresponding to the
EXTRA_TILE_COUNT = 384


@attr.s(frozen=True, kw_only=True)
class RpgMakerTileset:
    """
    A single tileset in the tileset mapping.
    """

    TRANSPARENT = Image.new(mode="RGBA", size=(32, 32), color=None)

    @staticmethod
    def _decode_tileset(name: bytes | str) -> str:
        if isinstance(name, RubyString):
            return name.text

        elif isinstance(name, str):
            return name

        return name.decode(encoding="utf-8")

    #: The numeric ID for this tileset.
    numeric_id: int = attr.ib()

    #: The name of this tileset, e.g. ``City Outskirt``.
    name: str = attr.ib()

    #: The *filename* of this tileset, e.g. ``Outskirts``.
    filename: str = attr.ib(converter=_decode_tileset)

    #: The terrain tags for this tileset.
    raw_terrain_tags: list[int] = attr.ib()

    #: The list of tile images for this tileset.
    tileset_image: ImageKlass = attr.ib(init=False, default=None)

    _tileset_cache: dict[int, ImageKlass] = attr.ib(init=False, factory=dict)

    def load_image(self, tilesets_path: Path):
        image_path = (tilesets_path / self.filename).with_suffix(".png")
        if not image_path.exists():
            # fucking windows
            image_path = image_path.with_suffix(".PNG")

        # lol!
        object.__setattr__(self, "tileset_image", Image.open(image_path))
        self.tileset_image.load()

    @property
    def tile_count(self) -> int:
        """
        The number of tiles in this tileset.
        """

        return len(self.raw_terrain_tags) - 384

    def close(self):
        self.tileset_image.close()
        self._tileset_cache.clear()

    def get_tile_image(self, index: int) -> ImageKlass | None:
        """
        Gets the tile image for the provided tileset index. This takes a raw tileset ID.
        """

        # extremely un-process safe.
        # todo: autotile handling
        if index >= 384:
            index -= 384
        else:
            return None

        try:
            return self._tileset_cache[index]
        except KeyError:
            pass

        # tilesets are 32x32, 8 tiles wide, unlimited verticality.
        col = index // 8
        row = index % 8

        col_pos = col * 32
        row_pos = row * 32

        cropped = self.tileset_image.crop((row_pos, col_pos, row_pos + 32, col_pos + 32))
        self._tileset_cache[index] = cropped
        return cropped


@attr.s(kw_only=True)
class AllTilesets:
    """
    Wraps all the tilesets in an RPG Maker XP game.
    """

    #: Mapping of numeric ID -> tileset.
    tilesets: list[RpgMakerTileset | None] = attr.ib()

    @cached_property
    def by_name(self) -> Mapping[str, RpgMakerTileset | None]:
        """
        A mapping of tilesets by name.
        """

        return MappingProxyType({it.name: it for it in self.tilesets})


def load_all_tilesets(root_game_path: Path) -> AllTilesets:
    """
    Loads tileset data from the provided root game path (i.e. the one with the ``mkxp-z``
    executable.)
    """

    # TODO: figure out how the fuck to load auto tiles so there's not massive holes

    images_path = root_game_path / "Graphics" / "Tilesets"

    try:
        tilesets_path = root_game_path / "Data" / "tilesets.rxdata"
        tileset_data: list[RubyObject] = unmarshal(tilesets_path)
    except FileNotFoundError:
        tilesets_path = root_game_path / "Data" / "Tilesets.rxdata"
        tileset_data: list[RubyObject] = unmarshal(tilesets_path)

    tilesets: list[RpgMakerTileset | None] = [None] * len(tileset_data)

    for subobject in tileset_data:
        if not subobject:
            continue

        # annoyingly, RubyString doesn't have an __int__
        id = int(str(subobject.attributes["@id"]))
        name = str(subobject.attributes["@name"])
        tileset_name = subobject.attributes["@tileset_name"]
        if not tileset_name:
            print(f"skipping fucked up tileset {id} / {name}")
            continue

        terrain_tags_tbl: RgssTable = subobject.attributes["@terrain_tags"]
        terrain_tags = terrain_tags_tbl.raw_data

        assert len(terrain_tags) == terrain_tags_tbl.x, "unexpectedly 2d tileset"

        tileset = RpgMakerTileset(
            numeric_id=id, name=name, filename=tileset_name, raw_terrain_tags=terrain_tags
        )
        try:
            tileset.load_image(images_path)
        except FileNotFoundError:
            print(f"couldn't load tileset {id} {name}")
            traceback.print_exc()
        else:
            tilesets[tileset.numeric_id] = tileset

    return AllTilesets(tilesets=tilesets)
