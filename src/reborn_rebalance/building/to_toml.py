import sys
from pathlib import Path

from reborn_rebalance.pbs.catalog import EssentialsCatalog


def import_to_toml():
    try:
        input_dir = Path(sys.argv[1]).absolute()
        output_dir = Path(sys.argv[2]).absolute()
    except IndexError:
        print(f"usage: {sys.argv[0]} <input game dir> <output data dir>")
        return 1

    if not input_dir.exists():
        print(f"{input_dir} doesn't exist")
        return 1

    output_dir.mkdir(exist_ok=True, parents=True)
    catalog = EssentialsCatalog.load_from_pbs(input_dir)
    catalog.save_to_toml(output_dir)

    print(f"Imported game data to {output_dir} successfully")


if __name__ == "__main__":
    import_to_toml()
