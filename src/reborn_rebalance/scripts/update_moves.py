# pyright: basic

import sys
from pathlib import Path

import rtoml
import tomli_w

# Re-assigns IDs because the all gen guy fucking reid'd old moves. what the fuck!
# Also fixes move function IDs.


KEEP_DESCRIPTIONS = {70, 794}


def main() -> int:
    try:
        old_path = Path(sys.argv[1])
        new_path = Path(sys.argv[2])
    except IndexError:
        print(f"usage: {sys.argv[0]} <path to old moves.toml> <path to new moves.toml>")
        return 1

    try:
        output_path = Path(sys.argv[3])
    except IndexError:
        output_path = Path("./data/moves.toml")

    old = rtoml.load(old_path)["moves"]
    new = rtoml.load(new_path)["moves"]

    rewritten = []

    by_name = {it["internal_name"]: it for it in old}

    for move in new:
        id: int = move["id"]

        try:
            old_move = by_name[move["internal_name"]]
        except KeyError:
            print(f"copying new move {id}/{move['internal_name']}")
            rewritten.append(move)
        else:
            name = f"{id}/{old_move['internal_name']}"

            if old_move["id"] != id:
                print(f"reassigning {name} to move ID {id}")
                old_move["id"] = id

            if (
                old_move["description"] != (new_desc := move["description"])
                and id not in KEEP_DESCRIPTIONS
            ):
                print(f"updating description for {name} to {new_desc}")
                old_move["description"] = new_desc

            # hard-code esper wing
            if id > 750 and id != 794:
                if old_move["move_function"] != (nf := move["move_function"]):
                    print(f"updating move function for {name} to '{nf}'")
                    old_move["move_function"] = nf

                if (of := old_move["flags"]) != (flags := move["flags"]):
                    print(f"updating flags for {name} from {of} to {flags}")
                    old_move["flags"] = flags

            rewritten.append(old_move)

    with output_path.open(mode="wb") as f:
        tomli_w.dump({"moves": rewritten}, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
