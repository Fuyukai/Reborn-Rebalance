import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import TypeVar, overload

# basically only used for generating the input files.
_DefaultV = TypeVar("_DefaultV")


class KvResultDict(dict[str, str | int]):
    """
    A result dict with helpers for type casting.
    """

    @overload
    def pop_str(self, key: str) -> str:
        ...

    @overload
    def pop_str(self, key: str, default: _DefaultV) -> str | _DefaultV:
        ...

    def pop_str(self, key: str, default: _DefaultV = None) -> str | _DefaultV:
        """
        Pops a string key from this dict, or returns the default if it doesn't exist.
        """

        result = self.pop(key, default)
        if result is not None and not isinstance(result, str):
            raise ValueError("expected str for " + key)

        return result

    @overload
    def pop_int(self, key: str) -> int:
        ...

    @overload
    def pop_int(self, key: str, default: _DefaultV) -> int | _DefaultV:
        ...

    def pop_int(self, key: str, default: _DefaultV = None) -> int | _DefaultV:
        """
        Pops an int key from this dict, or returns the default if it doesn't exist.
        """

        result = self.pop(key, default)
        if result is not None and not isinstance(result, int):
            raise ValueError("expected str for " + key)

        return result


class KeyValueParser:
    def __init__(self):
        # clever trick we do here wrt to mutability
        # _entries stores the actual value of _current when we see a number.
        # fjdsfy im mentally overstimulated tonight so just pretend you know what im talking about.

        self._entries: dict[int, KvResultDict] = {}
        self._current: KvResultDict = KvResultDict()

    def reset(self):
        self._entries = {}
        self._current = KvResultDict()

    def parse(self, lines: Iterator[str]) -> dict[int, KvResultDict]:
        for line in lines:
            line = line.strip()

            # le number line
            if line.startswith("["):
                number = int(line[1:-1])
                self._current = KvResultDict()
                self._entries[number] = KvResultDict(self._current)
                continue

            if line.startswith("#"):
                continue

            key, value = line.split("=", 1)
            with contextlib.suppress(ValueError):
                value = int(value.strip())

            self._current[key.strip()] = value

        return self._entries


def raw_parse_kv(path: Path) -> dict[int, KvResultDict]:
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
