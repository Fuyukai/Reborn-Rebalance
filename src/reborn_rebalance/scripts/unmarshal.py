import json
import struct
import sys
from pathlib import Path
from typing import Any, TypeVar

from rubymarshal.classes import ClassRegistry, RubyObject, RubyString, UserDef
from rubymarshal.reader import load, loads
from typing_extensions import override

from reborn_rebalance import _hotpatch

registry = ClassRegistry()

AnyRubyObject = TypeVar("AnyRubyObject", contravariant=True)

# disgusting hotpatch
_hotpatch._patch()

# https://github.com/Solistra/rvpacker/blob/develop/lib/rvpacker/rgss.rb#L27
class RgssTable(UserDef):
    """
    Represents the RGSS Table class. Like a shitty 3D array.
    """

    ruby_class_name = "Table"

    def __init__(self, ruby_class_name=None, attributes=None):
        super().__init__(ruby_class_name=ruby_class_name, attributes=attributes)

        # the actual raw map data
        self.raw_data: list[int] = []

        # dimensions? not sure
        self.dim = 0

        # row count
        self.x = 0
        # col count
        self.y = 0
        # layer count, always 3 for XP...
        self.z = 0

    @override
    def _load(self, private_data: bytes):
        # native endian, lol. why.
        header = struct.calcsize("<5L")
        self.dim, self.x, self.y, self.z, size = struct.unpack("<5L", private_data[:header])

        map_data = private_data[header:]
        # array of LE shorts
        if len(map_data) // 2 != size:
            raise ValueError(f"expected {size} bytes, got {len(map_data)}")

        self.raw_data = [i[0] for i in struct.iter_unpack("<H", map_data)]

    def to_dict(self) -> dict[str, Any]:
        return {"dim": self.dim, "x": self.x, "y": self.y, "z": self.z, "raw": self.raw_data}


registry.register(RgssTable)


class RubyJsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, bytes):
            try:
                return o.decode(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    return o.decode(encoding="shift-jis")
                except UnicodeDecodeError:
                    return o.hex()

        elif isinstance(o, RgssTable):
            return o.to_dict()

        elif isinstance(o, RubyString):
            return o.text

        elif isinstance(o, RubyObject):
            return o.attributes

        raise super().default(o)


def unmarshal(from_path: Path) -> AnyRubyObject | list[AnyRubyObject] | dict[str, AnyRubyObject]:
    """
    Unmarshals data from the provided path.
    """

    with from_path.open(mode="rb") as f:
        return load(f, registry=registry)


def main():
    data = Path(sys.argv[1]).absolute().read_bytes()
    output = Path(sys.argv[2])
    obb = loads(data, registry=registry)

    output.write_text(json.dumps(obb, indent=4, cls=RubyJsonEncoder))


if __name__ == "__main__":
    main()
