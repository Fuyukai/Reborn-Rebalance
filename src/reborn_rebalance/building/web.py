from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import attr
import jinja2
import rtoml
from PIL import Image
from tqdm import tqdm

from reborn_rebalance.changes import build_changelog
from reborn_rebalance.map.map import render_map
from reborn_rebalance.map.tileset import load_all_tilesets
from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.encounters import ENCOUNTER_SLOTS
from reborn_rebalance.pbs.map import FIELD_NAMES
from reborn_rebalance.pbs.move import MoveCategory


@attr.s(slots=True, kw_only=True)
class MapSidebarEntry:
    #: The ID for this map entry.
    id: int | None = attr.ib()

    #: The name for this map entry.
    name: str | None = attr.ib()

    #: The list of submaps for this map entry.
    submaps: list[MapSidebarEntry] = attr.ib(factory=list)


def _recursive_navbar_entry(catalog: EssentialsCatalog, entry: dict[str, Any]) -> MapSidebarEntry:
    if isinstance(entry, int):
        return MapSidebarEntry(id=entry, name=catalog.maps[entry].name, submaps=[])

    id = entry.get("id", None)  # fake maps have no id and are just used for grouping
    name = entry.get("name")
    if not name and id:
        name = catalog.maps[id].name

    submaps = [_recursive_navbar_entry(catalog, subentry) for subentry in entry.get("submaps", [])]

    return MapSidebarEntry(id=id, name=name, submaps=submaps)


def load_navbar_maps(catalog: EssentialsCatalog, path: Path) -> list[MapSidebarEntry]:
    """
    Loads the map links for the navigation bar.
    """

    raw_data = rtoml.loads(path.read_text())
    entires: list[MapSidebarEntry] = []

    for entry in raw_data["maps"]:
        parsed = _recursive_navbar_entry(catalog, entry)
        entires.append(parsed)

    return entires


@attr.s(kw_only=True)
class WalkthroughEntry:
    """
    A root entry in the navbar walkthrough view.
    """

    #: The name for this entry.
    name: str = attr.ib()

    #: The list of chapters for this entry.
    #: Tuple of (internal name, display name).
    chapters: list[tuple[str, str]] = attr.ib(factory=list)


def load_navbar_walkthroughs(path: Path) -> list[WalkthroughEntry]:
    """
    Loads the walkthrough links for the navigation bar.
    """

    raw_data = rtoml.loads(path.read_text())
    entries: list[WalkthroughEntry] = []

    for name, data in raw_data["section"].items():
        entry = WalkthroughEntry(name=name)
        for chapter in data.get("chapters", []):
            entry.chapters.append((chapter["name"], chapter["text"]))

        entries.append(entry)

    return entries


def crop_form_sprites(catalog: EssentialsCatalog, game_dir: Path, output_dir: Path):
    """
    Crops all form sprites from the original files.

    :param catalog: the catalog to load from
    :param game_dir: the game dir to load the sprites from
    :param output_dir: the dir to place the cropped form sprites in
    """

    for species in tqdm(catalog.species, desc="Form Sprites"):
        try:
            forms = catalog.forms[species.internal_name.upper()]
        except KeyError:
            continue

        # weh
        if not forms.form_mapping:
            continue

        form_count = max(forms.form_mapping.keys()) + 1

        if species.internal_name == "URSHIFU":
            # don't remember why I added this special case.
            form_count += 2

        elif forms.has_dynamax_form:
            # dynamax forms add an extra 4 tiles, so imagemagick will crop it but we discard it.
            form_count += 1

        input_file = game_dir / "Graphics" / "Battlers" / f"{species.dex_number:03d}.png"
        input_file = input_file.absolute()

        # could do a PIL native version. but yegh.
        with tempfile.TemporaryDirectory() as dir:
            path = str(Path(dir) / "%02d.png")
            subprocess.check_call(["magick", input_file, "-crop", f"2x{form_count * 2}@", path])

            for idx, name in forms.form_mapping.items():
                # front sprite is just (idx * 4).
                # eg normal form has 00 + 01, second form has 04 + 05, etc.
                front_sprite = idx * 4
                shiny_sprite = 1 + (idx * 4)

                regular_path = Path(dir) / f"{front_sprite:02d}.png"
                regular_output_path = output_dir / f"battler_{species.dex_number:04d}_{name}.png"
                shutil.copyfile(regular_path, regular_output_path)

                shiny_path = Path(dir) / f"{shiny_sprite:02d}.png"
                shiny_output_path = (
                    output_dir / f"battler_{species.dex_number:04d}_{name}_shiny.png"
                )
                shutil.copyfile(shiny_path, shiny_output_path)


