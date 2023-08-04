from __future__ import annotations

import attr
from cattrs import Converter
from cattrs.gen import make_dict_unstructure_fn


@attr.s(slots=True, kw_only=True)
class TrainerType:
    """
    A single trainer type.
    """

    @classmethod
    def add_unstructure_hook(cls, converter: Converter):
        unst_hook = make_dict_unstructure_fn(
            cls,
            converter,
            _cattrs_omit_if_default=True,
        )
        converter.register_unstructure_hook(cls, unst_hook)

    #: The ID for this trainer type. Corresponds to the trainer images in the Graphics directory.
    id: int = attr.ib()

    #: The internal name for this trainer type.
    internal_name: str = attr.ib()

    #: The prefix for this trainer type, e.g. 'Agent'. Shown in game.
    name_prefix: str = attr.ib()

    #: The money this trainer gives out per level.
    money_per_level: int = attr.ib()

    #: The custom BGM for this trainer type, or None if there is no custom BGM.
    bgm: str | None = attr.ib(default=None)

    #: The custom ending sound effect, or None if there is none.
    end_sfx: str | None = attr.ib(default=None)

    #: The custom intro sfx, or None if there is none.
    intro_sfx: str | None = attr.ib(default=None)

    #: The gender (?) of this trainer type.
    gender: str = attr.ib(default="Mixed")

    #: The skill level (?) for this trainer.
    skill_level: int | None = attr.ib(default=None)

    @classmethod
    def from_csv_row(cls, row: list[str]) -> TrainerType:
        """
        Parses a single trainer type from a CSV row.
        """

        id = int(row[0])
        internal_name = row[1]
        name_prefix = row[2]
        money_per_level = int(row[3])
        bgm = row[4] or None
        end_sfx = row[5] or None
        intro_sfx = row[6] or None
        gender = row[7]
        try:
            skill_level = int(row[8])
        except ValueError:
            # missing :yert:
            skill_level = None

        return cls(
            id=id,
            internal_name=internal_name,
            name_prefix=name_prefix,
            money_per_level=money_per_level,
            bgm=bgm,
            end_sfx=end_sfx,
            intro_sfx=intro_sfx,
            gender=gender,
            skill_level=skill_level,
        )

    def into_csv_row(self) -> list[str]:
        """
        Writes this trainer type to a CSV row.
        """

        return [
            str(self.id),
            self.internal_name,
            self.name_prefix,
            str(self.money_per_level),
            self.bgm or "",
            self.end_sfx or "",
            self.intro_sfx or "",
            self.gender,
            str(self.skill_level) if self.skill_level is not None else "",
        ]
