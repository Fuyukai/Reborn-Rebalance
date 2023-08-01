Reborn Rebalance
================

*This mod is built on top of and REQUIRES the All Gens Patch, v3.5.0a.*

This project is two parts:

- A rebalance mod for Pokémon Reborn...
- ... implemented via a transpiler from TOML data into Essentials PBS (2010 ver) and Ruby code.

This project is fully documented; you can find the
`documentation online <https://reborn.veriny.tf/>`_.

Currently Rebalanced
--------------------

- Pokémon species, based on several data sources:

  * The base source for rebalances is Pokémon Blaze Black 2 Redux (v1.4.0) by Drayano and AphexCubed.
    This is used for the Generation 1-5 Pokémon.
  * Then, Pokémon Photonic Sun by Buffel Salt is used for the Generation 6-7 Pokémon.
  * Finally, my own tweaks are used on top of the base tweaks.

- A small number of moves. See the list above.

Pre-Built Usage
---------------

Pre-built versions are available from the Releases tab of the repository.

1. Download Pokémon Reborn v19.16 via the updater. (Any download in the last year will be fine.)
2. Download the `All-Gen`_ patch, and extract it over Pokémon Reborn. (The pre-patched version will
   work fine).

  * This was built on top of version 3.5.0a, but any version should theoretically work. This mod
    mostly contains new game data and new events, but minimal code changes.

3. Add any other mods you might want on top, provided that they are compatible with All-Gen Patch.
4. Download a pre-built release, and extract it over your patched Pokémon Reborn.

Customised Usage
----------------

After seeing my balance tweaks, do you want me to kill myself? That's fine, you can customise this
mod easily. Edit the files in ``data`` as appropriate, then do the following:

.. highlight:: fish

1. Clone the repository:::

    git clone https://github.com/Fuyukai/Reborn-Rebalance.git

2. Install with Poetry:::

    cd Reborn-Rebalance; poetry install

3. (Optional, if you're building the web documentation) Generate the standard sprites:::

    poetry run gen-sprites <path to your installation directory>

4. Transpile the data into Reborn's format:::

    poetry run into-pbs ./data ./build

5. Copy everything inside ``./build`` to your Reborn directory:::

    cp -rv ./build/* ~/Games/Reborn  # or whatever

6. (Optional) Generate the web documentation:::

    poetry run gen-web

Then, you need to run Pokémon Reborn in debug mode (or, with Debug enabled), and run the
``pbCompilePokemonData`` command.

Future Plans
------------

- Add more events
- Document more things
- Adjust more battles
- More rebalancing!

.. _All-Gen: https://www.rebornevo.com/forums/topic/62201-all-gen-eevee-reborn-custom-megas/