def crop_regular_sprites(catalog: EssentialsCatalog, original_dir: Path, output_path: Path):
    """
    Crops all regular sprites for all species.

    :param catalog: the catalog, containing all the species
    :param original_dir: the root directory of the original game
    :param output_path: where to write the cropped sprites
    """

    for species in tqdm(catalog.species, desc="Species Sprites"):
        idx = species.dex_number
        input_mini_sprite = original_dir / "Graphics" / "Icons" / f"icon{idx:03d}.png"

        with Image.open(input_mini_sprite) as input_1, Image.open(input_mini_sprite) as input_2:
            input_1.load()
            input_2.load()

            output_normal = Image.new(mode="RGBA", size=(64, 64), color=None)  # type: ignore
            cropped_normal = input_1.crop((0, 0, 64, 64))
            output_normal.paste(cropped_normal)

            output_shiny = Image.new(mode="RGBA", size=(64, 64), color=None)  # type: ignore
            cropped_shiny = input_2.crop((128, 0, 192, 64))
            output_shiny.paste(cropped_shiny)

            output_normal.save(output_path / f"{idx:04d}.png", compress_level=9)
            output_shiny.save(output_path / f"{idx:04d}_shiny.png", compress_level=9)

        inp_battler = original_dir / "Graphics" / "Battlers" / f"{idx:03d}.png"
        with Image.open(inp_battler) as input_1, Image.open(inp_battler) as input_2:
            input_1.load()
            input_2.load()

            output_normal = Image.new(mode="RGBA", size=(192, 192), color=None)  # type: ignore
            cropped_normal = input_1.crop((0, 0, 192, 192))
            output_normal.paste(cropped_normal)

            output_shiny = Image.new(mode="RGBA", size=(192, 192), color=None)  # type: ignore
            cropped_shiny = input_2.crop((192, 0, 384, 192))
            output_shiny.paste(cropped_shiny)

            output_normal.save(output_path / f"battler_{idx:04d}.png", compress_level=9)
            output_shiny.save(output_path / f"battler_{idx:04d}_shiny.png", compress_level=9)


