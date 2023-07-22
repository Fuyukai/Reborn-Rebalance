import sys
from pathlib import Path

from reborn_rebalance.pbs.catalog import EssentialsCatalog


def main():
    """
    Dumps all of the PBS data into TOML files.
    """

    try:
        input_dir = Path(sys.argv[1]).absolute()
        output_dir = Path(sys.argv[2]).absolute()
    except IndexError:
        print(f"usage: {sys.argv[0]} <input PBS dir> <output YAML dir>")
        return 1

    if not input_dir.exists():
        print(f"{input_dir} doesn't exist")
        return 1

    output_dir.mkdir(exist_ok=True, parents=True)

    catalog = EssentialsCatalog.load_from_pbs(input_dir)
    catalog.save_to_toml(output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
