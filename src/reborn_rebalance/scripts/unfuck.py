from pathlib import Path

import rtoml

# Re-assigns IDs because the all gen guy fucking reid'd old moves. what the fuck!


def main():
    old = rtoml.load(Path("./data/movesold.toml"))["moves"]
    new = rtoml.load(Path("./data/movesnew.toml"))["moves"]

    rewritten = []

    by_name = {it["internal_name"]: it for it in old}

    for move in new:
        try:
            old_move = by_name[move["internal_name"]]
        except KeyError:
            rewritten.append(move)
        else:
            print(f"reassigning {old_move['id']}/{old_move['internal_name']} to {move['id']}")
            old_move["id"] = move["id"]
            rewritten.append(old_move)

    with Path("./data/moves.toml").open(mode="w") as f:
        rtoml.dump({"moves": rewritten}, f, pretty=False)
