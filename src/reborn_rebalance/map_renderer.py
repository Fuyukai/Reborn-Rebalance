import re
from pathlib import Path
from typing import cast

from PIL import Image
from PIL.Image import Image as ImageKlass
from rgcompiler.map.tileset import DecompiledTileset
from rgss import RubyRpgMap, read_object_rgxp


def load_map(map_path: Path) -> tuple[int, RubyRpgMap]:
    """
    Loads a single map from the provided path.
    """

    map_id: int = int(re.findall(r"Map([0-9]{3,})\.rxdata", map_path.name)[0])
    raw_map = cast(RubyRpgMap, read_object_rgxp(map_path))
    return (map_id, raw_map)


def get_tile_image(
    cache: dict[int, Image.Image], tileset: DecompiledTileset, idx: int
) -> Image.Image | None:
    # yuck, gotta cache these eventually
    if idx >= 384:
        actual_idx = idx - 384
        image = tileset.image
    elif idx >= 48:
        subtile_group = (idx // 48) - 1
        subtile = tileset.subtiles[subtile_group]
        actual_idx = 0 if subtile.is_single_row else idx % 48
        image = subtile.image
    else:
        # blank tiles
        return None

    try:
        return cache[idx]
    except KeyError:
        pass

    # tilesets are made up of 32x32 tiles, 8 tiles wide. autotiles are 6 tiles tall too.
    col = actual_idx // 8
    row = actual_idx % 8

    col_pos = col * 32
    row_pos = row * 32
    cropped = image.crop((row_pos, col_pos, row_pos + 32, col_pos + 32))
    cropped.convert("RGBA")
    cache[idx] = cropped
    return cropped


def render_map(
    tilesets: list[DecompiledTileset],
    map_path: Path,
) -> ImageKlass:
    """
    Renders an RPG Maker XP map to an image.
    """

    cache: dict[int, Image.Image] = {}

    _, rpg_map = load_map(map_path)
    tileset = tilesets[rpg_map.tileset_id - 1]
    assert tileset
    image = Image.new(mode="RGBA", size=(rpg_map.width * 32, rpg_map.height * 32))

    for layer in (0, 1, 2):
        for xpos in range(rpg_map.width):
            for ypos in range(rpg_map.height):
                tile_idx = rpg_map.get_tile_at(layer, xpos, ypos)
                tile_image = get_tile_image(cache, tileset, tile_idx)

                if tile_image is None:
                    continue

                pasted_x = xpos * 32
                pasted_y = ypos * 32

                # PIL my behated
                # use the tile image as the mask to correctly blend alpha for higher layers

                mask = tile_image if tile_image.mode == "RGBA" else None  # what the hell, PIL?
                image.paste(tile_image, (pasted_x, pasted_y, pasted_x + 32, pasted_y + 32), mask)

    return image
