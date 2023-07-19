from pathlib import Path
from typing import TextIO


# basically only used for generating the input files.


def _raw_parse_inner(f: TextIO) -> list[dict[str, str | int]]:
    has_started = False
    last_entry = {}
    entries: list[dict[str, str | int]] = []

    def handle_kv(line: str) -> (str, str | int):
        if not has_started:
            raise ValueError("expected a [num] as first entry, not a key-value pair")

        key, value = line.split("=", 1)
        try:
            value = int(value)
        except ValueError:
            pass

        # thanks, wingull
        last_entry[key.strip()] = value

    def handle_number(line: str):
        nonlocal has_started
        num = int(line[1:-1])

        if has_started:
            entries.append(last_entry.copy())
            last_entry.clear()
        else:
            has_started = True

    while read_line := f.readline().rstrip():
        if read_line.startswith("["):
            handle_number(read_line)
        else:
            handle_kv(read_line)

    if last_entry:
        entries.append(last_entry)

    return entries


def raw_parse_pokemon_pbs(path: Path) -> list[dict[str, str | int]]:
    """
    Parses the ``pokemon.txt`` into a list of dictionaries.
    """

    with path.open(mode="r", encoding="utf-8") as f:
        return _raw_parse_inner(f)


if __name__ == "__main__":
    from pprint import pp

    for entry in raw_parse_pokemon_pbs(
        Path.home() / "aur/pokemon/reborn/PBS/pokemon.txt"
    ):
        pp(entry)
