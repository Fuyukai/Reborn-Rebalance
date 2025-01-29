import re
import sys
from pathlib import Path

from rich import print

from reborn_rebalance.pbs.form import FORM_COPY
from reborn_rebalance.pbs.serialisation import load_all_forms

FORMS_RE = re.compile(r"PBSpecies::([A-Z]*) =>")
DYNA_RE = re.compile(r':FormName.*"Dyna"')


def main() -> int:
    """
    Attempts to find Pokémon that have a new form that we don't have a file for.
    """

    try:
        form_path = Path(sys.argv[1])
        multipleforms_path = Path(sys.argv[2])
    except IndexError:
        print(f"usage: {sys.argv[0]} <path to forms directory> <path to MultipleForms.rb>")
        return 1

    forms = load_all_forms(form_path)

    copies = [it[1] for it in FORM_COPY]

    ruby_form_file = multipleforms_path.read_text()
    for match in FORMS_RE.finditer(ruby_form_file):
        name = match.group(1)
        # auto-copied, just skip
        if name in copies:
            continue

        end = match.end(0)

        # prevent firing on dynamax only forms. this is kinda gross but the formatting of the
        # original file is terrible
        first_newline = ruby_form_file.find("\n", end)
        if '"Dyna"' in ruby_form_file[first_newline : first_newline + 50]:
            print(f"[cyan]Skipped[/cyan]: {name}")
            continue

        if name not in forms:
            print(f"Found missing form: [yellow]{name}[/yellow]")
        else:
            print(f"[green]Not missing[/green]: {name}")

    return 0
