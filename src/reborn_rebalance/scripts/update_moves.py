from pathlib import Path

import rtoml
import tomli_w

# Re-assigns IDs because the all gen guy fucking reid'd old moves. what the fuck!
# Also fixes move function IDs.


def main():
    old = rtoml.load(Path("./data/movesold.toml"))["moves"]
    new = rtoml.load(Path("./data/movesnew.toml"))["moves"]

    rewritten = []

    by_name = {it["internal_name"]: it for it in old}

    for move in new:
        id = move["id"]

        try:
            old_move = by_name[move["internal_name"]]
        except KeyError:
            print(f"copying new move {move['id']}/{move['internal_name']}")
            rewritten.append(move)
        else:
            name = f"{old_move['id']}/{old_move['internal_name']}"

            if old_move["id"] != id:
                print(f"reassigning {name} to move ID {id}")
                old_move["id"] = id

            # hard-code esper wing
            if id > 750 and id != 794:
                if old_move["move_function"] != (nf := move["move_function"]):
                    print(f"updating move function for {name} to '{nf}'")
                    old_move["move_function"] = nf

                if (of := old_move["flags"]) != (flags := move["flags"]):
                    print(f"updating flags for {name} from {of} to {flags}")
                    old_move["flags"] = flags

            rewritten.append(old_move)

    with Path("./data/moves.toml").open(mode="wb") as f:
        tomli_w.dump({"moves": rewritten}, f)
