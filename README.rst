Reborn Rebalance
================

This is my rebalance mod for Pokémon Reborn.

This currently rebalances the following:

- Pokémon species, based on several data sources

  * The base source for rebalances is Pokémon Blaze Black 2 Redux (v1.4.0) by Drayano and AphexCubed.
   This is used for the Generation 1-5 Pokémon.
  * Then, Pokémon Photonic Sun by Buffel Salt is used for the Generation 6-7 Pokémon.
  * Finally, my own tweaks are used on top of the base tweaks.

*This mod is built on top of and REQUIRES the All Gens Patch, v2.5.0a.*

Usage
-----

Either download a pre-built patch and apply it to your All Gens patched Pokémon
Reborn, or follow the instructions below to build the patch manually.

.. highlight:: fish

1. Clone the repo:::

    git clone https://github.com/Fuyukai/Reborn-Rebalance.git

2. Install with Poetry:::

    cd Reborn-Rebalance; poetry install

3. Dump the data into PBS format:::

    poetry run into-pbs ./data ./PBS

4. Copy ``./PBS`` to your Reborn directory:::

    cp -rv ./PBS ~/Games/Reborn  # or whatever

Then, you need to run Pokémon Reborn in debug mode (or, with Debug enabled), and run the
``pbCompilePokemonData`` command.

Future Plans
------------

- Adjust encounter tables to suck less
- Maybe adjust the modded teams provided by All Gens Patch.
- Rejuv/other Essentials game support?