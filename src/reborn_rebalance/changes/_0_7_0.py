from reborn_rebalance.changelog import ChangelogBuilder
from reborn_rebalance.pbs.type import PokemonType


def build_changes(builder: ChangelogBuilder):
    builder.custom("Imported most Pokémon changes from Blaze Black 2 Redux.")
    builder.custom("Imported most Pokémon changes for Gen 6-7 from Photonic Sun.")

    builder.move("DRAGONRUSH").change_move_base_power(100, 85).change_move_accuracy(75, 90)
    builder.move("WILDCHARGE").change_move_base_power(90, 120)

    blastoise = builder.pokemon(
        "BLASTOISE",
        """
        Mega Launcher Shell Smash Blastoise is disgustingly overpowered and easily carves through
        most enemies. Whilst it was fine in BB2R, it's been removed from Reborn Rebalanced for this
        reason.
        """,
    )
    blastoise.remove_level_up_move("SHELLSMASH")
    del blastoise

    butterfree = builder.pokemon(
        "BUTTERFREE",
        """
        Butterfree has had a stat buff to 425BST, and as such is now evolved into at Level 14
        instead. 
        """,
    )
    butterfree.add_base_stat_change("spa", 90, 100)
    butterfree.add_base_stat_change("spe", 70, 90)
    del butterfree

    beedrill = builder.pokemon("BEEDRILL", "Similar changes to Butterfree.")
    beedrill.add_base_stat_change("atk", 90, 110)
    beedrill.add_base_stat_change("spe", 75, 85)

    masquerain = builder.pokemon(
        "MASQUERAIN",
        """
        This cool little Pokémon previously ditched its cool typing of Bug/Water when evolving. 
        That has been restored, and it also has been given a stat buff to take advantage of it.
        """,
    )
    masquerain.add_base_stat_change("hp", 70, 80)
    masquerain.add_base_stat_change("def", 55, 87)
    masquerain.add_base_stat_change("spa", 100, 101)
    masquerain.add_base_stat_change("spd", 82, 86)
    masquerain.add_base_stat_change("spe", 80, 90)
    masquerain.add_type_change(PokemonType.FLYING, PokemonType.WATER)
    masquerain.add_ability_change("UNNERVE", "ADAPTABILITY")

    builder.pokemon("FLYGON", "Now a psuedo-Legend like it was always meant to be.")
    builder.pokemon("LUVDISC", "Now evolves into Alomomola at Level 25.")

    staraptor = builder.pokemon(
        "staraptor",
        """
        Staraptor has always had potential but 100 base speed is annoyingly low. Gen 7 gave it
        a buff in the form of ten extra SpD, which is useless. 
        """,
    )
    staraptor.add_type_change(PokemonType.NORMAL, PokemonType.FIGHTING)
    staraptor.add_base_stat_change("def", 70, 65)
    staraptor.add_base_stat_change("spd", 60, 50)
    staraptor.add_base_stat_change("spe", 100, 115)
    staraptor.add_level_up_move(70, "HIJUMPKICK")

    luxray = builder.pokemon(
        "LUXRAY",
        """
        Electric/Dark Luxray is the most common "rebalance" for Luxray. Electric/Fairy is way 
        cooler. It already learns Play Rough in the base game, too.
        """,
    )
    luxray.add_type_change(None, PokemonType.FAIRY)

    purugly = builder.pokemon(
        "PURUGLY", "It's an alarmingly fast, angry cat. Angry cats are pretty sharp."
    )
    purugly.add_ability_change("OWNTEMPO", "SHARPNESS")
    purugly.add_tm_move(75)
