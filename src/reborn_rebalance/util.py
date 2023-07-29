from contextlib import contextmanager
from enum import Enum
from io import StringIO
from typing import Any, Collection, Iterable, TypeVar

import cattrs

_ChunkType = TypeVar("_ChunkType")


def chunks(lst: Collection[_ChunkType], n: int) -> Iterable[list[_ChunkType]]:
    """
    Yield successive n-sized chunks from lst.
    """

    for i in range(0, len(lst), n):
        yield lst[i : i + n]


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

    def write_key_value(self, key: str, value: Any):
        self.backing.write(key)
        self.backing.write("=")
        self.backing.write(str(value))
        self.backing.write("\n")

    def write_list(self, key: str, value: list[Any]):
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
