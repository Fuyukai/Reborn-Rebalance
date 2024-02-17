from pathlib import Path

import rtoml
import tomli_w


def main() -> None:
    """
    Renumbers Gen 9 Pokemon to account for the 5.0 -> 6.5 changes.
    """

    # sprigatito is now nat dex 906.
    data_dir = Path("./data")
    gen_9_dir = data_dir / "species" / "gen_9"
    gen_9_dir.mkdir()

    for file in (data_dir / "species" / "gen_9_old").iterdir():
        snum, name = file.name.split("-", 1)
        num = int(snum)

        # Old eeveelutions were 0906-0915, and are now 1026-1035.
        if 906 <= num <= 916:  # noqa: SIM108
            new_number = 1026 + (num - 906)
        else:
            new_number = 906 + (num - 916)

        new_file_name = f"{new_number:04d}-{name}"

        with file.open(mode="r") as f:
            content = rtoml.load(f)
            content["dex_number"] = new_number

        new_file = gen_9_dir / new_file_name
        with new_file.open(mode="wb") as f:
            tomli_w.dump(content, f)


if __name__ == "__main__":
    main()
