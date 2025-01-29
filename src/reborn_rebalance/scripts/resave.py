import sys
from pathlib import Path

from reborn_rebalance.pbs.catalog import EssentialsCatalog


def main() -> int:
    """
    Resaves certain data to adjust to the new formatting.
    """

    try:
        path = Path(sys.argv[1])
        new_path = Path(sys.argv[2])
    except IndexError:
        print(f"usage: {sys.argv[0]} <path to data directory> <path to new directory>")
        return 1

    new_path.mkdir(exist_ok=True, parents=True)

    catalog = EssentialsCatalog.load_from_toml(path, skip_validation=True)
    catalog.save_to_toml(new_path)

    return 0


if __name__ == "__main__":
    main()
