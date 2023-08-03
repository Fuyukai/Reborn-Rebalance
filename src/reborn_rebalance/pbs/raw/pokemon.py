from pathlib import Path
from typing import Iterator

# basically only used for generating the input files.


class KeyValueParser:
    def __init__(self):
        # clever trick we do here wrt to mutability
        # _entries stores the actual value of _current when we see a number.
        # fjdsfy im mentally overstimulated tonight so just pretend you know what im talking about.

        self._entries: dict[int, dict[str, str | int]] = {}
        self._current: dict[str, str | int] = {}

    def reset(self):
        self._entries = {}
        self._current = {}

    def parse(self, lines: Iterator[str]) -> dict[int, dict[str, str | int]]:
        for line in lines:
            line = line.strip()

            # le number line
            if line.startswith("["):
                number = int(line[1:-1])
                self._current = {}
                self._entries[number] = self._current
                continue

            if line.startswith("#"):
                continue

            key, value = line.split("=", 1)
            try:
                value = int(value.strip())
            except ValueError:
                pass

            self._current[key.strip()] = value

        return self._entries


def raw_parse_kv(path: Path) -> dict[int, dict[str, str | int]]:
    """
    Parses a Key/Value PBS file into a list of dictionaries.
    """

    parser = KeyValueParser()

    with path.open(mode="r", encoding="utf-8") as f:
        return parser.parse(iter(f.readline, ""))


if __name__ == "__main__":
    from pprint import pp

    for entry in raw_parse_kv(Path.home() / "aur/pokemon/reborn/PBS/pokemon.txt"):
        pp(entry)
