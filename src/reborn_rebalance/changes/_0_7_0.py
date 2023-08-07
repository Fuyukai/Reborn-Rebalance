from reborn_rebalance.changelog import ChangelogBuilder
from reborn_rebalance.pbs.type import PokemonType


def build_changes(builder: ChangelogBuilder):
    builder.custom("Imported most Pokémon changes from Blaze Black 2 Redux.")
    builder.custom("Imported most Pokémon changes for Gen 6-7 from Photonic Sun.")

    builder.move("DRAGONRUSH").change_move_base_power(100, 85).change_move_accuracy(75, 90)
    builder.move("WILDCHARGE", "No longer causes recoil.")
    builder.move("ESPERWING", "Now has +1 priority, but no extra crits or speed boost.") \
        .change_move_base_power(80, 70)

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

    magneton = builder.pokemon(
        "MAGNETON", "Now evolves using a Thunder Stone instead of a location."
    )

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

    builder.pokemon(
        "FLYGON", "Now a psuedo-Legend like it was always meant to be."
    ).add_ability_change(None, "TINTEDLENS")
    builder.pokemon("LUVDISC", "Now evolves into Alomomola at Level 25.")

    staraptor = builder.pokemon(
        "staraptor",
        """
        Staraptor has always had potential but 100 base speed is annoyingly low. Gen 7 gave it
        a buff in the form of ten extra SpD, which is useless. (Yes, I am biased.)
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

    leavanny = builder.pokemon(
        "LEAVANNY",
        """
        Leavanny has a nice movepool with cutting moves that can take advantage of Sharpness,
        which is a big improvement over the middling Swarm.
        """,
    )
    leavanny.add_ability_change("SWARM", "SHARPNESS")

    crustle = builder.pokemon(
        "CRUSTLE",
        """
        Crustle can now use that massive rock it resides in to smash other Pokémon's brains in
        without suffering any recoil damage.
        """,
    )
    crustle.add_ability_change("WEAKARMOR", "ROCKHEAD")
    crustle.add_level_up_move(60, "HEADSMASH")
    crustle.add_level_up_move(70, "ROCKPOLISH")
    crustle.add_base_stat_change("def", 125, 135)
    crustle.add_base_stat_change("spd", 75, 95)

    sigilyph = builder.pokemon("SIGILYPH")
    sigilyph.add_base_stat_change("hp", 82, 87)
    sigilyph.add_base_stat_change("spa", 103, 113)

    archeops = builder.pokemon("ARCHEOPS", "Fuck Defeatist.")
    archeops.add_ability_change(None, "KLUTZ")

    garbodor = builder.pokemon(
        "GARBODOR", "Garbodor is awesome but its vanilla abilities leave a bit to be desired."
    )
    garbodor.add_ability_change("STENCH", "GOOEY")
    garbodor.add_ability_change("WEAKARMOR", "INNARDSOUT")

    cinccino = builder.pokemon(
        "CINCCINO", "There's no reason to ever use this, but it matches the Pokédex entry."
    )
    cinccino.add_ability_change("CUTECHARM", "LIMBER")

    builder.pokemon("JELLICENT", "Now uses stupid strats.")
    builder.pokemon("KLINKLANG").add_ability_change(None, "SPEEDBOOST")
    builder.pokemon("CHANDELURE", "You are absolutely fucking not getting Shadow Tag on this.")

    haxorus = builder.pokemon("HAXORUS", "Is now the psuedo-Legend it was always destined to be.")
    haxorus.add_base_stat_change("hp", 76, 96)
    haxorus.add_base_stat_change("atk", 147, 150)
    haxorus.add_base_stat_change("spa", 60, 67)
    haxorus.add_base_stat_change("spd", 70, 90)
    haxorus.add_base_stat_change("spe", 97, 107)
    haxorus.add_ability_change("RIVALRY", "STRONGJAW")
    haxorus.add_ability_change("UNNERVE", "SHARPNESS")
    haxorus.add_level_up_move(52, "JAWLOCK")

    builder.pokemon(
        "CUBCHOO", "We've got you surrounded! Come miss every single move!"
    ).add_ability_change("SNOWCLOAK", "TOUGHCLAWS")

    builder.pokemon(
        "BEARTIC", "I hate evasion abilities! I hate evasion abilities!"
    ).add_ability_change("SNOWCLOAK", "TOUGHCLAWS").add_ability_change("SWIFTSWIM", "SLUSHRUSH")

    builder.pokemon("STUNFISK", "Shoutouts to /r/stunfisk").add_ability_change(
        "SANDVEIL", "COMPETITIVE"
    )

    builder.pokemon(
        "BOUFFALANT", "The raging bull Pokémon now gets an appropriate ability."
    ).add_ability_change("SOUNDPROOF", "BERSERK")

    builder.pokemon(
        "CHARJABUG", "Now evolves inside Shade's Gym (location 281), similar to old Magneton."
    )
    builder.pokemon("VIKAVOLT", "Now Alola's second psuedo-Legend.")

    builder.pokemon(
        "RAPIDASH",
        """
        Rapidash-G is now Fire/Psychic instead of the overused Psychic/Fairy. It has a much more
        similar movepool to its Kantoian form, too.
        """,
    )
