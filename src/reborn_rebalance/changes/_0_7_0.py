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
        """
    )
    blastoise.remove_level_up_move("SHELLSMASH")

    for mon in ["starly", "staravia"]:
        star_builder = builder.pokemon(mon)
        star_builder.remove_level_up_move("TAKEDOWN")
        star_builder.remove_level_up_move("FINALGAMBIT")

        if mon == "staravia":
            star_builder.add_level_up_move(29, "STEELWING")
            star_builder.add_level_up_move(33, "DOUBLEEDGE")
        else:
            star_builder.add_level_up_move(33, "DOUBLEEDGE")

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
    staraptor.remove_level_up_move("TAKEDOWN")
    staraptor.remove_level_up_move("FINALGAMBIT")
    staraptor.add_level_up_move(29, "STEELWING")
    staraptor.add_level_up_move(33, "DOUBLEEDGE")
    staraptor.add_level_up_move(57, "HIJUMPKICK")
