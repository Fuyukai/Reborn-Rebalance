import contextlib
import sys
from io import StringIO
from pathlib import Path

from reborn_rebalance.pbs.catalog import EssentialsCatalog


def extended_validate_megas(catalog: EssentialsCatalog):
    """
    Validates that mega evolutions are correct.
    """

    for species_name, forms in catalog.forms.items():
        species = catalog.species_mapping[species_name]

        to_check = []

        if forms.custom_mega_mapping:
            to_check.extend(forms.form_mapping[it] for it in forms.custom_mega_mapping.values())
        else:
            if forms.mega_form:
                to_check.append(forms.form_mapping[forms.mega_form])

        if not to_check:
            continue

        for form_name in to_check:
            try:
                form = forms.forms[form_name]
            except KeyError:
                print(f"error: missing mega form definition for {species.name}")
                continue

            attrs = form.combined_attributes(species)

            if len(attrs.raw_abilities) != 1:
                print(
                    f"warning: mega form {form.form_name} for {species.name} should have exactly"
                    " one ability"
                )

            bst = attrs.base_stats.sum()
            if bst != (expected := species.base_stats.sum() + 100):
                print(
                    f"warning: mega form {form.form_name} for {species.name} should have a BST of"
                    f" {expected}, not {bst}"
                )


def extended_validate_abilities(catalog: EssentialsCatalog):
    for species in catalog.species:
        if len(species.full_abilities) > 3:
            print(
                f"warning: species {species.name} has too many abilities ({species.full_abilities})"
            )

        if len(set(species.full_abilities)) != len(species.full_abilities):
            print(
                f"warning: species {species.name} has duplicate abilities"
                f" ({species.full_abilities})"
            )

        if species.internal_name not in catalog.forms:
            continue

        for form in catalog.forms[species.internal_name].forms.values():
            attrs = form.combined_attributes(species)
            if len(attrs.raw_abilities) > 3:
                print(
                    f"warning: species {species.name} form {form.form_name} has too many abilities"
                    f" ({attrs.raw_abilities})"
                )

            if len(set(attrs.raw_abilities)) != len(attrs.raw_abilities):
                print(
                    f"warning: species {species.name} form {form.form_name} has duplicate abilities"
                    f" ({attrs.raw_abilities})"
                )


def do_extended_validation():
    with contextlib.redirect_stdout(StringIO()):
        catalog = EssentialsCatalog.load_from_toml(Path(sys.argv[1]))

    print("=== Begin Extended Validation ===\n")
    extended_validate_megas(catalog)
    print()
    extended_validate_abilities(catalog)


if __name__ == "__main__":
    do_extended_validation()
