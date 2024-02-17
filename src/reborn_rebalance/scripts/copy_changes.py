
import shutil
import sys
from pathlib import Path

CHANGE_FILES = [
    "Data/attacksRS.dat",
    "Data/dexdata.dat",
    "Data/eggEmerald.dat",
    "Data/encounters.dat",
    "Data/evolutions.dat",
    "Data/fieldnotes.dat",
    "Data/items.dat",
    "Data/messages.dat",
    "Data/metadata.dat",
    "Data/metrics.dat",
    "Data/move2anim.dat",
    "Data/moves.dat",
    "Data/regionals.dat",
    "Data/tm.dat",
    "Data/trainers.dat",
    "Data/trainertypes.dat",
    "Scripts/Reborn/PBAbilities.rb",
    "Scripts/Reborn/PBItems.rb",
    "Scripts/Reborn/PBMoves.rb",
    "Scripts/Reborn/PBSpecies.rb",
    "Scripts/Reborn/PBTrainers.rb",
]

def main() -> int:
    """
    Copies the subset of modified files from a compiled directory to the output directory.
    """

    try:
        game_dir = Path(sys.argv[1])
        output_dir = Path(sys.argv[2])
    except IndexError:
        print(f"usage: {sys.argv[0]} <game directory> <output directory>", file=sys.stderr)
        return 1

    for file in CHANGE_FILES:
        input_path = game_dir / file
        output_path = output_dir / file
        output_path.parent.mkdir(exist_ok=True, parents=True)

        print(input_path, " -> ", output_path)
        shutil.copy2(input_path, output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
