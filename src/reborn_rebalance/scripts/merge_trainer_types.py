from pathlib import Path

import rtoml


def main() -> None:
    """
    Merges the ``skill_level`` field with the old music fields.
    """

    old_types = rtoml.loads(Path("./data/trainer_types.toml.old").read_text())
    new_types = rtoml.loads(Path("./data/trainer_types.toml").read_text())

    for k, v in new_types["trainer_types"].items():
        old = old_types["trainer_types"].get(k)
        if old is None:
            old_types["trainer_types"][k] = v
        else:
            if skill := v.get("skill_level"):
                old["skill_level"] = skill

            old["id"] = v["id"]

    Path("./data/trainer_types.toml").write_text(rtoml.dumps(old_types))


if __name__ == "__main__":
    main()
