import sys
from pathlib import Path

from reborn_rebalance.map.map import render_map
from reborn_rebalance.map.tileset import load_all_tilesets


def main():
    try:
        input_dir = Path(sys.argv[1])
        overrides_dir = Path(sys.argv[2])
        output_dir = Path(sys.argv[3])
    except IndexError:
        print("usage: render-all-maps <input> <overrides> <output>")
        return 1

    tilesets = load_all_tilesets(input_dir)
    maps = input_dir.glob("**/Map*.rxdata")
    output_dir.mkdir(parents=True, exist_ok=True)

    for map_path in maps:
        if map_path.name == "MapInfos.rxdata":
            continue

        output_path = (output_dir / map_path.name).with_suffix(".png")
        if output_path.exists():
            continue

        override = overrides_dir / map_path.name
        if override.exists():
            output = render_map(tilesets, override)
        else:
            output = render_map(tilesets, map_path)

        output.save(output_path)

        print(f"Rendered: {map_path.name}")


if __name__ == "__main__":
    sys.exit(main())
