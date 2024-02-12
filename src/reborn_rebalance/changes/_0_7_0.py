from reborn_rebalance.changelog import ChangelogBuilder
from reborn_rebalance.pbs.type import PokemonType


def build_changes(builder: ChangelogBuilder):
    builder.custom("Imported most Pokémon changes from Blaze Black 2 Redux.")
    builder.custom("Imported most Pokémon changes for Gen 6-7 from Photonic Sun.")

    builder.custom(
        "Moved the Move Reminder to after Badge 3 so you have less terrible movepools. (Map368)"
    )
    builder.custom("Added an event to get a Greavard early in the Beryl Cemetery. (Map152)")
    builder.custom("Added a 'hotfix' for the Natu event seemingly not working properly. (Map150)")

    builder.move("DRAGONRUSH").change_move_base_power(100, 85).change_move_accuracy(75, 90)
    builder.move("WILDCHARGE", "No longer causes recoil.")
    builder.move(
        "ESPERWING", "Now has +1 priority, but no extra crits or speed boost."
    ).change_move_base_power(80, 70)

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

    builder.pokemon("MAGNETON", "Now evolves using a Thunder Stone instead of a location.")

    # both get it via TM, but no ground TMs are available until route 2 (sand tomb).
    builder.pokemon("PHANPY", "Now gets ground STAB much earlier!").add_level_up_move(
        16, "BULLDOZE"
    ).add_ability_change("SANDVEIL", "BULLETPROOF")
    builder.pokemon("DONPHAN", "Now gets ground STAB much earlier!").add_level_up_move(
        16, "BULLDOZE"
    ).add_ability_change("SANDVEIL", "BULLETPROOF")

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

    builder.pokemon("ALTARIA", "Mega Altaria now has Delta Stream.")

    builder.pokemon(
        "FLYGON", "Now a psuedo-Legend like it was always meant to be."
    ).add_ability_change(None, "TINTEDLENS")
    builder.pokemon("LUVDISC", "Now evolves into Alomomola at Level 25.")

    builder.pokemon("CHIMECHO", "Now has a less bad movepool.").add_level_up_move(
        25, "BUGBUZZ"
    ).add_level_up_move(44, "AIRCUTTER").add_level_up_move(48, "EERIESPELL").add_tm_move(
        177
    ).add_tutor_move("OMINOUSWIND")

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

    builder.pokemon("BASTIODON").add_ability_change(None, "EARTHEATER").add_base_stat_change(
        "hp", 60, 65
    )

    builder.pokemon("LUMINEON").add_level_up_move(0, "TAILGLOW")

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

    builder.pokemon("SEISMITOAD").add_level_up_move(0, "BRICKBREAK")

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

    builder.pokemon("ESCAVALIER").add_tm_move(89)
    builder.pokemon("ACCELGOR", "Now learns Extreme Speed on evolution.")

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
    builder.pokemon("CHANDELURE", "You are absolutely fucking not getting Shadow Tag on this.")

    builder.pokemon("STUNFISK", "Shoutouts to /r/stunfisk").add_ability_change(
        "SANDVEIL", "COMPETITIVE"
    )

    builder.pokemon(
        "BOUFFALANT", "The raging bull Pokémon now gets an appropriate ability."
    ).add_ability_change("SOUNDPROOF", "BERSERK")

    builder.pokemon("MARACTUS").add_level_up_move(48, "VICTORYDANCE")

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

    builder.pokemon(
        "BARBARACLE",
        """
        All-Gen Patch's custom mega bafflingly makes this a special attacker, despite having a
        primarily physical movepool. This has been fixed and now Barbaracle-M is a physical
        attacker again.
        """,
    )

    builder.pokemon(
        "DRAGALGE",
        """
        For a Pokémon that evolves at level 48, it sure does have a sad BST. It's been given a 
        stat buff, as well as more appropriate abilities than a duplicate one.
        """,
    ).add_base_stat_change("hp", 65, 80).add_base_stat_change("def", 90, 94).add_base_stat_change(
        "spa", 97, 119
    ).add_ability_change("POISONTOUCH", "TOXICDEBRIS").add_tutor_move("SYNTHESIS")

    builder.pokemon("GOODRA", "Goodra-H now gets Shell Smash at level 62.")

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

    sandaconda = builder.pokemon("SANDACONDA", "Has an expanded movepool.")
    sandaconda.add_level_up_move(0, "SANDTOMB")
    sandaconda.add_level_up_move(12, "STEAMROLLER")
    sandaconda.remove_level_up_move("HEADBUTT")
    sandaconda.add_level_up_move(19, "POISONFANG")
    sandaconda.add_level_up_move(32, "SCORCHINGSANDS")
    sandaconda.remove_level_up_move("SLAM")
    sandaconda.add_level_up_move(41, "ROCKBLAST")
    sandaconda.add_level_up_move(50, "EXTREMESPEED")
    sandaconda.add_level_up_move(55, "HEADLONGRUSH")
    sandaconda.add_level_up_move(60, "HEADSMASH")

    houndstone = builder.pokemon("HOUNDSTONE", "Now it's a rocky doggy!")
    houndstone.add_type_change(None, PokemonType.ROCK)
    houndstone.add_level_up_move(16, "ROCKTOMB")
    houndstone.add_level_up_move(20, "ANCIENTPOWER")
    houndstone.add_tm_move(39).add_tm_move(71).add_tm_move(80)

    builder.pokemon("CETITAN").add_tm_move(8)

    builder.pokemon("VAROOM").add_tm_move(89).add_ability_change(None, "SPEEDBOOST")

    revavroom = builder.pokemon("REVAVROOM", "Now ten times as punny.")
    revavroom.add_tm_move(89)
    revavroom.add_ability_change(None, "SPEEDBOOST")
    revavroom.add_level_up_move(0, "HIGHHORSEPOWER")
