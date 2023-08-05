from contextlib import contextmanager
from io import StringIO
from typing import Any, Collection, Iterable, Iterator, Sequence, TypeVar

import attr

_ChunkType = TypeVar("_ChunkType")
_GetSafelyType = TypeVar("_GetSafelyType")


def chunks(lst: Collection[_ChunkType], n: int) -> Iterable[list[_ChunkType]]:
    """
    Yield successive n-sized chunks from lst.
    """

    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def get_safely(
    thing: Sequence[_GetSafelyType], index: int, default: _GetSafelyType = None
) -> _GetSafelyType | None:
    try:
        return thing[index]
    except IndexError:
        return default


class PbsBuffer(object):
    """
    A buffer-like object that supports writing PBS-formatted data.
    """

    def __init__(self):
        self.backing = StringIO()

    def write_id_header(self, id: Any):
        self.backing.write("[")
        self.backing.write(str(id))
        self.backing.write("]\n")

    def write_comment(self, comment: str):
        self.backing.write("# ")
        self.backing.write(comment)
        self.backing.write("\n")

    def write_key_value(self, key: str, value: Any):
        self.backing.write(key)
        self.backing.write("=")
        self.backing.write(str(value))
        self.backing.write("\n")

    def write_list(self, key: str, value: Iterable[Any]):
        """
        Writes a comma-joined list.
        """

        if not list:
            return

        self.backing.write(key)
        self.backing.write("=")
        self.backing.write(",".join(value))
        self.backing.write("\n")


class RubyBuffer:
    """
    A buffer for Ruby code generation.
    """

    def __init__(self):
        self._indent = 0
        self.backing = StringIO()

    @contextmanager
    def indented(self) -> None:
        try:
            self._indent += 4
            yield
        finally:
            self._indent -= 4

    def write(self, data: str):
        self.backing.write(data)

    def write_line(self, data: str):
        self.backing.write(" " * self._indent)
        self.backing.write(data)
        self.backing.write("\n")


@attr.s()
class StupidFuckingIterationWrapper:
    what_the_fuck_iterator: Iterator[str] = attr.ib()

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            fucking_next = next(self.what_the_fuck_iterator).strip()
            if fucking_next.startswith("#"):
                continue

            if not fucking_next:
                continue

            return fucking_next
