import sys
from pathlib import Path

from reborn_rebalance.pbs.serialisation import (
    load_single_trainer_file_toml,
    save_single_trainer,
)
from reborn_rebalance.pbs.trainer import TrainerCatalog


def main() -> int:
    """
    Turns empty StatWrappers into None for trainer files.
    """

    try:
        root_dir = Path(sys.argv[1]) / "trainers"
    except IndexError:
        print(f"usage: {sys.argv[0]} <path to data>")
        return 1

    for trainer_path in root_dir.rglob("*"):
        if trainer_path.suffix != ".toml":
            continue

        name, trainers_data = load_single_trainer_file_toml(trainer_path)
        catalog = TrainerCatalog(trainer_name=name, trainers=trainers_data)

        for tr in catalog.all_trainers():
            for poke in tr.pokemon:
                if poke.evs is not None and poke.evs.sum() == 0:
                    poke.evs = None

        save_single_trainer(trainer_path, catalog)

    return 0
