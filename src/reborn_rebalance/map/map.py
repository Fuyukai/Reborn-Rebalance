import enum
import math
import re
import sys
from pathlib import Path

import attr
from PIL import Image
from PIL.Image import Image as ImageKlass

from reborn_rebalance.map.tileset import AllTilesets, load_all_tilesets
from reborn_rebalance.scripts.unmarshal import RgssTable, unmarshal

# TODO: event parsing. yeah, eventually i wanna show that on the docs too (esp. if this turns into
#       a more general purpose essentials transpiler).


class MapLayer(enum.IntEnum):
    LOWEST = 0
    MIDDLE = 1
    HIGHEST = 2


@attr.s(frozen=True, slots=True, kw_only=True)
class MapBgm:
    volume: int = attr.ib()
    name: str = attr.ib()
    pitch: str = attr.ib()


@attr.s(kw_only=True, slots=True)
class RpgMakerMap:
    """
    A single RPG Maker XP map.
    """

    #: The ID of this map.
    id: int = attr.ib()

    #: The dimensions of this map, (width, height).
    dimensions: tuple[int, int] = attr.ib()

    #: The ID of the tileset for this map.
    tileset_id: int = attr.ib()

    #: The background music that plays in this map.
    bgm: MapBgm | None = attr.ib()

    #: The raw table of tiles for this map.
    tiles: RgssTable = attr.ib()

    @property
    def height(self) -> int:
        return self.dimensions[1]

    @property
    def width(self) -> int:
        return self.dimensions[0]

    @property
    def tiles_per_layer(self) -> int:
        return math.prod(self.dimensions)

    def get_tile_idx(self, layer: MapLayer, x: int, y: int) -> int:
        """
        Gets the raw tileset tile (i.e., not normalised within bounds) for the specified tile.
        """

        # serialised in three layers, bottom to top.
        offset = int(layer) * self.tiles_per_layer
        # serialised in rows of tiles, then Y down.
        offset += self.width * y
        offset += x

        return self.tiles.raw_data[offset]


def load_map(map_path: Path) -> RpgMakerMap:
    """
    Loads a single map from the provided path.
    """

    map_id: int = int(re.findall(r"Map([0-9]{3,})\.rxdata", map_path.name)[0])
    raw_data = unmarshal(map_path).attributes  # type: ignore
    tileset_id = raw_data["@tileset_id"]

    raw_bgm = raw_data["@bgm"].attributes
    if raw_bgm["@name"]:
        music = MapBgm(
            volume=raw_bgm["@volume"], name=str(raw_bgm["@name"]), pitch=raw_bgm["@pitch"]
        )
    else:
        music = None

    dimensions = (raw_data["@width"], raw_data["@height"])
    tile_data: RgssTable = raw_data["@data"]

    assert (tile_data.x, tile_data.y) == dimensions, "wtf?"

    return RpgMakerMap(
        id=map_id,
        tileset_id=tileset_id,
        dimensions=dimensions,
        bgm=music,
        tiles=tile_data,
    )


def render_map(
    tilesets: AllTilesets,
    map_path: Path,
) -> ImageKlass:
    """
    Renders an RPG Maker XP map to an image.
    """

    rpg_map = load_map(map_path)
    tileset = tilesets.tilesets[rpg_map.tileset_id]
    assert tileset
    image = Image.new(mode="RGBA", size=(rpg_map.width * 32, rpg_map.height * 32))

    for layer in (0, 1, 2):
        layer = MapLayer(layer)

        for xpos in range(rpg_map.width):
            for ypos in range(rpg_map.height):
                tile_idx = rpg_map.get_tile_idx(layer, xpos, ypos)

                tile_image = tileset.get_tile_image(tile_idx)

                if tile_image is None:
                    continue

                pasted_x = xpos * 32
                pasted_y = ypos * 32

                # PIL my behated
                # use the tile image as the mask to correctly blend alpha for higher layers
                image.paste(
                    tile_image, (pasted_x, pasted_y, pasted_x + 32, pasted_y + 32), tile_image
                )

    return image


if __name__ == "__main__":

    def main():
        root_path = Path(sys.argv[1])
        map_path = root_path / "Data" / f"Map{int(sys.argv[2]):03d}.rxdata"

        tilesets = load_all_tilesets(root_path)
        rendered_map = render_map(tilesets, map_path)
        rendered_map.save(Path(sys.argv[3]))

    main()
