from typing import Any, final

import attrs
import cattrs
from cattrs import Converter

# of course, in their infinite wisdom, this uses a bunch of fucking DICTS inside
# sigh.

# field notes are written manually. what the fuck?
# oh god the field ruby code is so bad. and this is AFTER going through rubyfmt.


@attrs.define(kw_only=True)
class FieldMoveData:
    # AAAH OF COURSE THEY'RE ALL OPTIONAL
    mult: int | None = attrs.field(default=None)
    typemod: int | None = attrs.field(default=None)  # ?
    multtext: int | None = attrs.field(default=None)
    fieldchange: int | None = attrs.field(default=None)
    changetext: int | None = attrs.field(default=None)
    accmod: int | None = attrs.field(default=None)  # kys
    dont_change_backup: bool = attrs.field(alias="dontchangebackup", default=True)


@attrs.define(kw_only=True)
class FieldTypeData:
    mult: int | None = attrs.field(default=None)
    typemod: int | None = attrs.field(default=None)
    multtext: int | None = attrs.field(default=None)
    condition: str | None = attrs.field(default=None)


@attrs.define(kw_only=True)
@final
class FieldEffectData:
    """
    Wraps information about a single field effect.
    """

    @classmethod
    def add_unstructure_hook(cls, converter: Converter) -> None:
        for klass in [FieldMoveData, FieldTypeData, FieldEffectData]:
            converter.register_structure_hook(
                klass, cattrs.gen.make_dict_structure_fn(klass, converter, _cattrs_use_alias=True)
            )

    # https://rubystyle.guide/

    field_name: str = attrs.field(alias="fieldname")
    intro_message: str = attrs.field(alias="intromessage")
    field_graphic_name: str = attrs.field(alias="fieldgraphics")

    # no clue what these three are
    secretpoweranim: int = attrs.field()
    naturemoves: int = attrs.field()
    mimicry: int = attrs.field()

    field_move_data: dict[str, FieldMoveData] = attrs.field(alias="fieldmovedata")
    field_type_data: dict[str, FieldTypeData] = attrs.field(alias="fieldtypedata")
    seeddata: dict[Any, Any]

    move_message_list: list[str] = attrs.field(alias="movemessagelist")
    type_message_list: list[str] = attrs.field(alias="typemessagelist")
    change_message_list: list[str] = attrs.field(alias="changemessagelist")

    status_move_boost: list[int] = attrs.field(alias="statusmoveboost")

    field_change_conditions: dict[Any, Any] = attrs.field(alias="fieldchangeconditions")
