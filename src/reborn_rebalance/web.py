import shutil
import sys
from pathlib import Path

import jinja2

from reborn_rebalance.changes import build_changelog
from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.move import MoveCategory


# todo: hardcode the paths less
def changelog_klass(before: int, after: int):
    if before > after:
        return "has-text-danger"
    else:
        return "has-text-success"


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

    catalog = EssentialsCatalog.load_from_toml(Path("./data"))
    changelog = build_changelog(catalog)

    loader = jinja2.FileSystemLoader(searchpath=Path("./templates").absolute())
    env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
    env.globals["catalog"] = catalog
    env.globals["changelog"] = changelog
    env.globals["MoveCategory"] = MoveCategory
    env.globals["changelog_klass"] = changelog_klass

    with (output_dir / "changelog.html").open(mode="w", encoding="utf-8") as f:
        f.write(env.get_template("changelog/page.html").render())

    with (output_dir / "species" / "list.html").open(mode="w", encoding="utf-8") as f:
        f.write(env.get_template("species/list.html").render(species_definitions=catalog.species))

    specific_mon_template = env.get_template("species/single.html")
    for idx, species in enumerate(catalog.species):
        path = output_dir / "species" / "specific" / species.internal_name.lower()
        path = path.with_suffix(".html")
        path.write_text(specific_mon_template.render(species=species, pokedex_number=idx + 1))

    # copy both sets of static data over
    shutil.copytree(Path("./templates/static"), output_dir / "static", dirs_exist_ok=True)
    shutil.copytree(Path("./sprites"), output_dir / "sprites", dirs_exist_ok=True)


if __name__ == "__main__":
    main()
