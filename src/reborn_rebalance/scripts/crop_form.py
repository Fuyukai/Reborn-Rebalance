import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from reborn_rebalance.pbs.catalog import EssentialsCatalog


def main(
    catalog: EssentialsCatalog,
    reborn_path: Path,
    dump_path: Path,
    species: str,
):
    root_species = catalog.species_mapping[species.upper()]
    forms = catalog.forms[species.upper()]
    form_count = max(forms.form_mapping.values())

    input_file = reborn_path / "Graphics" / "Battlers" / f"{root_species.dex_number:03d}.png"
    input_file = input_file.absolute()

    # could do a PIL native version. but yegh.
    with tempfile.TemporaryDirectory() as dir:
        path = str(Path(dir) / "%02d.png")
        subprocess.check_call(["magick", input_file, "-crop", f"2x{form_count * 2}@", path])

        for idx, name in forms.form_mapping.values():
            # front sprite is just (idx * 4).
            # eg normal form has 00 + 01, second form has 04 + 05, etc.
            front_sprite = idx * 4
            shiny_sprite = 1 + (idx * 4)

            regular_path = Path(dir) / f"{front_sprite:02d}.png"
            regular_output_path = dump_path / f"battler_{root_species.dex_number:04d}_{name}.png"
            shutil.copyfile(regular_path, regular_output_path)

            regular_path = Path(dir) / f"{shiny_sprite:02d}.png"
            regular_output_path = dump_path / f"battler_{root_species.dex_number:04d}_{name}.png"
            shutil.copyfile(regular_path, regular_output_path)


def run():
    catalog = EssentialsCatalog.load_only_species(Path("./data"))
    reborn_path = Path.home() / "aur/pokemon/reborn"
    dump_path = Path("./sprites/custom")
    species = sys.argv[1]

    main(catalog, reborn_path, dump_path, species)


if __name__ == "__main__":
    run()
