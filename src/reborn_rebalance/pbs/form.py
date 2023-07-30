import textwrap
from pathlib import Path

import attr
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn

from reborn_rebalance.pbs.pokemon import (
    FormAttributes,
    PokemonSpecies,
    RawLevelUpMove,
    StatWrapper,
)
from reborn_rebalance.pbs.type import PokemonType
from reborn_rebalance.util import RubyBuffer

# realistically I only care to support a small subset of the possible values in the
# species definition.

HEADER = """
FormCopy = [
	[PBSpecies::FLABEBE,PBSpecies::FLOETTE],
	[PBSpecies::FLABEBE,PBSpecies::FLORGES],
	[PBSpecies::SHELLOS,PBSpecies::GASTRODON],
	[PBSpecies::DEERLING,PBSpecies::SAWSBUCK]
]
"""

FOOTER = """
for form in FormCopy
	PokemonForms[form[1]] = PokemonForms[form[0]].clone
end
"""


@attr.s(frozen=True, slots=True, kw_only=True)
class SinglePokemonForm:
    """
    A single individual form for a Pokémon. This contains a set of *overrides* to the base
    species; any overrides that are empty are ignored.
    """

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        unst_hook = make_dict_unstructure_fn(
            cls,
            converter,
            _cattrs_omit_if_default=True,
        )
        converter.register_unstructure_hook(cls, unst_hook)

    #: The name for this form, e.g. 'Hisui'.
    form_name: str = attr.ib()

    #: The primary type override for this form.
    primary_type: PokemonType | None = attr.ib(default=None)
    #: The secondary type override for this form.
    secondary_type: PokemonType | None = attr.ib(default=None)

    #: The stat overrides for this form.
    base_stats: StatWrapper | None = attr.ib(default=None)

    #: The Pokédex entry override for this form.
    pokedex_entry: str | None = attr.ib(default=None)

    #: The ability overrides for this form.
    raw_abilities: list[str] = attr.ib(factory=list)

    #: The moveset overrides for this form.
    raw_level_up_moves: list[RawLevelUpMove] = attr.ib(factory=list)

    def combined_attributes(self, species: PokemonSpecies) -> FormAttributes:
        """
        Gets the combined attributes of this form and the provided species.
        """

        attribs = FormAttributes(
            name=species.name,
            form_name=self.form_name,
            primary_type=self.primary_type or species.primary_type,
            secondary_type=self.secondary_type or species.secondary_type,
            base_stats=self.base_stats or species.base_stats,
            pokedex_entry=self.pokedex_entry or species.pokedex_entry,
            raw_abilities=self.raw_abilities or species.raw_abilities,
            raw_level_up_moves=self.raw_level_up_moves or species.raw_level_up_moves,
            internal_name=species.internal_name,
        )

        return attribs

    def generate_ruby_code(self, buffer: RubyBuffer):
        """
        Generates the ruby code for this form.
        """

        if self.primary_type:
            buffer.write_line(f":Type1 => PBTypes::{self.primary_type.name}")

        if self.secondary_type:
            buffer.write_line(f":Type2 => PBTypes::{self.secondary_type.name}")

        if self.base_stats:
            buffer.write_line(f":BaseStats => [{self.base_stats.to_pbs()}]")

        if self.pokedex_entry:
            buffer.write_line(f':DexEntry => "{self.pokedex_entry}"')

        if self.raw_abilities:
            ability_line = ", ".join([f"PBAbilities::{ability}" for ability in self.raw_abilities])
            buffer.write_line(f":Ability => [{ability_line}]")

        if self.raw_level_up_moves:
            buffer.write_line(":Movelist => [")

            with buffer.indented():
                for move in self.raw_level_up_moves:
                    buffer.write_line(f"[{move.at_level}, PBMoves::{move.name}],")

            buffer.write_line("],")


@attr.s(frozen=True, slots=True, kw_only=True)
class PokemonForms:
    """
    Wraps multiple forms for a Pokémon.
    """

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        unst_hook = make_dict_unstructure_fn(
            cls,
            converter,
            _cattrs_omit_if_default=True,
        )
        converter.register_unstructure_hook(cls, unst_hook)

    #: The internal name for the species these forms are for.
    internal_name: str = attr.ib()

    #: The mapping of form name -> form ID.
    form_mapping: dict[int, str] = attr.ib()

    #: The custom initialiser code to use for this species.
    #: Used to create different forms during encounters, for example.
    custom_init: str = attr.ib(default=None)

    #: The default form ID for this species.
    #: Not sure what this is used for.
    default_form: int = attr.ib(default=0)

    #: The mega-evolution form ID for this species.
    #: May be None if this species has no mega evolutions.
    mega_form: int | None = attr.ib(default=None)

    #: The mapping of form name -> form data for this species.
    #: Needs to match the ``form_names`` properties in the species definition.
    #: Please note that form IDs and the indexes in here are unrelated to each other.
    forms: dict[str, SinglePokemonForm] = attr.ib(factory=dict)

    def generate_ruby_code(self, buffer: RubyBuffer):
        """
        Generates the Ruby code for this form.
        """
        buffer.write_line(f"PBSpecies::{self.internal_name} => {{")

        with buffer.indented():
            buffer.write_line(":FormName => {")

            # some forms have a 0 => "Normal"...
            # not sure why.

            with buffer.indented():
                for idx, form_name in self.form_mapping.items():
                    buffer.write_line(f'{idx} => "{form_name}",')

            buffer.write_line("},")

            if self.custom_init:
                with buffer.indented():
                    buffer.write_line(":OnCreation => proc{")

                    lines = self.custom_init.splitlines()
                    for line in lines:
                        buffer.write_line(line)

                    buffer.write_line("},")

            for form_name, form in self.forms.items():
                buffer.write_line(f'"{form.form_name}" => {{')

                with buffer.indented():
                    form.generate_ruby_code(buffer)

                buffer.write_line("},")

        buffer.write_line("},")


def save_forms_to_ruby(output_path: Path, forms: dict[str, PokemonForms]):
    """
    Generates the ruby code for the forms data.
    """

    buffer = RubyBuffer()
    buffer.write(HEADER)

    buffer.write_line("PokemonForms = {")

    with buffer.indented():
        for form_list in forms.values():
            form_list.generate_ruby_code(buffer)

    buffer.write_line("}")
    buffer.write(FOOTER)

    with output_path.open(mode="w", encoding="utf-8") as f:
        print("writing to", output_path, f)
        f.write(buffer.backing.getvalue())
