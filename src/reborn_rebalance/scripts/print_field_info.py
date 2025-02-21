import sys
from pathlib import Path
from typing import cast

from rhodochrosite import GenericRubyUserObject, read_object
from rich import print

from reborn_rebalance.pbs.catalog import EssentialsCatalog
from reborn_rebalance.pbs.serialisation import make_field_effect_data


def main() -> int:
    try:
        catalog_path = Path(sys.argv[1])
        fields_dat = Path(sys.argv[2])
    except IndexError:
        print(f"usage: {sys.argv[0]} <path to catalogue> <path to fields.dat>")
        return 1

    EssentialsCatalog.load_from_toml(catalog_path, skip_species=True)

    data = cast(
        list[GenericRubyUserObject], read_object(fields_dat.read_bytes(), unwrap_dict_keys=True)
    )
    for raw_field in data:
        field_effect = make_field_effect_data(raw_field)
        print(field_effect)

    return 0


if __name__ == "__main__":
    main()