def render_all_maps(
    catalog: EssentialsCatalog,
    game_dir: Path,
    data_dir: Path,
    output_dir: Path,
):
    tilesets = load_all_tilesets(game_dir)

    for map_id in tqdm(catalog.maps.keys(), desc="Map Rendering"):
        map_name = f"Map{map_id:03d}.rxdata"
        map_path = data_dir / "overwritten_maps" / map_name
        if not map_path.exists():
            map_path = game_dir / "Data" / map_name

        output_path = (output_dir / map_path.name).with_suffix(".png")
        if output_path.exists():
            continue

        with render_map(tilesets, map_path) as output:
            output.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="Automatic web documentation builder")

    parser.add_argument(
        "--game-dir", help="The game directory to load sprites from.", type=Path, default=None
    )
    parser.add_argument(
        "--image-cache-location",
        help="The location to cache battler sprites and map renderers. ",
        type=Path,
        default=Path.cwd() / "sprites",
    )
    parser.add_argument(
        "--crop-regular-sprites",
        help=(
            "Generates cropped input battler sprites before building. Only needs to be done if "
            "battler sprites changed"
        ),
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--crop-form-sprites",
        help=(
            "Generates cropped form battler sprites before building. Only needs to be done if "
            "battler sprites changed"
        ),
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--render-maps",
        help="Generates rendered map files (WIP). Only needs to be done if maps changed",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "INPUT", help="The input data directory", type=Path, default=Path.cwd() / "data"
    )
    # TODO: bundle these
    parser.add_argument(
        "TEMPLATES",
        help="The input templates directory",
        type=Path,
        default=Path.cwd() / "templates",
    )
    parser.add_argument(
        "OUTPUT", help="The output website directory", type=Path, default=Path.cwd()
    )

    args = parser.parse_args()
    input_dir: Path = args.INPUT
    if not input_dir.exists():
        parser.error(f"no such directory: {args.INPUT}")

    template_dir: Path = args.TEMPLATES
    if not template_dir.exists():
        parser.error(f"no such directory: {args.TEMPLATES}")

    output_dir: Path = args.OUTPUT
    # if output_dir.exists():
    #    shutil.rmtree(output_dir)

    output_dir.mkdir(exist_ok=True, parents=True)

    catalog = EssentialsCatalog.load_from_toml(input_dir)

    game_dir: Path | None = args.game_dir
    image_cache_location: Path = args.image_cache_location

    pokesprites = image_cache_location / "mons"
    pokesprites.mkdir(exist_ok=True, parents=True)

    maps_dir = image_cache_location / "rendered_maps"
    maps_dir.mkdir(exist_ok=True, parents=True)

    if args.crop_regular_sprites:
        if game_dir is None:
            parser.error("--game-dir must be provided for image processing")

        crop_regular_sprites(catalog, game_dir, pokesprites)

    if args.crop_form_sprites:
        if game_dir is None:
            parser.error("--game-dir must be provided for image processing")

        crop_form_sprites(catalog, game_dir, pokesprites)

    if args.render_maps:
        if game_dir is None:
            parser.error("--game-dir must be provided for image processing")

        render_all_maps(catalog, game_dir, args.INPUT, maps_dir)

    changelog = build_changelog(catalog)

    walkthru_statics = []
    search_paths = [template_dir]
    if (wdir := input_dir / "walkthroughs").exists():
        search_paths.append(wdir)

    loader = jinja2.FileSystemLoader(searchpath=search_paths)
    env = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
    env.globals["catalog"] = catalog
    env.globals["changelog"] = changelog
    env.globals["MoveCategory"] = MoveCategory
    env.globals["ENCOUNTER_SLOTS"] = ENCOUNTER_SLOTS
    env.globals["FIELD_NAMES"] = FIELD_NAMES
    env.globals["navbar_maps"] = load_navbar_maps(catalog, input_dir / "web" / "navbar_maps.toml")

    if wdir.exists():
        env.globals["navbar_walkthroughs"] = load_navbar_walkthroughs(wdir / "navbar.toml")
    else:
        env.globals["navbar_walkthroughs"] = None

    # build single-file templates
    with (output_dir / "changelog.html").open(mode="w", encoding="utf-8") as f:
        f.write(env.get_template("changelog/page.html").render())

    (output_dir / "species").mkdir(exist_ok=True, parents=True)
    (output_dir / "species" / "specific").mkdir(exist_ok=True, parents=True)
    with (output_dir / "species" / "index.html").open(mode="w", encoding="utf-8") as f:
        f.write(env.get_template("species/list.html").render(species_definitions=catalog.species))

    (output_dir / "trainers").mkdir(exist_ok=True, parents=True)
    trainer_template = env.get_template("trainers/single_trainer.html")
    for tr in tqdm(catalog.trainers.values(), desc="Trainer Page Rendering"):
        path = (output_dir / "trainers" / tr.trainer_name).with_suffix(".html")
        try:
            path.write_text(trainer_template.render(trainers=tr))
        except:
            print("Error rendering", tr.trainer_name, file=sys.stderr)
            raise

    (output_dir / "walkthroughs").mkdir(exist_ok=True, parents=True)
    if wdir.exists():
        for path in wdir.iterdir():
            if not path.is_dir():
                continue

            if (wdir_static := path / "static").exists():
                walkthru_statics.append(wdir_static)

            template = env.get_template(f"{path.name}/page.html")
            output = (output_dir / "walkthroughs" / path.name).with_suffix(".html")
            output.write_text(template.render())

    # now make sure the sprites and static data are all there
    shutil.copytree(template_dir / "static", output_dir / "static", dirs_exist_ok=True)
    shutil.copytree(pokesprites, output_dir / "sprites", dirs_exist_ok=True)
    shutil.copytree(maps_dir, output_dir / "static" / "maps", dirs_exist_ok=True)

    for static_dir in walkthru_statics:
        output = output_dir / "static" / static_dir.parent.name
        shutil.copytree(static_dir, output, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
