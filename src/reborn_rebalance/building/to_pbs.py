import shutil
import sys
from pathlib import Path

from reborn_rebalance.pbs.catalog import EssentialsCatalog


def build_to_pbs() -> int:
    """
    CLI entrypoint for building the data provided into a format consumable by the game.
    """

    try:
        input_dir = Path(sys.argv[1]).absolute()
        output_dir = Path(sys.argv[2]).absolute()
    except IndexError:
        print(f"usage: {sys.argv[0]} <input data dir> <game dir>")
        return 1

    if not input_dir.exists():
        print(f"{input_dir} doesn't exist")
        return 1

    output_dir.mkdir(exist_ok=True, parents=True)
    catalog = EssentialsCatalog.load_from_toml(input_dir)
    catalog.save_to_essentials(output_dir)

    overridden_maps = input_dir / "overwritten_maps"
    if overridden_maps.exists():
        data_dir = output_dir / "Data"
        data_dir.mkdir(exist_ok=True, parents=True)

        for map in overridden_maps.glob("**/*.rxdata"):
            print(f"Copying map {map.stem}")
            new_path = data_dir / map.name
            shutil.copy2(map, new_path)


if __name__ == "__main__":
    sys.exit(build_to_pbs())
