import shutil
import sys
from pathlib import Path

import jinja2

from reborn_rebalance.pbs.serialisation import load_all_species_from_yaml

# todo: hardcode the paths less


def main():
    try:
        output_dir = Path(sys.argv[1])
    except IndexError:
        output_dir = Path.cwd() / "website"

    try:
        shutil.rmtree(output_dir)
    except FileNotFoundError:
        pass

    output_dir.mkdir(exist_ok=True, parents=True)
    (output_dir / "species").mkdir(exist_ok=True, parents=True)
    (output_dir / "species" / "specific").mkdir(exist_ok=True, parents=True)

    loader = jinja2.FileSystemLoader(searchpath=Path("./templates").absolute())
    env = jinja2.Environment(loader=loader)

    # begin loading block
    species_defs = load_all_species_from_yaml(Path.cwd() / "data" / "species")

    # end loading block

    with (output_dir / "species" / "list.html").open(mode="w", encoding="utf-8") as f:
        f.write(env.get_template("species/list.html").render(species_definitions=species_defs))

    specific_mon_template = env.get_template("species/single.html")
    for idx, species in enumerate(species_defs):
        path = output_dir / "species" / "specific" / species.internal_name.lower()
        path = path.with_suffix(".html")
        path.write_text(specific_mon_template.render(species=species, pokedex_number=idx + 1))

    # copy both sets of static data over
    shutil.copytree(Path("./templates/static"), output_dir / "static", dirs_exist_ok=True)
    shutil.copytree(Path("./sprites"), output_dir / "sprites", dirs_exist_ok=True)


if __name__ == "__main__":
    main()
