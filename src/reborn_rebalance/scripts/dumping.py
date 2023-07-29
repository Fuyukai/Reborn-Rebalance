import sys
from functools import partial
from pathlib import Path
from typing import Callable

from reborn_rebalance.pbs.catalog import EssentialsCatalog


def load_and_dump(
    intro: Callable[[Path], EssentialsCatalog], outro: Callable[[EssentialsCatalog, Path], None]
):
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

    catalog = intro(input_dir)
    outro(catalog, output_dir)


to_pbs = partial(
    load_and_dump, EssentialsCatalog.load_from_toml, EssentialsCatalog.save_to_essentials
)  # type: ignore
to_toml = partial(load_and_dump, EssentialsCatalog.load_from_pbs, EssentialsCatalog.save_to_toml)
