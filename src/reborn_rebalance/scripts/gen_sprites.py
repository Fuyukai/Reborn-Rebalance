import sys
from pathlib import Path

from PIL import Image

from reborn_rebalance.pbs.serialisation import load_all_species_from_toml

BLACKLISTED = [
    "eeveon",
    "maneon",
    "hawkeon",
    "bristleon",
    "zirconeon",
    "kitsuneon",
    "drekeon",
]


def gen_all_sprites():
    """
    Copies out sprites from the Reborn directory.
    """

    data_dir = Path("./data/species").absolute()
    graphics_dir = Path(sys.argv[1]) / "Graphics"
    output_path = Path("./sprites").absolute()
    output_path.mkdir(parents=True, exist_ok=True)

    for idx, species in enumerate(load_all_species_from_toml(data_dir)):
        idx += 1
        input_mini_sprite = graphics_dir / "Icons" / f"icon{idx:03d}.png"

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

        inp_battler = graphics_dir / "Battlers" / f"{idx:03d}.png"
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

        print(f"cropped and saved {idx} ({species.name})")


if __name__ == "__main__":
    gen_all_sprites()
