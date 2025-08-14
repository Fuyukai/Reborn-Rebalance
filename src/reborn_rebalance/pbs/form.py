from io import StringIO
from pathlib import Path

import attr
import structlog
from cattr import override
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn

from reborn_rebalance.pbs.pokemon import (
    EvolutionType,
    FormAttributes,
    PokemonEvolution,
    PokemonSpecies,
    RawLevelUpMove,
    StatWrapper,
)
from reborn_rebalance.pbs.type import PokemonType
from reborn_rebalance.util import RubyBuffer

# realistically I only care to support a small subset of the possible values in the
# species definition.

FORM_COPY = [
    ("FLABEBE", "FLOETTE"),
    ("SHELLOS", "GASTRODON"),
    ("DEERLING", "SAWSBUCK"),
]


def _make_header():
    header = StringIO()
    header.write("FormCopy = [\n")
    for from_, to in FORM_COPY:
        header.write("    [PBSpecies::")
        header.write(from_)
        header.write(", PBSpecies::")
        header.write(to)
        header.write("],\n")
    header.write("]\n\n")
    return header.getvalue()


HEADER = _make_header()

FOOTER = """
for form in FormCopy
    PokemonForms[form[1]] = PokemonForms[form[0]].clone
end
"""


@attr.s(slots=True, kw_only=True)
class SinglePokemonForm:
    """
    A single individual form for a Pokémon.

    This contains a set of *overrides* to the base species; any overrides that are empty are
    ignored.
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
    form_name: str = attr.ib(default=None)

    #: The primary type override for this form.
    primary_type: PokemonType | None = attr.ib(default=None)
    #: The secondary type override for this form.
    secondary_type: PokemonType | None = attr.ib(default=None)

    #: The stat overrides for this form.
    base_stats: StatWrapper | None = attr.ib(default=None)

    #: The Pokédex entry override for this form.
    pokedex_entry: str | None = attr.ib(default=None)

    #: The ability overrides for this form.
    raw_abilities: list[str] = attr.ib(factory=lambda: [])

    #: The moveset overrides for this form.
    raw_level_up_moves: list[RawLevelUpMove] = attr.ib(factory=lambda: [])

    #: The custom egg moves for this form.
    raw_egg_moves: list[str] = attr.ib(factory=lambda: [])

    #: The evolutionary data for this form, if any.
    evo_data_v2: list[PokemonEvolution] = attr.ib(factory=lambda: [])

    def combined_attributes(self, species: PokemonSpecies) -> FormAttributes:
        """
        Gets the combined attributes of this form and the provided species.
        """

        return FormAttributes(
            name=species.name,
            form_name=self.form_name,
            primary_type=self.primary_type or species.primary_type,
            secondary_type=self.secondary_type or species.secondary_type,
            base_stats=self.base_stats or species.base_stats,
            pokedex_entry=self.pokedex_entry or species.pokedex_entry,
            raw_abilities=self.raw_abilities or species.full_abilities,
            raw_level_up_moves=self.raw_level_up_moves or species.raw_level_up_moves,
            raw_egg_moves=self.raw_egg_moves or species.raw_egg_moves,
            internal_name=species.internal_name,
            evolutions=self.evo_data_v2 or species.evolutions,
        )

    def generate_ruby_code(self, buffer: RubyBuffer):
        """
        Generates the ruby code for this form.
        """

        if self.primary_type:
            buffer.write_whole_line(f":Type1 => PBTypes::{self.primary_type.name},")

        if self.secondary_type:
            buffer.write_whole_line(f":Type2 => PBTypes::{self.secondary_type.name},")

        if self.base_stats:
            buffer.write_whole_line(f":BaseStats => [{self.base_stats.to_pbs()}],")

        if self.pokedex_entry:
            buffer.write_whole_line(f':DexEntry => "{self.pokedex_entry}",')

        if self.raw_abilities:
            ability_line = ", ".join([f"PBAbilities::{ability}" for ability in self.raw_abilities])
            buffer.write_whole_line(f":Ability => [{ability_line}],")

        if self.raw_level_up_moves:
            buffer.write_whole_line(":Movelist => [")

            with buffer.indented():
                for move in self.raw_level_up_moves:
                    buffer.write_whole_line(f"[{move.at_level}, PBMoves::{move.name}],")

            buffer.write_whole_line("],")

        if self.evo_data_v2:
            buffer.write_whole_line(":GetEvo => [")

            with buffer.indented():
                for evolution in self.evo_data_v2:
                    buffer.write_indent()
                    buffer.write(
                        f"[PBSpecies::{evolution.into_name}, "
                        f"PBEvolution::{evolution.condition.name}, "
                    )

                    if evolution.condition in (
                        EvolutionType.Item,
                        EvolutionType.ItemMale,
                        EvolutionType.ItemFemale,
                    ):
                        buffer.write(f"PBItems::{evolution.parameter}")
                    elif evolution.parameter is not None:
                        buffer.write(evolution.parameter)
                    else:
                        buffer.write_whole_line("0")

                    buffer.write("],\n")

            buffer.write_whole_line("],")


@attr.s(frozen=True, slots=True, kw_only=True)
class PokemonForms:
    """
    Wraps multiple forms for a Pokémon.
    """

    @classmethod
    def _unstructure_form_mapping(cls, mapping: dict[int, str]) -> dict[str, str]:
        return {str(k): v for k, v in mapping.items()}

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        unst_hook = make_dict_unstructure_fn(
            cls,
            converter,
            _cattrs_omit_if_default=True,
            form_mapping=override(unstruct_hook=cls._unstructure_form_mapping),
        )
        converter.register_unstructure_hook(cls, unst_hook)

    #: The internal name for the species these forms are for.
    internal_name: str = attr.ib()

    #: The mapping of form name -> form ID.
    form_mapping: dict[int, str] = attr.ib(factory=lambda: {})

    #: The custom initialiser code to use for this species.
    #:
    #: Used to create different forms during encounters, for example.
    custom_init: str = attr.ib(default=None)

    #: The default form ID for this species.
    #:
    #: Used to return Mega Evolved Pokémon to their default form after exiting a battle.
    default_form: int = attr.ib(default=0)

    #: The mega-evolution form ID for this species.
    #:
    #: May be None if this species has no mega evolutions.
    mega_form: int | None = attr.ib(default=None)

    #: A custom mapping of {item => form}. Overrides ``default_form``.
    custom_default_mapping: dict[str, int] = attr.ib(factory=lambda: {})

    #: A custom mapping of {mega stone => mega form}. Overrides ``mega_form``.
    custom_mega_mapping: dict[str, int] = attr.ib(factory=lambda: {})

    #: The... ultra (?) form for this species.
    ultra_form: int | None = attr.ib(default=None)

    #: The PULSE form for this species.
    pulse_form: int | None = attr.ib(default=None)

    #: If true, this has a dynamax form. Used strictly for sprite generation.
    has_dynamax_form: bool = attr.ib(default=False)

    #: The mapping of form name -> form data for this species.
    #: Needs to match the ``form_names`` properties in the species definition.
    #: Please note that form IDs and the indexes in here are unrelated to each other.
    forms: dict[str, SinglePokemonForm] = attr.ib(factory=lambda: {})

    def _validate(self) -> ExceptionGroup[Exception] | None:
        errors: list[Exception] = []

        for form_name in self.forms:
            if form_name not in self.form_mapping.values():
                errors.append(ValueError(f"extraneous form: {form_name}"))  # noqa: PERF401

        if self.mega_form is not None and self.mega_form not in self.form_mapping:
            errors.append(ValueError(f"no such mega form: {self.mega_form}"))

        if self.pulse_form is not None and self.pulse_form not in self.form_mapping:
            errors.append(ValueError(f"no such pulse form: {self.pulse_form}"))

        if errors:
            return ExceptionGroup(f"Error validating {self.internal_name}", errors)

        return None

    def by_id(self, id: int) -> SinglePokemonForm | None:
        try:
            form_name = self.form_mapping[id]
            return self.forms[form_name]
        except KeyError:
            return None

    def generate_ruby_code(self, buffer: RubyBuffer):
        """
        Generates the Ruby code for this form.
        """

        buffer.write_whole_line(f"PBSpecies::{self.internal_name} => {{")

        with buffer.indented():
            # e.g. unown has multiple different forms, but only one form name.
            if self.form_mapping:
                buffer.write_whole_line(":FormName => {")

                # some forms have a 0 => "Normal"...
                # not sure why.

                with buffer.indented():
                    for idx, form_name in self.form_mapping.items():
                        buffer.write_whole_line(f'{idx} => "{form_name}",')

                buffer.write_whole_line("},")

            if self.custom_default_mapping:
                buffer.write_whole_line(":DefaultForm => {")
                with buffer.indented():
                    for name, idx in self.custom_default_mapping.items():
                        buffer.write_whole_line(f"PBItems::{name} => {idx},")

                buffer.write_whole_line("},")

            if self.custom_mega_mapping:
                buffer.write_whole_line(":MegaForm => {")

                with buffer.indented():
                    for name, idx in self.custom_mega_mapping.items():
                        buffer.write_whole_line(f"PBItems::{name} => {idx},")

                buffer.write_whole_line("},")

                if not self.custom_default_mapping:
                    buffer.write_whole_line(f":DefaultForm => {self.default_form},")

            elif self.mega_form is not None:
                buffer.write_whole_line(f":MegaForm => {self.mega_form},")

                if not self.custom_default_mapping:
                    buffer.write_whole_line(f":DefaultForm => {self.default_form},")

            if self.ultra_form is not None:
                buffer.write_whole_line(f":UltraForm => {self.ultra_form},")

            if self.pulse_form is not None:
                buffer.write_whole_line(f":PulseForm => {self.pulse_form},")

            if self.custom_init:
                buffer.write_whole_line(":OnCreation => proc{")

                with buffer.indented():
                    lines = self.custom_init.splitlines()
                    for line in lines:
                        buffer.write_whole_line(line)

                buffer.write_whole_line("},")

            for form in self.forms.values():
                buffer.write_whole_line(f'"{form.form_name}" => {{')

                with buffer.indented():
                    form.generate_ruby_code(buffer)

                buffer.write_whole_line("},")

        buffer.write_whole_line("},")


def save_forms_to_ruby(
    output_path: Path,
    forms: dict[str, PokemonForms],
):
    """
    Generates the ruby code for the forms data.
    """

    buffer = RubyBuffer()
    buffer.write(HEADER)

    buffer.write_whole_line("PokemonForms = {")

    with buffer.indented():
        for form_list in forms.values():
            form_list.generate_ruby_code(buffer)

    buffer.write_whole_line("}")
    buffer.write(FOOTER)

    with output_path.open(mode="w", encoding="utf-8") as f:
        structlog.get_logger(__name__).info("save", type="forms", path=output_path)
        f.write(buffer.backing.getvalue())
